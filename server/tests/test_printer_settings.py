"""Tests for printer_settings — per-printer label settings persistence."""

import json

import printer_settings


class TestGetSettings:
    def test_returns_none_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(printer_settings, "STATE_FILE", tmp_path / "absent.json")
        assert printer_settings.get_settings("printer-1") is None

    def test_returns_none_when_printer_not_in_file(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        p.write_text(json.dumps({"printer_settings": {"other": {"tapeSizeMm": 12}}}))
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)
        assert printer_settings.get_settings("printer-1") is None

    def test_returns_stored_settings(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        p.write_text(json.dumps({
            "printer_settings": {
                "Bus 001: ID 0922:1002": {
                    "tapeSizeMm": 19,
                    "foregroundColor": "red",
                    "backgroundColor": "yellow",
                }
            }
        }))
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)
        result = printer_settings.get_settings("Bus 001: ID 0922:1002")
        assert result == {
            "tapeSizeMm": 19,
            "foregroundColor": "red",
            "backgroundColor": "yellow",
        }

    def test_handles_corrupt_json(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        p.write_text("{not json")
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)
        assert printer_settings.get_settings("printer-1") is None

    def test_handles_non_dict_state(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        p.write_text("[]")
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)
        assert printer_settings.get_settings("printer-1") is None


class TestSaveSettings:
    def test_saves_and_round_trips(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)

        printer_settings.save_settings("printer-A", {
            "tapeSizeMm": 12,
            "foregroundColor": "black",
            "backgroundColor": "white",
        })

        result = printer_settings.get_settings("printer-A")
        assert result == {
            "tapeSizeMm": 12,
            "foregroundColor": "black",
            "backgroundColor": "white",
        }

    def test_filters_unknown_fields(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)

        printer_settings.save_settings("printer-A", {
            "tapeSizeMm": 12,
            "marginPx": 99,       # not persisted
            "justify": "left",    # not persisted
            "unknownField": True,
        })

        result = printer_settings.get_settings("printer-A")
        assert "tapeSizeMm" in result
        assert "marginPx" not in result
        assert "justify" not in result
        assert "unknownField" not in result

    def test_does_not_clobber_usb_power_data(self, tmp_path, monkeypatch):
        """Saving printer settings must not destroy hub/port data stored by usb_power."""
        p = tmp_path / "state.json"
        p.write_text(json.dumps({"hub": "1-1", "port": 3}))
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)

        printer_settings.save_settings("printer-A", {"tapeSizeMm": 12})

        data = json.loads(p.read_text())
        assert data["hub"] == "1-1"
        assert data["port"] == 3
        assert "printer_settings" in data

    def test_multiple_printers(self, tmp_path, monkeypatch):
        p = tmp_path / "state.json"
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)

        printer_settings.save_settings("printer-A", {"tapeSizeMm": 6})
        printer_settings.save_settings("printer-B", {"tapeSizeMm": 19})
        printer_settings.save_settings("virtual:Office", {
            "tapeSizeMm": 12,
            "foregroundColor": "blue",
        })

        assert printer_settings.get_settings("printer-A") == {"tapeSizeMm": 6}
        assert printer_settings.get_settings("printer-B") == {"tapeSizeMm": 19}
        assert printer_settings.get_settings("virtual:Office") == {
            "tapeSizeMm": 12,
            "foregroundColor": "blue",
        }

    def test_removes_entry_when_all_fields_empty(self, tmp_path, monkeypatch):
        """Saving an empty or invalid dict should remove the printer's settings entry."""
        p = tmp_path / "state.json"
        monkeypatch.setattr(printer_settings, "STATE_FILE", p)

        printer_settings.save_settings("printer-A", {"tapeSizeMm": 12})
        assert printer_settings.get_settings("printer-A") is not None

        # Save with no valid persisted fields
        printer_settings.save_settings("printer-A", {"marginPx": 99})
        assert printer_settings.get_settings("printer-A") is None

    def test_swallows_write_errors(self, tmp_path, monkeypatch):
        """save_settings must never raise, even if the filesystem is broken."""
        blocker = tmp_path / "blocker"
        blocker.write_text("not a dir")
        bad_path = blocker / "state.json"
        monkeypatch.setattr(printer_settings, "STATE_FILE", bad_path)

        # Should not raise
        printer_settings.save_settings("printer-A", {"tapeSizeMm": 12})
