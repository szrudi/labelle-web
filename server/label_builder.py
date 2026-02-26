import os
from io import BytesIO

from PIL import Image

from labelle.lib.constants import (
    DEFAULT_BARCODE_TYPE,
    DEFAULT_MARGIN_PX,
    PIXELS_PER_MM,
    BarcodeType,
    Direction,
)
from labelle.lib.devices.dymo_labeler import DymoLabeler
from labelle.lib.font_config import get_font_path
from labelle.lib.render_engines.barcode import BarcodeRenderEngine
from labelle.lib.render_engines.barcode_with_text import BarcodeWithTextRenderEngine
from labelle.lib.render_engines.horizontally_combined import (
    HorizontallyCombinedRenderEngine,
)
from labelle.lib.render_engines.print_payload import PrintPayloadRenderEngine
from labelle.lib.render_engines.print_preview import PrintPreviewRenderEngine
from labelle.lib.render_engines.picture import PictureRenderEngine
from labelle.lib.render_engines.qr import QrRenderEngine
from labelle.lib.render_engines.render_context import RenderContext
from labelle.lib.render_engines.render_engine import RenderEngine
from labelle.lib.render_engines.text import TextRenderEngine


def mm_to_payload_px(mm: float, margin: float) -> float:
    """Convert a length in mm to pixels of payload, subtracting margin from each side."""
    return max(0, (mm * PIXELS_PER_MM) - margin * 2)


def _build_render_engines(
    widgets: list[dict], upload_dir: str = "",
) -> list[RenderEngine]:
    """Convert a list of widget dicts into labelle RenderEngine instances."""
    engines: list[RenderEngine] = []
    for widget in widgets:
        widget_type = widget.get("type")

        if widget_type == "text":
            text = widget.get("text", "")
            if not text:
                continue
            font_path = get_font_path(style=widget.get("fontStyle", "regular"))
            engines.append(
                TextRenderEngine(
                    text_lines=text.split("\n"),
                    font_file_name=font_path,
                    frame_width_px=widget.get("frameWidthPx", 0),
                    font_size_ratio=widget.get("fontScale", 90) / 100.0,
                    align=Direction(widget.get("align", "left")),
                )
            )

        elif widget_type == "qr":
            content = widget.get("content", "").strip()
            if content:
                engines.append(QrRenderEngine(content))

        elif widget_type == "barcode":
            content = widget.get("content", "").strip()
            if not content:
                continue
            barcode_type_str = widget.get("barcodeType", "code128")
            try:
                barcode_type = BarcodeType(barcode_type_str.lower())
            except ValueError:
                barcode_type = DEFAULT_BARCODE_TYPE

            if widget.get("showText", False):
                font_path = get_font_path(style="regular")
                engines.append(
                    BarcodeWithTextRenderEngine(
                        content=content,
                        font_file_name=font_path,
                        barcode_type=barcode_type,
                    )
                )
            else:
                engines.append(
                    BarcodeRenderEngine(content=content, barcode_type=barcode_type)
                )

        elif widget_type == "image":
            filename = widget.get("filename", "")
            if filename and upload_dir:
                picture_path = os.path.join(upload_dir, filename)
                if os.path.isfile(picture_path):
                    engines.append(PictureRenderEngine(picture_path=picture_path))

    return engines


def _render_label(
    dymo_labeler: DymoLabeler,
    render_engine: RenderEngine,
    settings: dict,
    justify: Direction,
    margin_px: float,
    min_payload_px: float,
    *,
    for_print: bool = False,
    show_margins: bool = False,
) -> Image.Image:
    """Render a label bitmap.

    Args:
        for_print: If True, renders the raw B&W payload for the printer.
                   If False, renders a color preview image.
        show_margins: If True, show margin indicators in the preview.
    """
    render_context = RenderContext(
        height_px=dymo_labeler.height_px,
        foreground_color=settings.get("foregroundColor", "black"),
        background_color=settings.get("backgroundColor", "white"),
        preview_show_margins=show_margins,
    )
    engine_cls = PrintPayloadRenderEngine if for_print else PrintPreviewRenderEngine
    output_engine = engine_cls(
        render_engine=render_engine,
        justify=justify,
        visible_horizontal_margin_px=margin_px,
        labeler_margin_px=dymo_labeler.labeler_margin_px,
        min_width_px=min_payload_px,
    )
    if for_print:
        bitmap, _ = output_engine.render_with_meta(render_context)
        return bitmap
    return output_engine.render(render_context)


def _prepare_render(
    widgets: list[dict], settings: dict, upload_dir: str = "",
) -> tuple[DymoLabeler, RenderEngine, Direction, float, float]:
    """Shared setup for rendering: build engines, parse settings, create labeler."""
    engines = _build_render_engines(widgets, upload_dir)
    if not engines:
        raise ValueError("No renderable widgets provided")

    render_engine = HorizontallyCombinedRenderEngine(engines)

    margin_px = settings.get("marginPx", DEFAULT_MARGIN_PX)
    min_length_mm = settings.get("minLengthMm", 0)
    min_payload_px = mm_to_payload_px(min_length_mm, margin_px)
    justify = Direction(settings.get("justify", "center"))

    dymo_labeler = DymoLabeler(tape_size_mm=settings.get("tapeSizeMm", 12))

    return dymo_labeler, render_engine, justify, margin_px, min_payload_px


def render_preview(
    widgets: list[dict], settings: dict, upload_dir: str = "", show_margins: bool = False,
) -> Image.Image:
    """Render a color preview image from widgets."""
    dymo_labeler, render_engine, justify, margin_px, min_payload_px = _prepare_render(
        widgets, settings, upload_dir
    )
    return _render_label(
        dymo_labeler, render_engine, settings, justify, margin_px, min_payload_px,
        show_margins=show_margins,
    )


def render_payload(
    widgets: list[dict], settings: dict, upload_dir: str = "",
) -> Image.Image:
    """Render a B&W payload image ready for printing."""
    dymo_labeler, render_engine, justify, margin_px, min_payload_px = _prepare_render(
        widgets, settings, upload_dir
    )
    return _render_label(
        dymo_labeler, render_engine, settings, justify, margin_px, min_payload_px,
        for_print=True,
    )


def preview_label(widgets: list[dict], settings: dict, upload_dir: str = "") -> bytes:
    """Build render engines from widgets and return a PNG preview as bytes."""
    bitmap = render_preview(
        widgets, settings, upload_dir,
        show_margins=settings.get("showMargins", True),
    )
    buf = BytesIO()
    bitmap.save(buf, format="PNG")
    return buf.getvalue()
