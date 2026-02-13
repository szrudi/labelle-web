import { useRef } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { uploadImage } from "../lib/api";

export function AddWidgetMenu() {
  const addText = useLabelStore((s) => s.addTextWidget);
  const addQr = useLabelStore((s) => s.addQrWidget);
  const addBarcode = useLabelStore((s) => s.addBarcodeWidget);
  const addImage = useLabelStore((s) => s.addImageWidget);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    try {
      const { filename } = await uploadImage(file);
      addImage(filename);
    } catch (err) {
      console.error("Image upload failed:", err);
    }
  };

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
      <button className="btn flex-1" onClick={() => fileRef.current?.click()}>
        + Image
      </button>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />
    </div>
  );
}
