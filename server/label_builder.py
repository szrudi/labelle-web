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
from labelle.lib.devices.device_manager import DeviceManager
from labelle.lib.devices.dymo_labeler import DymoLabeler

from config import get_virtual_printers
from virtual_printer import VirtualPrinter
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


def _render_payload(
    dymo_labeler: DymoLabeler,
    render_engine: RenderEngine,
    settings: dict,
    justify: Direction,
    margin_px: float,
    min_payload_px: float,
) -> Image.Image:
    """Render a label bitmap from the given engine and settings."""
    render_context = RenderContext(
        height_px=dymo_labeler.height_px,
        foreground_color=settings.get("foregroundColor", "black"),
        background_color=settings.get("backgroundColor", "white"),
    )
    payload = PrintPayloadRenderEngine(
        render_engine=render_engine,
        justify=justify,
        visible_horizontal_margin_px=margin_px,
        labeler_margin_px=dymo_labeler.labeler_margin_px,
        min_width_px=min_payload_px,
    )
    bitmap, _ = payload.render_with_meta(render_context)
    return bitmap


def print_label(
    widgets: list[dict], settings: dict, upload_dir: str = "", printer_id: str | None = None
) -> None:
    """Build render engines from widgets and print to the connected DYMO printer or virtual printer.

    Args:
        widgets: List of widget dictionaries to render
        settings: Label settings (tape size, margins, etc.)
        upload_dir: Directory where uploaded images are stored
        printer_id: Optional printer ID to use. Can be:
                   - USB ID (e.g. "Bus 001 Device 005: ID 0922:1234") for real printer
                   - virtual:name (e.g. "virtual:Office_Printer") for virtual printer
                   - None to auto-select first available real printer
    """
    engines = _build_render_engines(widgets, upload_dir)
    if not engines:
        raise ValueError("No renderable widgets provided")

    render_engine = HorizontallyCombinedRenderEngine(engines)

    margin_px = settings.get("marginPx", DEFAULT_MARGIN_PX)
    min_length_mm = settings.get("minLengthMm", 0)
    min_payload_px = mm_to_payload_px(min_length_mm, margin_px)
    justify = Direction(settings.get("justify", "center"))

    # Check if this is a virtual printer request
    if printer_id and printer_id.startswith("virtual:"):
        # Handle virtual printer - save to file instead of printing
        virtual_printers_config = get_virtual_printers()

        # Find matching virtual printer
        virtual_printer = None
        for config in virtual_printers_config:
            test_printer = VirtualPrinter(config["name"], config["path"])
            if test_printer.id == printer_id:
                virtual_printer = test_printer
                break

        if not virtual_printer:
            raise ValueError(f"Virtual printer not found: {printer_id}")

        # Use DymoLabeler without device just to get dimensions
        dymo_labeler = DymoLabeler(tape_size_mm=settings.get("tapeSizeMm", 12))
        bitmap = _render_payload(dymo_labeler, render_engine, settings, justify, margin_px, min_payload_px)

        # Save to file instead of printing
        virtual_printer.save_label(bitmap)
    else:
        # Try real USB printer first
        device = None
        try:
            device_manager = DeviceManager()
            device_manager.scan()

            # TODO: Future improvement - store per-printer settings (tape size, margins, color)
            if printer_id:
                # Find printer by USB ID
                matching_devices = [dev for dev in device_manager.devices if dev.usb_id == printer_id]
                if not matching_devices:
                    raise ValueError(f"Printer not found: {printer_id}")
                device = matching_devices[0]
            else:
                # Auto-select first available USB printer
                device = device_manager.find_and_select_device()
        except Exception:
            # If a specific printer was requested but not found, don't fall back
            if printer_id:
                raise

            # Auto-select: fall back to first virtual printer
            virtual_printers_config = get_virtual_printers()
            if virtual_printers_config:
                config = virtual_printers_config[0]
                virtual_printer = VirtualPrinter(config["name"], config["path"])

                dymo_labeler = DymoLabeler(tape_size_mm=settings.get("tapeSizeMm", 12))
                bitmap = _render_payload(dymo_labeler, render_engine, settings, justify, margin_px, min_payload_px)
                virtual_printer.save_label(bitmap)
                return

            raise ValueError("No printers available (no USB printers found and no virtual printers configured)")

        device.setup()

        dymo_labeler = DymoLabeler(
            tape_size_mm=settings.get("tapeSizeMm", 12),
            device=device,
        )
        bitmap = _render_payload(dymo_labeler, render_engine, settings, justify, margin_px, min_payload_px)
        dymo_labeler.print(bitmap)


def preview_label(widgets: list[dict], settings: dict, upload_dir: str = "") -> bytes:
    """Build render engines from widgets and return a PNG preview as bytes."""
    engines = _build_render_engines(widgets, upload_dir)
    if not engines:
        raise ValueError("No renderable widgets provided")

    render_engine = HorizontallyCombinedRenderEngine(engines)

    margin_px = settings.get("marginPx", DEFAULT_MARGIN_PX)
    min_length_mm = settings.get("minLengthMm", 0)
    min_payload_px = mm_to_payload_px(min_length_mm, margin_px)
    justify = Direction(settings.get("justify", "center"))

    dymo_labeler = DymoLabeler(tape_size_mm=settings.get("tapeSizeMm", 12))

    render_context = RenderContext(
        height_px=dymo_labeler.height_px,
        foreground_color=settings.get("foregroundColor", "black"),
        background_color=settings.get("backgroundColor", "white"),
        preview_show_margins=settings.get("showMargins", True),
    )

    preview = PrintPreviewRenderEngine(
        render_engine=render_engine,
        justify=justify,
        visible_horizontal_margin_px=margin_px,
        labeler_margin_px=dymo_labeler.labeler_margin_px,
        min_width_px=min_payload_px,
    )
    bitmap = preview.render(render_context)

    buf = BytesIO()
    bitmap.save(buf, format="PNG")
    return buf.getvalue()
