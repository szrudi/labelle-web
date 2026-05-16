"""Per-printer label settings persistence for Labelle Web.

Extends the same state file used by usb_power.py to also store per-printer
label settings (tape size, foreground/background colors). Follows the same
atomic-write pattern: serialize to a sibling .tmp file, then os.replace()
over the target so a reader never sees a torn JSON blob.

The state file lives at the path pointed to by LABELLE_STATE_FILE
(default: /app/output/.labelle/state.json). This is already a persistent
volume in the standard Docker deployment, so no new volume mounts are
required.
"""

import json
import logging
import os
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

# Valid tape sizes in mm that the DYMO labelers support.
VALID_TAPE_SIZES_MM = {6, 9, 12, 19}

# Valid foreground/background color names as accepted by labelle's renderer
# and the SettingsBar UI.
VALID_COLORS = {"white", "black", "yellow", "blue", "red", "green"}

_STATE_FILE = Path(
    os.environ.get("LABELLE_STATE_FILE", "/app/output/.labelle/state.json")
)

# Serialise writes so concurrent requests to /api/printer-settings don't
# race on the .tmp -> target replace.
_write_lock = Lock()


def _get_state_file() -> Path:
    """Return the state file path, resolved at call time so tests can
    override LABELLE_STATE_FILE after import."""
    return Path(os.environ.get("LABELLE_STATE_FILE",
                               "/app/output/.labelle/state.json"))


def _read_state() -> dict:
    """Return the full state dict from disk, or an empty dict on any error."""
    try:
        return json.loads(_get_state_file().read_text())
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not read printer state from %s: %s", _STATE_FILE, e)
        return {}


def _write_state(state: dict) -> None:
    """Atomically persist the full state dict.

    Best-effort: a write failure (read-only fs, missing volume mount,
    permissions) only loses cross-restart memory, never breaks runtime.
    """
    state_file = _get_state_file()
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = state_file.with_suffix(state_file.suffix + ".tmp")
        tmp.write_text(json.dumps(state))
        tmp.replace(state_file)
    except OSError as e:
        logger.warning("Could not save printer state to %s: %s", state_file, e)


def load_printer_settings(printer_id: str) -> dict:
    """Return saved label settings for a printer, or an empty dict.

    Args:
        printer_id: The printer's unique identifier (USB id or virtual id).

    Returns:
        Dict with zero or more of: tapeSizeMm, foregroundColor, backgroundColor.
        Returns empty dict if no settings are saved for this printer.
    """
    state = _read_state()
    printers = state.get("printers", {})
    settings = printers.get(printer_id)
    if not isinstance(settings, dict):
        return {}
    # Filter to only valid keys
    return {k: v for k, v in settings.items() if k in ("tapeSizeMm", "foregroundColor", "backgroundColor")}


def save_printer_settings(printer_id: str, settings: dict) -> None:
    """Persist label settings for a specific printer.

    Only recognised keys (tapeSizeMm, foregroundColor, backgroundColor)
    are stored. Invalid values are silently dropped and a warning logged.

    Args:
        printer_id: The printer's unique identifier.
        settings: Dict with one or more of:
            tapeSizeMm (int): 6, 9, 12, or 19
            foregroundColor (str): white, black, yellow, blue, red, green
            backgroundColor (str): white, black, yellow, blue, red, green
    """
    clean: dict = {}

    if "tapeSizeMm" in settings:
        val = settings["tapeSizeMm"]
        if isinstance(val, int) and val in VALID_TAPE_SIZES_MM:
            clean["tapeSizeMm"] = val
        else:
            logger.warning(
                "Ignoring invalid tapeSizeMm=%r for printer %s (must be one of %s)",
                val, printer_id, sorted(VALID_TAPE_SIZES_MM),
            )

    if "foregroundColor" in settings:
        val = settings["foregroundColor"]
        if isinstance(val, str) and val.lower() in VALID_COLORS:
            clean["foregroundColor"] = val.lower()
        else:
            logger.warning(
                "Ignoring invalid foregroundColor=%r for printer %s (must be one of %s)",
                val, printer_id, sorted(VALID_COLORS),
            )

    if "backgroundColor" in settings:
        val = settings["backgroundColor"]
        if isinstance(val, str) and val.lower() in VALID_COLORS:
            clean["backgroundColor"] = val.lower()
        else:
            logger.warning(
                "Ignoring invalid backgroundColor=%r for printer %s (must be one of %s)",
                val, printer_id, sorted(VALID_COLORS),
            )

    if not clean:
        # Nothing valid to save — remove any stale entry for this printer
        _remove_printer_entry(printer_id)
        return

    with _write_lock:
        state = _read_state()
        printers = state.get("printers", {})
        if not isinstance(printers, dict):
            printers = {}
        printers[printer_id] = clean
        state["printers"] = printers
        _write_state(state)


def _remove_printer_entry(printer_id: str) -> None:
    """Remove any saved settings for a printer (best-effort, no error if absent)."""
    with _write_lock:
        state = _read_state()
        printers = state.get("printers", {})
        if isinstance(printers, dict) and printer_id in printers:
            del printers[printer_id]
            state["printers"] = printers
            _write_state(state)


def get_all_printer_settings() -> dict[str, dict]:
    """Return all persisted printer settings as {printer_id: settings_dict}.

    Used by list_printers() to attach saved settings to each printer
    entry in the API response.
    """
    state = _read_state()
    printers = state.get("printers", {})
    if not isinstance(printers, dict):
        return {}
    # Filter each printer's settings to valid keys only
    result: dict[str, dict] = {}
    for pid, settings in printers.items():
        if isinstance(settings, dict):
            filtered = {k: v for k, v in settings.items()
                       if k in ("tapeSizeMm", "foregroundColor", "backgroundColor")}
            if filtered:
                result[pid] = filtered
    return result
