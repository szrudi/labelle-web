import type { TextWidget } from "../types/label";
import { FONT_SIZE_RATIO } from "./constants";

const FONT_FAMILY_MAP: Record<string, string> = {
  regular: "sans-serif",
  bold: "sans-serif",
  italic: "sans-serif",
  narrow: "Arial Narrow, sans-serif",
};

function getFontString(style: string, sizePx: number): string {
  const family = FONT_FAMILY_MAP[style] ?? "sans-serif";
  const weight = style === "bold" ? "bold" : "normal";
  const fontStyle = style === "italic" ? "italic" : "normal";
  return `${fontStyle} ${weight} ${sizePx}px ${family}`;
}

/**
 * Render a text widget to an offscreen canvas and return its ImageData.
 * Returns null if the text is empty.
 */
export function renderText(
  widget: TextWidget,
  heightPx: number,
  fg: string,
  bg: string,
): OffscreenCanvas | null {
  const lines = widget.text.split("\n").filter((_, i, arr) => {
    // keep all lines except trailing empty ones
    return !(i === arr.length - 1 && arr[i] === "");

  });
  if (lines.length === 0) return null;

  const numLines = lines.length;
  const lineHeight = heightPx / numLines;
  const scaleFactor = (widget.fontScale / 100) * FONT_SIZE_RATIO;
  const fontSize = Math.max(4, Math.round(lineHeight * scaleFactor));
  const font = getFontString(widget.fontStyle, fontSize);
  const frame = widget.frameWidthPx;

  // Measure text widths
  const measure = new OffscreenCanvas(1, 1).getContext("2d")!;
  measure.font = font;
  let maxWidth = 0;
  const metrics: TextMetrics[] = [];
  for (const line of lines) {
    const m = measure.measureText(line || " ");
    metrics.push(m);
    maxWidth = Math.max(maxWidth, m.width);
  }

  const padding = 4;
  const totalWidth = Math.ceil(maxWidth) + frame * 2 + padding * 2;
  const totalHeight = heightPx;

  const canvas = new OffscreenCanvas(totalWidth, totalHeight);
  const ctx = canvas.getContext("2d")!;

  // Background
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, totalWidth, totalHeight);

  // Frame
  if (frame > 0) {
    ctx.strokeStyle = fg;
    ctx.lineWidth = frame;
    const half = frame / 2;
    ctx.strokeRect(half, half, totalWidth - frame, totalHeight - frame);
  }

  // Draw text lines
  ctx.fillStyle = fg;
  ctx.font = font;
  ctx.textBaseline = "middle";

  const alignMap: Record<string, CanvasTextAlign> = {
    left: "left",
    center: "center",
    right: "right",
  };
  ctx.textAlign = alignMap[widget.align] ?? "left";

  let xAnchor: number;
  if (widget.align === "center") {
    xAnchor = totalWidth / 2;
  } else if (widget.align === "right") {
    xAnchor = totalWidth - frame - padding;
  } else {
    xAnchor = frame + padding;
  }

  for (let i = 0; i < lines.length; i++) {
    const y = lineHeight * i + lineHeight / 2;
    ctx.fillText(lines[i]!, xAnchor, y);
  }

  return canvas;
}
