import type { LabelWidget, LabelSettings } from "../types/label";
import {
  TAPE_HEIGHT_PX,
  WIDGET_PADDING_PX,
  PIXELS_PER_MM,
  PREVIEW_SCALE,
} from "./constants";
import { renderText } from "./textRenderer";
import { renderQr } from "./qrRenderer";
import { renderBarcode } from "./barcodeRenderer";

const COLOR_MAP: Record<string, string> = {
  white: "#ffffff",
  black: "#000000",
  yellow: "#ffdd00",
  blue: "#0055ff",
  red: "#dd0000",
  green: "#00aa00",
};

function toHex(c: string): string {
  return COLOR_MAP[c] ?? c;
}

/**
 * Render the full label preview onto the provided canvas element.
 * Combines all widgets horizontally, applies margins, justify, and min-length.
 */
export async function renderLabel(
  canvas: HTMLCanvasElement,
  widgets: LabelWidget[],
  settings: LabelSettings,
): Promise<void> {
  const heightPx = TAPE_HEIGHT_PX[settings.tapeSizeMm];
  const fg = toHex(settings.foregroundColor);
  const bg = toHex(settings.backgroundColor);
  const margin = settings.marginPx;
  const minWidthPx = Math.round(settings.minLengthMm * PIXELS_PER_MM);

  // Render each widget to an offscreen canvas
  const bitmaps: OffscreenCanvas[] = [];
  for (const w of widgets) {
    let bmp: OffscreenCanvas | null = null;
    switch (w.type) {
      case "text":
        bmp = renderText(w, heightPx, fg, bg);
        break;
      case "qr":
        bmp = await renderQr(w.content, heightPx, fg, bg);
        break;
      case "barcode":
        bmp = renderBarcode(w, heightPx, fg, bg);
        break;
    }
    if (bmp) bitmaps.push(bmp);
  }

  // Calculate total content width
  const contentWidth =
    bitmaps.length === 0
      ? 0
      : bitmaps.reduce((sum, b) => sum + b.width, 0) +
        WIDGET_PADDING_PX * (bitmaps.length - 1);

  const totalWidth = Math.max(contentWidth + margin * 2, minWidthPx);

  // Apply justify offset
  let contentX: number;
  if (settings.justify === "right") {
    contentX = totalWidth - margin - contentWidth;
  } else if (settings.justify === "center") {
    contentX = (totalWidth - contentWidth) / 2;
  } else {
    contentX = margin;
  }

  // Scale up for display
  const scale = PREVIEW_SCALE;
  canvas.width = totalWidth * scale;
  canvas.height = heightPx * scale;

  const ctx = canvas.getContext("2d")!;
  ctx.imageSmoothingEnabled = false;

  // Fill background
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw each bitmap
  let x = contentX;
  for (const bmp of bitmaps) {
    const yOffset = (heightPx - bmp.height) / 2;
    ctx.drawImage(
      bmp,
      0,
      0,
      bmp.width,
      bmp.height,
      x * scale,
      yOffset * scale,
      bmp.width * scale,
      bmp.height * scale,
    );
    x += bmp.width + WIDGET_PADDING_PX;
  }

  // Draw margin guides
  if (settings.showMargins && margin > 0) {
    ctx.strokeStyle = "rgba(255, 0, 0, 0.5)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    // Left margin
    ctx.beginPath();
    ctx.moveTo(margin * scale, 0);
    ctx.lineTo(margin * scale, canvas.height);
    ctx.stroke();
    // Right margin
    ctx.beginPath();
    ctx.moveTo((totalWidth - margin) * scale, 0);
    ctx.lineTo((totalWidth - margin) * scale, canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}
