"""Per-port USB power control via uhubctl.

Lets us power off the Dymo printer's USB port when idle so its transformer
isn't running 24/7, and power it back on when the user opens the page.

Requires `uhubctl` on PATH (apt-installed in the Docker image). The hub must
support per-port power switching (ppps) — confirmed for the 2109:3431 USB
2.0 hub on hector.
"""

import os
import re
import subprocess

UHUBCTL_BIN = os.environ.get("UHUBCTL_BIN", "uhubctl")
DYMO_USB_ID = "0922:1002"

_HUB_LINE_RE = re.compile(r"Current status for hub (\S+)")
_PORT_DEVICE_RE = re.compile(r"\s+Port (\d+):.*\[(\S+) ")
_PORT_LINE_RE = re.compile(r"\s+Port (\d+):\s+(\w+)(.*)")


def _run(*args: str) -> str:
    result = subprocess.run(
        [UHUBCTL_BIN, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=True,
    )
    return result.stdout.decode()


def find_printer_port(vendor_product_id: str = DYMO_USB_ID) -> tuple[str, int] | None:
    """Locate (hub, port) for a USB device by `VVVV:PPPP` id, or None if absent."""
    output = _run()
    current_hub: str | None = None
    for line in output.splitlines():
        if m := _HUB_LINE_RE.match(line):
            current_hub = m.group(1)
            continue
        if current_hub and (m := _PORT_DEVICE_RE.match(line)):
            if m.group(2) == vendor_product_id:
                return current_hub, int(m.group(1))
    return None


def get_port_status(hub: str, port: int) -> dict:
    """Return {'powered': bool, 'connected': bool} for a specific hub port."""
    output = _run("-l", hub, "-p", str(port))
    for line in output.splitlines():
        m = _PORT_LINE_RE.match(line)
        if m and int(m.group(1)) == port:
            flags = m.group(3)
            return {
                "powered": "power" in flags,
                "connected": "connect" in flags,
            }
    raise ValueError(f"Port {port} not found on hub {hub}")


def set_port_power(hub: str, port: int, on: bool) -> None:
    _run("-l", hub, "-p", str(port), "-a", "on" if on else "off")


def power_on(hub: str, port: int) -> None:
    set_port_power(hub, port, on=True)


def power_off(hub: str, port: int) -> None:
    set_port_power(hub, port, on=False)


_last_known_port: tuple[str, int] | None = None


def find_or_recall_printer_port(
    vendor_product_id: str = DYMO_USB_ID,
) -> tuple[str, int] | None:
    """Like find_printer_port, but remembers the last live result.

    Needed because once we power off the port, the device disappears from
    the USB tree — `find_printer_port` would return None and we'd have no
    way to power it back on. This falls back to the cached result.
    """
    global _last_known_port
    found = find_printer_port(vendor_product_id)
    if found:
        _last_known_port = found
    return found or _last_known_port
