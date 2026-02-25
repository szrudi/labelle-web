import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


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


class TestApiPreview:
    @patch("app.preview_label")
    def test_returns_png_for_valid_text_widget(self, mock_preview, client):
        # Create a minimal valid PNG
        img = Image.new("RGB", (10, 10), "white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mock_preview.return_value = buf.getvalue()

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {"tapeSizeMm": 12},
        }
        resp = client.post(
            "/api/preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert resp.content_type == "image/png"
        assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_returns_400_for_empty_widgets(self, client):
        payload = {"widgets": [], "settings": {}}
        resp = client.post(
            "/api/preview",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_returns_400_for_missing_widgets_key(self, client):
        payload = {"settings": {}}
        resp = client.post(
            "/api/preview",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("app.preview_label")
    def test_returns_500_when_preview_raises(self, mock_preview, client):
        mock_preview.side_effect = Exception("Render failed")

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {"tapeSizeMm": 12},
        }
        resp = client.post(
            "/api/preview",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 500
        assert "Render failed" in resp.get_json()["message"]


class TestApiUploadImage:
    def test_uploads_png_returns_filename(self, client):
        img = Image.new("RGB", (10, 10), "red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/api/upload-image",
            data={"file": (buf, "test.png")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200
        data = resp.get_json()
        assert "filename" in data
        assert data["filename"].endswith(".png")

    def test_rgba_image_saved_as_rgb(self, client):
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        resp = client.post(
            "/api/upload-image",
            data={"file": (buf, "rgba.png")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200
        filename = resp.get_json()["filename"]
        # Verify the saved file is RGB (transparency flattened)
        from app import UPLOAD_DIR

        saved = Image.open(os.path.join(UPLOAD_DIR, filename))
        assert saved.mode == "RGB"

    def test_returns_400_when_no_file(self, client):
        resp = client.post(
            "/api/upload-image",
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_returns_400_when_empty_filename(self, client):
        buf = io.BytesIO(b"fake")
        resp = client.post(
            "/api/upload-image",
            data={"file": (buf, "")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


class TestApiServeUpload:
    def test_serves_previously_uploaded_file(self, client):
        # Upload first
        img = Image.new("RGB", (5, 5), "blue")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        upload_resp = client.post(
            "/api/upload-image",
            data={"file": (buf, "serve_test.png")},
            content_type="multipart/form-data",
        )
        filename = upload_resp.get_json()["filename"]

        # Now serve it
        resp = client.get(f"/api/uploads/{filename}")
        assert resp.status_code == 200

    def test_returns_404_for_nonexistent_file(self, client):
        resp = client.get("/api/uploads/nonexistent_abc123.png")
        assert resp.status_code == 404


class TestApiPrintErrors:
    @patch("app.print_label")
    def test_returns_400_for_empty_widgets(self, mock_print, client):
        payload = {"widgets": [], "settings": {}}
        resp = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 400
        mock_print.assert_not_called()

    @patch("app.print_label")
    def test_returns_500_when_print_raises(self, mock_print, client):
        mock_print.side_effect = Exception("Printer on fire")

        payload = {
            "widgets": [{"type": "text", "text": "Hello", "id": "1"}],
            "settings": {"tapeSizeMm": 12},
        }
        resp = client.post(
            "/api/print",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert resp.status_code == 500
        assert "Printer on fire" in resp.get_json()["message"]
