import { useLabelStore } from "../state/useLabelStore";
import type { TextWidget, FontStyle, Alignment } from "../types/label";

export function TextWidgetEditor({ widget }: { widget: TextWidget }) {
  const update = useLabelStore((s) => s.updateWidget);

  return (
    <div className="space-y-2">
      <textarea
        className="input w-full resize-none"
        rows={2}
        placeholder="Label text..."
        value={widget.text}
        onChange={(e) => update(widget.id, { text: e.target.value })}
      />
      <div className="flex flex-wrap gap-2">
        <label className="flex items-center gap-1 text-xs">
          Style
          <select
            className="input text-xs"
            value={widget.fontStyle}
            onChange={(e) =>
              update(widget.id, { fontStyle: e.target.value as FontStyle })
            }
          >
            <option value="regular">Regular</option>
            <option value="bold">Bold</option>
            <option value="italic">Italic</option>
            <option value="narrow">Narrow</option>
          </select>
        </label>

        <label className="flex items-center gap-1 text-xs">
          Scale %
          <input
            type="number"
            className="input text-xs w-16"
            min={10}
            max={150}
            value={widget.fontScale}
            onChange={(e) =>
              update(widget.id, { fontScale: Number(e.target.value) })
            }
          />
        </label>

        <label className="flex items-center gap-1 text-xs">
          Frame
          <input
            type="number"
            className="input text-xs w-14"
            min={0}
            max={20}
            value={widget.frameWidthPx}
            onChange={(e) =>
              update(widget.id, { frameWidthPx: Number(e.target.value) })
            }
          />
        </label>

        <label className="flex items-center gap-1 text-xs">
          Align
          <select
            className="input text-xs"
            value={widget.align}
            onChange={(e) =>
              update(widget.id, { align: e.target.value as Alignment })
            }
          >
            <option value="left">Left</option>
            <option value="center">Center</option>
            <option value="right">Right</option>
          </select>
        </label>
      </div>
    </div>
  );
}
