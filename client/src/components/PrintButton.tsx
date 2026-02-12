import { useState } from "react";
import { useLabelStore } from "../state/useLabelStore";
import { printLabel } from "../lib/api";

export function PrintButton() {
  const widgets = useLabelStore((s) => s.widgets);
  const settings = useLabelStore((s) => s.settings);
  const [status, setStatus] = useState<{
    type: "idle" | "loading" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  const handlePrint = async () => {
    if (widgets.length === 0) {
      setStatus({ type: "error", message: "Add at least one widget" });
      return;
    }

    setStatus({ type: "loading" });
    try {
      const result = await printLabel(widgets, settings);
      if (result.status === "success") {
        setStatus({ type: "success", message: result.message });
      } else {
        setStatus({ type: "error", message: result.message });
      }
    } catch (err) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Network error",
      });
    }

    // Clear success after 3 seconds
    setTimeout(() => {
      setStatus((s) => (s.type === "success" ? { type: "idle" } : s));
    }, 3000);
  };

  return (
    <div>
      <button
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 rounded-lg font-semibold transition-colors"
        onClick={handlePrint}
        disabled={status.type === "loading"}
      >
        {status.type === "loading" ? "Printing..." : "Print Label"}
      </button>
      {status.message && (
        <p
          className={`text-sm mt-2 text-center ${
            status.type === "success" ? "text-green-600" : "text-red-600"
          }`}
        >
          {status.message}
        </p>
      )}
    </div>
  );
}
