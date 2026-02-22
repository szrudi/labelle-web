"""Configuration loader for Labelle Web server.

Loads environment variables and provides configuration for features like virtual printers.
"""

import json
import logging
import os

LOG = logging.getLogger(__name__)


def get_virtual_printers() -> list[dict]:
    """Load virtual printer configuration from VIRTUAL_PRINTERS environment variable.

    Expected format: JSON array of objects with 'name' and 'path' fields.
    Example: [{"name": "Office Printer", "path": "./output/office"}]

    Returns:
        List of virtual printer configuration dictionaries.
        Returns empty list if not configured or on parse error.
    """
    virtual_printers_env = os.environ.get("VIRTUAL_PRINTERS", "")
    if not virtual_printers_env.strip():
        return []

    try:
        printers = json.loads(virtual_printers_env)
        if not isinstance(printers, list):
            LOG.error("VIRTUAL_PRINTERS must be a JSON array")
            return []

        # Validate structure
        valid_printers = []
        for printer in printers:
            if not isinstance(printer, dict):
                LOG.warning(f"Skipping invalid virtual printer config: {printer}")
                continue
            if "name" not in printer or "path" not in printer:
                LOG.warning(f"Virtual printer missing 'name' or 'path': {printer}")
                continue
            valid_printers.append(printer)

        LOG.info(f"Loaded {len(valid_printers)} virtual printer(s) from config")
        return valid_printers
    except json.JSONDecodeError as e:
        LOG.error(f"Failed to parse VIRTUAL_PRINTERS environment variable: {e}")
        return []
