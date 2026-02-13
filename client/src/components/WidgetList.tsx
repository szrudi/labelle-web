import { useState, useCallback } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { WidgetEditor } from "./WidgetEditor";

export function WidgetList() {
  const widgets = useLabelStore((s) => s.widgets);
  const moveWidget = useLabelStore((s) => s.moveWidget);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);

  const handleDragStart = useCallback(
    (index: number, e: React.DragEvent) => {
      setDragIndex(index);
      e.dataTransfer.effectAllowed = "move";
    },
    [],
  );

  const handleDragOver = useCallback(
    (index: number, e: React.DragEvent) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setOverIndex(index);
    },
    [],
  );

  const handleDragEnd = useCallback(() => {
    if (dragIndex !== null && overIndex !== null && dragIndex !== overIndex) {
      moveWidget(dragIndex, overIndex);
    }
    setDragIndex(null);
    setOverIndex(null);
  }, [dragIndex, overIndex, moveWidget]);

  if (widgets.length === 0) {
    return (
      <div className="text-gray-400 text-sm text-center py-4">
        No widgets. Add one below.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {widgets.map((w, i) => (
        <WidgetEditor
          key={w.id}
          widget={w}
          index={i}
          isDragging={dragIndex === i}
          isOver={dragIndex !== null && dragIndex !== i && overIndex === i}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        />
      ))}
    </div>
  );
}
