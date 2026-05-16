"""Per-printer label settings persistence.

Stores per-printer label settings (tape size, foreground/background
color) in the same LABELLE_STATE_FILE used by usb_power, under a
``printer_settings`` key. Matches the existing atomic-write + tolerant-
read patterns so the two modules coexist in one file without clobbering
each other.

A write failure (read-only fs, missing volume mount, permissions) is
logged and ignored — runtime never breaks just because state can't be
persisted.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = Path(
    os.environ.get("LABELLE_STATE_FILE", "/app/output/.labelle/state.json")
)

SETTINGS_KEY = "printer_settings"

# Fields from LabelSettings we persist per-printer. These are the
# "physical printer property" fields listed in the issue.  marginPx,
# minLengthMm, justify, and cutMark are deliberately excluded — they're
# label preferences, not printer properties.
PERSISTED_FIELDS = frozenset({"tapeSizeMm", "foregroundColor", "backgroundColor"})


def _read_full_state() -> dict:
    """Read the full state dict from disk, or empty dict if absent/invalid."""
    try:
        data = json.loads(STATE_FILE.read_text())
        if isinstance(data, dict):
            return data
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not read state from %s: %s", STATE_FILE, e)
    return {}


def _write_full_state(state: dict) -> None:
    """Atomically write the full state dict to disk."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
        tmp.write_text(json.dumps(state))
        tmp.replace(STATE_FILE)
    except OSError as e:
        logger.warning("Could not write state to %s: %s", STATE_FILE, e)


def get_settings(printer_id: str) -> dict | None:
    """Return persisted settings for a printer, or None if none saved."""
    state = _read_full_state()
    settings_map = state.get(SETTINGS_KEY, {})
    if not isinstance(settings_map, dict):
        return None
    stored = settings_map.get(printer_id)
    if isinstance(stored, dict):
        return stored
    return None


def save_settings(printer_id: str, settings: dict) -> None:
    """Persist per-printer settings, merging into existing state.

    Only fields in ``PERSISTED_FIELDS`` are stored — everything else is
    silently dropped.
    """
    state = _read_full_state()
    settings_map = state.get(SETTINGS_KEY)
    if not isinstance(settings_map, dict):
        settings_map = {}
        state[SETTINGS_KEY] = settings_map

    filtered: dict[str, object] = {}
    for k, v in settings.items():
        if k in PERSISTED_FIELDS:
            filtered[k] = v

    # Don't store an empty dict — remove the key so the state file
    # stays clean when a user resets settings to all defaults.
    if filtered:
        settings_map[printer_id] = filtered
    else:
        settings_map.pop(printer_id, None)

    _write_full_state(state)
