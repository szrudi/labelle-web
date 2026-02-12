import JsBarcode from "jsbarcode";
import type { BarcodeWidget } from "../types/label";
import { JSBARCODE_FORMAT_MAP } from "./constants";

/**
 * Render a barcode widget to an offscreen canvas.
 * Returns null if content is empty or barcode generation fails.
 */
export function renderBarcode(
  widget: BarcodeWidget,
  heightPx: number,
  fg: string,
  bg: string,
): OffscreenCanvas | null {
  if (!widget.content.trim()) return null;

  const format = JSBARCODE_FORMAT_MAP[widget.barcodeType] ?? "CODE128";
  const barcodeHeight = widget.showText
    ? Math.round(heightPx * 0.6)
    : heightPx;

  // Use a temporary canvas to render via JsBarcode
  const tmpCanvas = document.createElement("canvas");
  try {
    JsBarcode(tmpCanvas, widget.content, {
      format,
      width: 2,
      height: barcodeHeight,
      displayValue: widget.showText,
      fontSize: Math.max(8, Math.round(heightPx * 0.2)),
      margin: 0,
      background: bg,
      lineColor: fg,
    });
  } catch {
    // Invalid barcode content for format - return null
    return null;
  }

  const w = tmpCanvas.width;
  const h = tmpCanvas.height;
  if (w === 0 || h === 0) return null;

  const canvas = new OffscreenCanvas(w, h);
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(tmpCanvas, 0, 0);
  return canvas;
}
