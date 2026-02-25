import json
import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client(virtual_printer_env):
    """Flask test client with virtual printers configured."""
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_no_printers(no_virtual_printers_env):
    """Flask test client with no printers configured."""
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestApiPrintersUsbScanFailure:
    @patch("app.DeviceManager")
    def test_returns_virtual_printers_when_usb_scan_throws(self, mock_dm_cls, client):
        """USB scan failure should not prevent virtual printers from being returned."""
        mock_dm_cls.side_effect = Exception("USB subsystem unavailable")

        resp = client.get("/api/printers")
        assert resp.status_code == 200

        data = resp.get_json()
        printers = data["printers"]
        virtual = [p for p in printers if p["vendorProductId"] == "virtual"]
        assert len(virtual) == 2

    @patch("app.DeviceManager")
    def test_returns_empty_when_usb_scan_throws_and_no_virtual(self, mock_dm_cls, client_no_printers):
        mock_dm_cls.side_effect = Exception("USB subsystem unavailable")

        resp = client_no_printers.get("/api/printers")
        assert resp.status_code == 200
        assert resp.get_json()["printers"] == []


class TestApiPrinters:
    @patch("app.DeviceManager")
    def test_returns_virtual_printers(self, mock_dm_cls, client):
        # Mock DeviceManager to return no USB devices
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        resp = client.get("/api/printers")
        assert resp.status_code == 200

        data = resp.get_json()
        printers = data["printers"]

        # Should have virtual printers from the fixture
        virtual = [p for p in printers if p["vendorProductId"] == "virtual"]
        assert len(virtual) == 2
        assert virtual[0]["name"].endswith("(Virtual)")
        assert virtual[0]["id"].startswith("virtual:")

    @patch("app.DeviceManager")
    def test_no_printers_configured(self, mock_dm_cls, client_no_printers):
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        resp = client_no_printers.get("/api/printers")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["printers"] == []

    @patch("app.DeviceManager")
    def test_virtual_printer_ids_are_unique(self, mock_dm_cls, client):
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        resp = client.get("/api/printers")
        data = resp.get_json()
        ids = [p["id"] for p in data["printers"]]
        assert len(ids) == len(set(ids))


class TestApiPrintWithVirtualPrinter:
    @patch("app.DeviceManager")
    @patch("app.print_label")
    def test_print_with_virtual_printer_id(self, mock_print, mock_dm_cls, client):
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {
                "tapeSizeMm": 12,
                "marginPx": 56,
                "minLengthMm": 0,
                "justify": "center",
                "foregroundColor": "black",
                "backgroundColor": "white",
                "showMargins": False,
                "printerId": "virtual:Test_Printer",
            },
        }

        resp = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_print.assert_called_once()
        # Verify printer_id was passed through
        call_kwargs = mock_print.call_args
        assert call_kwargs[1]["printer_id"] == "virtual:Test_Printer"

    @patch("app.DeviceManager")
    @patch("app.print_label")
    def test_print_with_auto_select(self, mock_print, mock_dm_cls, client):
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {
                "tapeSizeMm": 12,
                "marginPx": 56,
                "minLengthMm": 0,
                "justify": "center",
                "foregroundColor": "black",
                "backgroundColor": "white",
                "showMargins": False,
            },
        }

        resp = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_print.assert_called_once()
        # Auto-select: printerId is absent, so printer_id should be None
        call_kwargs = mock_print.call_args
        assert call_kwargs[1]["printer_id"] is None

    @patch("app.DeviceManager")
    @patch("app.print_label")
    def test_print_with_empty_string_printer_id(self, mock_print, mock_dm_cls, client):
        """Frontend sends empty string when Auto-select is chosen."""
        mock_dm = MagicMock()
        mock_dm.devices = []
        mock_dm_cls.return_value = mock_dm

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {
                "tapeSizeMm": 12,
                "marginPx": 56,
                "minLengthMm": 0,
                "justify": "center",
                "foregroundColor": "black",
                "backgroundColor": "white",
                "showMargins": False,
                "printerId": "",
            },
        }

        resp = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 200
        mock_print.assert_called_once()
        # Empty string from settings.get("printerId") — passed as-is
        call_kwargs = mock_print.call_args
        assert call_kwargs[1]["printer_id"] == ""
