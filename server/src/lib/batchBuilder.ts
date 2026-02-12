interface TextWidget {
  type: "text";
  text: string;
}

interface QrWidget {
  type: "qr";
  content: string;
}

interface BarcodeWidget {
  type: "barcode";
  content: string;
  barcodeType: string;
}

type Widget = TextWidget | QrWidget | BarcodeWidget;

/**
 * Build the labelle batch-mode stdin from an array of widgets.
 *
 * Format:
 *   LABELLE-LABEL-SPEC-VERSION:1
 *   TEXT:line1
 *   NEWLINE:line2
 *   QR:content
 *   BARCODE#type:content
 */
export function buildBatchInput(widgets: Widget[]): string {
  const lines: string[] = ["LABELLE-LABEL-SPEC-VERSION:1"];

  for (const w of widgets) {
    switch (w.type) {
      case "text": {
        const textLines = w.text.split("\n");
        if (textLines.length > 0) {
          lines.push(`TEXT:${textLines[0]}`);
          for (let i = 1; i < textLines.length; i++) {
            lines.push(`NEWLINE:${textLines[i]}`);
          }
        }
        break;
      }
      case "qr": {
        if (w.content.trim()) {
          lines.push(`QR:${w.content}`);
        }
        break;
      }
      case "barcode": {
        if (w.content.trim()) {
          const type = w.barcodeType || "code128";
          lines.push(`BARCODE#${type}:${w.content}`);
        }
        break;
      }
    }
  }

  return lines.join("\n") + "\n";
}
