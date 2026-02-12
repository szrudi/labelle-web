import { useLabelStore } from "../state/useLabelStore";
import type { QrWidget } from "../types/label";

export function QrWidgetEditor({ widget }: { widget: QrWidget }) {
  const update = useLabelStore((s) => s.updateWidget);

  return (
    <input
      className="input w-full"
      type="text"
      placeholder="QR content (URL, text...)"
      value={widget.content}
      onChange={(e) => update(widget.id, { content: e.target.value })}
    />
  );
}
