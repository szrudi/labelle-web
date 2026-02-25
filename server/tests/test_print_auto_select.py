"""Tests for auto-select printer behavior in label_builder.print_label.

When no printer_id is specified (auto-select), print_label should:
1. Try real USB printers first
2. Fall back to the first virtual printer if no USB printers are found
3. Raise an error only if no printers at all are available
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def sample_widgets():
    return [{"type": "text", "text": "Hello", "id": "1"}]


@pytest.fixture
def sample_settings():
    return {
        "tapeSizeMm": 12,
        "marginPx": 56,
        "minLengthMm": 0,
        "justify": "center",
        "foregroundColor": "black",
        "backgroundColor": "white",
        "showMargins": False,
    }


class TestAutoSelectWithVirtualPrinters:
    @patch("label_builder.DeviceManager")
    def test_auto_select_falls_back_to_virtual_printer(
        self, mock_dm_cls, sample_widgets, sample_settings, virtual_printer_env
    ):
        """When no USB printers exist but virtual printers are configured,
        auto-select should use the first virtual printer."""
        mock_dm = MagicMock()
        mock_dm.scan.side_effect = Exception("No supported devices found")
        mock_dm_cls.return_value = mock_dm

        from label_builder import print_label

        # Should NOT raise — should fall back to virtual printer
        print_label(sample_widgets, sample_settings, printer_id=None)

    @patch("label_builder.DeviceManager")
    def test_auto_select_saves_to_virtual_printer_output_dir(
        self, mock_dm_cls, sample_widgets, sample_settings, virtual_printer_env
    ):
        """Auto-select fallback should actually save a file to the virtual printer's output dir."""
        mock_dm = MagicMock()
        mock_dm.scan.side_effect = Exception("No supported devices found")
        mock_dm_cls.return_value = mock_dm

        from label_builder import print_label

        print_label(sample_widgets, sample_settings, printer_id=None)

        # Check that a file was saved to the first virtual printer's output dir
        output_dir = virtual_printer_env[0]["path"]
        files = os.listdir(output_dir)
        assert len(files) == 1
        assert files[0].endswith(".png")

    @patch("label_builder.DeviceManager")
    def test_auto_select_no_printers_at_all_raises(
        self, mock_dm_cls, sample_widgets, sample_settings, no_virtual_printers_env
    ):
        """When no USB printers AND no virtual printers exist, auto-select should raise."""
        mock_dm = MagicMock()
        mock_dm.scan.side_effect = Exception("No supported devices found")
        mock_dm_cls.return_value = mock_dm

        from label_builder import print_label

        with pytest.raises(Exception):
            print_label(sample_widgets, sample_settings, printer_id=None)
