import { useRef } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { uploadImage } from "../lib/api";
import type { ImageWidget } from "../types/label";

export function ImageWidgetEditor({ widget }: { widget: ImageWidget }) {
  const update = useLabelStore((s) => s.updateWidget);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    try {
      const { filename } = await uploadImage(file);
      update(widget.id, { filename });
    } catch (err) {
      console.error("Image upload failed:", err);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <img
          src={`/api/uploads/${widget.filename}`}
          alt="Uploaded image"
          className="h-10 rounded border border-gray-200 bg-gray-50"
        />
        <span className="text-xs text-gray-500 truncate flex-1">
          {widget.filename}
        </span>
        <button
          className="btn text-xs"
          onClick={() => fileRef.current?.click()}
        >
          Replace
        </button>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
    </div>
  );
}
