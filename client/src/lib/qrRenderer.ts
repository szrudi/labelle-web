import QRCode from "qrcode";

/**
 * Render a QR code to an offscreen canvas, scaled to fit the tape height.
 * Returns null if content is empty.
 */
export async function renderQr(
  content: string,
  heightPx: number,
  fg: string,
  bg: string,
): Promise<OffscreenCanvas | null> {
  if (!content.trim()) return null;

  // Generate QR as a data array using qrcode library
  const modules = QRCode.create(content, {
    errorCorrectionLevel: "M",
  }).modules;

  const size = modules.size; // number of modules per side
  const data = modules.data;
  const scale = Math.max(1, Math.floor(heightPx / size));
  const canvasSize = size * scale;

  const canvas = new OffscreenCanvas(canvasSize, canvasSize);
  const ctx = canvas.getContext("2d")!;

  // Background
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvasSize, canvasSize);

  // Draw modules
  ctx.fillStyle = fg;
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (data[row * size + col]) {
        ctx.fillRect(col * scale, row * scale, scale, scale);
      }
    }
  }

  return canvas;
}
