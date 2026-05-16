import json
import os
import tempfile
from pathlib import Path

from printer_persistence import (
    load_printer_settings,
    save_printer_settings,
    get_all_printer_settings,
    VALID_TAPE_SIZES_MM,
    VALID_COLORS,
)


class TestSaveAndLoadPrinterSettings:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        self.tmp_path = Path(self.tmp.name)
        os.environ["LABELLE_STATE_FILE"] = str(self.tmp_path)

    def teardown_method(self):
        os.environ.pop("LABELLE_STATE_FILE", None)
        self.tmp_path.unlink(missing_ok=True)
        tmp_file = self.tmp_path.with_suffix(self.tmp_path.suffix + ".tmp")
        tmp_file.unlink(missing_ok=True)
        # Clean up any parent .labelle dir created
        parent = self.tmp_path.parent
        if parent.name == ".labelle":
            try:
                parent.rmdir()
            except OSError:
                pass

    def test_save_and_load_tape_size(self):
        save_printer_settings("printer-1", {"tapeSizeMm": 19})
        settings = load_printer_settings("printer-1")
        assert settings == {"tapeSizeMm": 19}

    def test_save_and_load_all_fields(self):
        save_printer_settings("printer-a", {
            "tapeSizeMm": 12,
            "foregroundColor": "blue",
            "backgroundColor": "yellow",
        })
        settings = load_printer_settings("printer-a")
        assert settings == {
            "tapeSizeMm": 12,
            "foregroundColor": "blue",
            "backgroundColor": "yellow",
        }

    def test_unknown_printer_returns_empty(self):
        settings = load_printer_settings("nonexistent")
        assert settings == {}

    def test_invalid_tape_size_is_ignored(self):
        save_printer_settings("printer-b", {"tapeSizeMm": 99})
        settings = load_printer_settings("printer-b")
        assert settings == {}

    def test_invalid_color_is_ignored(self):
        save_printer_settings("printer-c", {"foregroundColor": "magenta"})
        settings = load_printer_settings("printer-c")
        assert settings == {}

    def test_mixed_valid_and_invalid(self):
        save_printer_settings("printer-d", {
            "tapeSizeMm": 6,
            "foregroundColor": "invalid",
            "backgroundColor": "red",
        })
        settings = load_printer_settings("printer-d")
        assert settings == {
            "tapeSizeMm": 6,
            "backgroundColor": "red",
        }

    def test_color_case_insensitive(self):
        save_printer_settings("printer-e", {"foregroundColor": "BLACK"})
        settings = load_printer_settings("printer-e")
        assert settings == {"foregroundColor": "black"}

    def test_save_empty_cleans_up_entry(self):
        # First save valid data
        save_printer_settings("printer-f", {"tapeSizeMm": 12})
        assert load_printer_settings("printer-f") == {"tapeSizeMm": 12}
        # Then save something with no valid fields
        save_printer_settings("printer-f", {"tapeSizeMm": 99})
        assert load_printer_settings("printer-f") == {}

    def test_get_all_printer_settings(self):
        save_printer_settings("p1", {"tapeSizeMm": 12})
        save_printer_settings("p2", {"tapeSizeMm": 19, "foregroundColor": "red"})
        all_settings = get_all_printer_settings()
        assert all_settings["p1"] == {"tapeSizeMm": 12}
        assert all_settings["p2"] == {"tapeSizeMm": 19, "foregroundColor": "red"}

    def test_get_all_printer_settings_skips_empty(self):
        # Entry cleaned up by invalid save should not appear
        save_printer_settings("clean-me", {"tapeSizeMm": 12})
        save_printer_settings("clean-me", {"tapeSizeMm": 99})
        all_settings = get_all_printer_settings()
        assert "clean-me" not in all_settings

    def test_state_file_survives_roundtrip(self):
        """Verify the same on-disk state file is readable after a write."""
        save_printer_settings("rt-1", {"tapeSizeMm": 9})
        # Read from disk directly
        state = json.loads(self.tmp_path.read_text())
        assert state["printers"]["rt-1"] == {"tapeSizeMm": 9}

    def test_no_file_is_graceful(self):
        """When no state file exists, load returns empty."""
        os.environ["LABELLE_STATE_FILE"] = "/tmp/nonexistent-path-12345.json"
        assert load_printer_settings("any") == {}
        assert get_all_printer_settings() == {}

    def test_all_valid_tape_sizes(self):
        for size in VALID_TAPE_SIZES_MM:
            save_printer_settings(f"tape-{size}", {"tapeSizeMm": size})
            assert load_printer_settings(f"tape-{size}") == {"tapeSizeMm": size}

    def test_all_valid_colors(self):
        for color in VALID_COLORS:
            save_printer_settings(f"color-{color}", {"foregroundColor": color})
            assert load_printer_settings(f"color-{color}") == {"foregroundColor": color}
