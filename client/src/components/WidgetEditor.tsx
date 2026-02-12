import { useLabelStore } from "../state/useLabelStore";
import { TextWidgetEditor } from "./TextWidgetEditor";
import { QrWidgetEditor } from "./QrWidgetEditor";
import { BarcodeWidgetEditor } from "./BarcodeWidgetEditor";
import type { LabelWidget } from "../types/label";

const TYPE_LABELS: Record<LabelWidget["type"], string> = {
  text: "Aa",
  qr: "QR",
  barcode: "|||",
};

export function WidgetEditor({ widget }: { widget: LabelWidget }) {
  const remove = useLabelStore((s) => s.removeWidget);

  return (
    <div className="bg-white rounded-lg shadow p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
          {TYPE_LABELS[widget.type]}
        </span>
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
    </div>
  );
}
