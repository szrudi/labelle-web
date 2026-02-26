"""Virtual printer implementation for testing and development.

Virtual printers save label output to a configured directory instead of sending
to a physical USB printer. Output can be a preview PNG, label JSON, or both,
controlled by the `output_mode` setting.
"""

import datetime
import json
import logging
import os
import uuid
from pathlib import Path

from PIL import Image

LOG = logging.getLogger(__name__)


class VirtualPrinter:
    """Virtual printer that saves labels as PNG and/or JSON files."""

    def __init__(self, name: str, output_path: str, output_mode: str = "image"):
        self.name = name
        self.output_path = output_path
        self.output_mode = output_mode
        self._ensure_output_directory()

    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        try:
            Path(self.output_path).mkdir(parents=True, exist_ok=True)
            LOG.info(f"Virtual printer '{self.name}' output directory: {self.output_path}")
        except Exception as e:
            LOG.error(f"Failed to create output directory {self.output_path}: {e}")

    @property
    def id(self) -> str:
        """Get unique printer ID with virtual prefix."""
        sanitized_name = self.name.replace(" ", "_").replace("(", "").replace(")", "")
        return f"virtual:{sanitized_name}"

    @property
    def display_name(self) -> str:
        """Get display name with virtual indicator."""
        return f"{self.name} (Virtual)"

    def _generate_base_path(self) -> str:
        """Generate a unique base file path (without extension)."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return os.path.join(self.output_path, f"label_{timestamp}_{unique_id}")

    def save_preview(self, bitmap: Image.Image) -> str:
        """Save preview bitmap as PNG.

        Returns:
            Path to saved file.

        Raises:
            IOError: If file cannot be saved.
        """
        filepath = self._generate_base_path() + ".png"
        try:
            bitmap.save(filepath, format="PNG")
            LOG.info(f"Virtual printer '{self.name}' saved preview to: {filepath}")
            return filepath
        except Exception as e:
            LOG.error(f"Failed to save preview to {filepath}: {e}")
            raise IOError(f"Failed to save preview: {e}") from e

    def save_json(self, widgets: list[dict], settings: dict) -> str:
        """Save label data as JSON.

        Returns:
            Path to saved file.

        Raises:
            IOError: If file cannot be saved.
        """
        filepath = self._generate_base_path() + ".json"
        data = {"widgets": widgets, "settings": settings}
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            LOG.info(f"Virtual printer '{self.name}' saved JSON to: {filepath}")
            return filepath
        except Exception as e:
            LOG.error(f"Failed to save JSON to {filepath}: {e}")
            raise IOError(f"Failed to save JSON: {e}") from e

    def save(
        self,
        preview_bitmap: Image.Image,
        widgets: list[dict],
        settings: dict,
    ) -> list[str]:
        """Save output based on configured output_mode.

        Returns:
            List of saved file paths.
        """
        paths: list[str] = []
        if self.output_mode in ("image", "both"):
            paths.append(self.save_preview(preview_bitmap))
        if self.output_mode in ("json", "both"):
            paths.append(self.save_json(widgets, settings))
        return paths
