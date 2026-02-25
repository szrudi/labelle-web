"""Virtual printer implementation for testing and development.

Virtual printers save label output as PNG files to a configured directory
instead of sending to a physical USB printer. This allows testing multi-printer
functionality without needing multiple physical devices.
"""

import datetime
import logging
import os
import uuid
from pathlib import Path

from PIL import Image

LOG = logging.getLogger(__name__)


class VirtualPrinter:
    """Virtual printer that saves labels as PNG files."""

    def __init__(self, name: str, output_path: str):
        """Initialize a virtual printer.

        Args:
            name: Human-readable name for the printer
            output_path: Directory path where labels will be saved
        """
        self.name = name
        self.output_path = output_path
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
        # Use sanitized name as ID suffix (replace spaces/special chars)
        sanitized_name = self.name.replace(" ", "_").replace("(", "").replace(")", "")
        return f"virtual:{sanitized_name}"

    @property
    def display_name(self) -> str:
        """Get display name with virtual indicator."""
        return f"{self.name} (Virtual)"

    def save_label(self, bitmap: Image.Image) -> str:
        """Save label bitmap to file.

        Args:
            bitmap: PIL Image object to save

        Returns:
            Path to saved file

        Raises:
            IOError: If file cannot be saved
        """
        # Generate unique filename with timestamp and UUID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"label_{timestamp}_{unique_id}.png"
        filepath = os.path.join(self.output_path, filename)

        try:
            bitmap.save(filepath, format="PNG")
            LOG.info(f"Virtual printer '{self.name}' saved label to: {filepath}")
            return filepath
        except Exception as e:
            LOG.error(f"Failed to save label to {filepath}: {e}")
            raise IOError(f"Failed to save label: {e}") from e
