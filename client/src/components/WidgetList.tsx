import { useLabelStore } from "../state/useLabelStore";
import { WidgetEditor } from "./WidgetEditor";

export function WidgetList() {
  const widgets = useLabelStore((s) => s.widgets);

  if (widgets.length === 0) {
    return (
      <div className="text-gray-400 text-sm text-center py-4">
        No widgets. Add one below.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {widgets.map((w) => (
        <WidgetEditor key={w.id} widget={w} />
      ))}
    </div>
  );
}
