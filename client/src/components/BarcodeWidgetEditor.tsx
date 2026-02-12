import { useLabelStore } from "../state/useLabelStore";
import { BARCODE_TYPES } from "../lib/constants";
import type { BarcodeWidget, BarcodeType } from "../types/label";

export function BarcodeWidgetEditor({ widget }: { widget: BarcodeWidget }) {
  const update = useLabelStore((s) => s.updateWidget);

  return (
    <div className="space-y-2">
      <input
        className="input w-full"
        type="text"
        placeholder="Barcode content..."
        value={widget.content}
        onChange={(e) => update(widget.id, { content: e.target.value })}
      />
      <div className="flex flex-wrap gap-2">
        <label className="flex items-center gap-1 text-xs">
          Type
          <select
            className="input text-xs"
            value={widget.barcodeType}
            onChange={(e) =>
              update(widget.id, {
                barcodeType: e.target.value as BarcodeType,
              })
            }
          >
            {BARCODE_TYPES.map((bt) => (
              <option key={bt.value} value={bt.value}>
                {bt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-1 text-xs cursor-pointer">
          <input
            type="checkbox"
            checked={widget.showText}
            onChange={(e) => update(widget.id, { showText: e.target.checked })}
          />
          Show text
        </label>
      </div>
    </div>
  );
}
