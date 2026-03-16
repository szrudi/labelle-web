import os
import tempfile

import pytest
from PIL import Image

from label_builder import (
    _build_render_engines,
    mm_to_payload_px,
    preview_label,
    render_payload,
)
from labelle.lib.constants import PIXELS_PER_MM
from labelle.lib.devices.dymo_labeler import DymoLabeler
from labelle.lib.render_engines.barcode import BarcodeRenderEngine
from labelle.lib.render_engines.barcode_with_text import BarcodeWithTextRenderEngine
from labelle.lib.render_engines.picture import PictureRenderEngine
from labelle.lib.render_engines.qr import QrRenderEngine
from labelle.lib.render_engines.text import TextRenderEngine


@pytest.fixture
def upload_dir():
    """Temporary directory for test image uploads."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_image(upload_dir):
    """Create a small PNG in the upload dir and return its filename."""
    filename = "test.png"
    img = Image.new("RGB", (10, 10), color="red")
    img.save(os.path.join(upload_dir, filename))
    return filename


class TestBuildRenderEngines:
    def test_text_widget_produces_text_engine(self):
        widgets = [{"type": "text", "text": "Hello", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 1
        assert isinstance(engines[0], TextRenderEngine)

    def test_qr_widget_produces_qr_engine(self):
        widgets = [{"type": "qr", "content": "https://example.com", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 1
        assert isinstance(engines[0], QrRenderEngine)

    def test_barcode_widget_produces_barcode_engine(self):
        widgets = [{"type": "barcode", "content": "12345", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 1
        assert isinstance(engines[0], BarcodeRenderEngine)

    def test_barcode_with_show_text_produces_barcode_with_text_engine(self):
        widgets = [
            {"type": "barcode", "content": "12345", "showText": True, "id": "1"}
        ]
        engines = _build_render_engines(widgets)
        assert len(engines) == 1
        assert isinstance(engines[0], BarcodeWithTextRenderEngine)

    def test_image_widget_with_valid_file(self, upload_dir, sample_image):
        widgets = [{"type": "image", "filename": sample_image, "id": "1"}]
        engines = _build_render_engines(widgets, upload_dir)
        assert len(engines) == 1
        assert isinstance(engines[0], PictureRenderEngine)

    def test_image_widget_with_missing_file_is_skipped(self, upload_dir):
        widgets = [{"type": "image", "filename": "nonexistent.png", "id": "1"}]
        engines = _build_render_engines(widgets, upload_dir)
        assert len(engines) == 0

    def test_empty_text_widget_is_skipped(self):
        widgets = [{"type": "text", "text": "", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 0

    def test_empty_qr_content_is_skipped(self):
        widgets = [{"type": "qr", "content": "", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 0

    def test_empty_barcode_content_is_skipped(self):
        widgets = [{"type": "barcode", "content": "", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 0

    def test_unknown_widget_type_is_skipped(self):
        widgets = [{"type": "unknown", "id": "1"}]
        engines = _build_render_engines(widgets)
        assert len(engines) == 0

    def test_multiple_widgets_produce_engines_in_order(self):
        widgets = [
            {"type": "text", "text": "First", "id": "1"},
            {"type": "qr", "content": "Second", "id": "2"},
            {"type": "barcode", "content": "12345", "id": "3"},
        ]
        engines = _build_render_engines(widgets)
        assert len(engines) == 3
        assert isinstance(engines[0], TextRenderEngine)
        assert isinstance(engines[1], QrRenderEngine)
        assert isinstance(engines[2], BarcodeRenderEngine)

    def test_invalid_barcode_type_falls_back_to_default(self):
        widgets = [
            {
                "type": "barcode",
                "content": "12345",
                "barcodeType": "invalid_type",
                "id": "1",
            }
        ]
        engines = _build_render_engines(widgets)
        assert len(engines) == 1
        assert isinstance(engines[0], BarcodeRenderEngine)


class TestPreviewLabel:
    def test_returns_valid_png_bytes(self):
        widgets = [{"type": "text", "text": "Test", "id": "1"}]
        settings = {"tapeSizeMm": 12}
        result = preview_label(widgets, settings)
        # PNG magic bytes
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_raises_value_error_for_no_renderable_widgets(self):
        widgets = [{"type": "text", "text": "", "id": "1"}]
        settings = {"tapeSizeMm": 12}
        with pytest.raises(ValueError, match="No renderable widgets"):
            preview_label(widgets, settings)

    def test_respects_settings(self):
        widgets = [{"type": "text", "text": "Test", "id": "1"}]
        small = preview_label(widgets, {"tapeSizeMm": 6})
        large = preview_label(widgets, {"tapeSizeMm": 19})
        # Different tape sizes should produce different image heights
        small_img = Image.open(__import__("io").BytesIO(small))
        large_img = Image.open(__import__("io").BytesIO(large))
        assert large_img.height > small_img.height


class TestMmToPayloadPx:
    def test_basic_conversion(self):
        result = mm_to_payload_px(10, 0)
        assert result == 10 * PIXELS_PER_MM

    def test_zero_mm_returns_zero(self):
        assert mm_to_payload_px(0, 0) == 0

    def test_margin_larger_than_total_returns_zero(self):
        # margin * 2 > mm * PIXELS_PER_MM → clamped to 0
        result = mm_to_payload_px(1, 1000)
        assert result == 0

    def test_margin_subtracted(self):
        margin = 10
        result = mm_to_payload_px(10, margin)
        assert result == (10 * PIXELS_PER_MM) - margin * 2


class TestRenderPayloadVerticalMargins:
    """Verify that the print payload fits within the physical print-head coverage zone.

    DYMO D1 tape has a clear laminate on each side. For 12 mm tape, only the
    central ~8.2 mm (≈44 of 64 printer dots) is the coloured label material
    that will show after printing. Text that extends into the outer dots (the
    laminate zone) is invisible on the finished label.

    After the fix, content must be rendered within the printable zone and the
    bitmap must be padded to the full tape height required by the printer protocol.
    """

    def _get_content_rows(self, bitmap: Image.Image) -> tuple[int, int]:
        """Return (first_row, last_row) that contain any ink in the bitmap."""
        width, height = bitmap.size
        bw = bitmap.convert("1")
        first_row = height
        last_row = -1
        for y in range(height):
            for x in range(width):
                if bw.getpixel((x, y)):
                    first_row = min(first_row, y)
                    last_row = max(last_row, y)
                    break
        return first_row, last_row

    def test_print_bitmap_height_equals_tape_height(self):
        """The print bitmap must always be exactly dymo_labeler.height_px rows tall."""
        widgets = [{"type": "text", "text": "Hello", "id": "1"}]
        for tape_mm in [6, 9, 12, 19]:
            d = DymoLabeler(tape_mm)
            bitmap = render_payload(widgets, {"tapeSizeMm": tape_mm})
            assert bitmap.height == d.height_px, (
                f"{tape_mm}mm tape: expected height {d.height_px}, got {bitmap.height}"
            )

    def test_content_within_printable_zone_12mm(self):
        """For 12 mm tape the content must sit inside the ~44-dot printable zone."""
        widgets = [{"type": "text", "text": "Hello", "id": "1"}]
        bitmap = render_payload(widgets, {"tapeSizeMm": 12})
        d = DymoLabeler(12)
        _, v_margin_px = d.labeler_margin_px
        v_margin_dots = round(
            v_margin_px * d.height_px / (d.tape_size_mm * PIXELS_PER_MM)
        )
        printable_top = v_margin_dots
        printable_bottom = d.height_px - v_margin_dots - 1

        first_row, last_row = self._get_content_rows(bitmap)
        assert first_row >= printable_top, (
            f"Content starts at row {first_row}, expected >= {printable_top}"
        )
        assert last_row <= printable_bottom, (
            f"Content ends at row {last_row}, expected <= {printable_bottom}"
        )

    def test_content_vertically_centred_12mm(self):
        """Content should be centered within the printable zone, not flush to the top."""
        widgets = [{"type": "text", "text": "Hello", "id": "1"}]
        bitmap = render_payload(widgets, {"tapeSizeMm": 12})
        d = DymoLabeler(12)
        _, v_margin_px = d.labeler_margin_px
        v_margin_dots = round(
            v_margin_px * d.height_px / (d.tape_size_mm * PIXELS_PER_MM)
        )
        tape_center = d.height_px / 2

        first_row, last_row = self._get_content_rows(bitmap)
        content_center = (first_row + last_row) / 2
        # Content center should be close to the tape center (within 20 % of tape height)
        tolerance = d.height_px * 0.20
        assert abs(content_center - tape_center) < tolerance, (
            f"Content center {content_center:.1f} is too far from tape center {tape_center:.1f}"
        )
