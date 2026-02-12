import { useRef, useEffect } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { renderLabel } from "../lib/canvasRenderer";

export function LabelPreview() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const widgets = useLabelStore((s) => s.widgets);
  const settings = useLabelStore((s) => s.settings);

  useEffect(() => {
    const timer = setTimeout(() => {
      const canvas = canvasRef.current;
      if (canvas) {
        renderLabel(canvas, widgets, settings);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [widgets, settings]);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-sm font-medium text-gray-600 mb-2">Preview</h2>
      <div className="overflow-x-auto">
        <canvas
          ref={canvasRef}
          className="border border-gray-200 rounded"
          style={{ imageRendering: "pixelated", maxWidth: "100%", height: "auto" }}
        />
      </div>
    </div>
  );
}
