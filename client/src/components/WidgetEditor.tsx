import { useRef } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { TextWidgetEditor } from "./TextWidgetEditor";
import { QrWidgetEditor } from "./QrWidgetEditor";
import { BarcodeWidgetEditor } from "./BarcodeWidgetEditor";
import { ImageWidgetEditor } from "./ImageWidgetEditor";
import type { LabelWidget } from "../types/label";

const TYPE_LABELS: Record<LabelWidget["type"], string> = {
  text: "Aa",
  qr: "QR",
  barcode: "|||",
  image: "IMG",
};

interface WidgetEditorProps {
  widget: LabelWidget;
  index: number;
  isDragging: boolean;
  isOver: boolean;
  onDragStart: (index: number, e: React.DragEvent) => void;
  onDragOver: (index: number, e: React.DragEvent) => void;
  onDragEnd: () => void;
}

export function WidgetEditor({
  widget,
  index,
  isDragging,
  isOver,
  onDragStart,
  onDragOver,
  onDragEnd,
}: WidgetEditorProps) {
  const remove = useLabelStore((s) => s.removeWidget);
  const cardRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={cardRef}
      className={`bg-white rounded-lg shadow p-3 transition-all duration-150 ${
        isDragging ? "opacity-50" : ""
      } ${isOver ? "ring-2 ring-blue-400" : ""}`}
      onDragOver={(e) => onDragOver(index, e)}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span
            draggable
            onDragStart={(e) => {
              if (cardRef.current) {
                const rect = cardRef.current.getBoundingClientRect();
                e.dataTransfer.setDragImage(
                  cardRef.current,
                  e.clientX - rect.left,
                  e.clientY - rect.top,
                );
              }
              onDragStart(index, e);
            }}
            onDragEnd={onDragEnd}
            className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 select-none"
            title="Drag to reorder"
          >
            ⠿
          </span>
          <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
            {TYPE_LABELS[widget.type]}
          </span>
        </div>
        <button
          className="text-red-500 hover:text-red-700 text-sm px-1"
          onClick={() => remove(widget.id)}
          title="Remove widget"
        >
          &times;
        </button>
      </div>
      {widget.type === "text" && <TextWidgetEditor widget={widget} />}
      {widget.type === "qr" && <QrWidgetEditor widget={widget} />}
      {widget.type === "barcode" && <BarcodeWidgetEditor widget={widget} />}
      {widget.type === "image" && <ImageWidgetEditor widget={widget} />}
    </div>
  );
}
