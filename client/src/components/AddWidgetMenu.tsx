import { useLabelStore } from "../state/useLabelStore";

export function AddWidgetMenu() {
  const addText = useLabelStore((s) => s.addTextWidget);
  const addQr = useLabelStore((s) => s.addQrWidget);
  const addBarcode = useLabelStore((s) => s.addBarcodeWidget);

  return (
    <div className="flex gap-2">
      <button className="btn flex-1" onClick={addText}>
        + Text
      </button>
      <button className="btn flex-1" onClick={addQr}>
        + QR
      </button>
      <button className="btn flex-1" onClick={addBarcode}>
        + Barcode
      </button>
    </div>
  );
}
