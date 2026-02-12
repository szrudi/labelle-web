import { useLabelStore } from "../state/useLabelStore";
import { TAPE_SIZES, LABEL_COLORS } from "../lib/constants";
import type { TapeSize, Alignment, LabelColor } from "../types/label";

export function SettingsBar() {
  const settings = useLabelStore((s) => s.settings);
  const update = useLabelStore((s) => s.updateSettings);

  return (
    <div className="bg-white rounded-lg shadow p-3 flex flex-wrap items-center gap-4 text-sm">
      <Field label="Tape (mm)">
        <select
          className="input w-20"
          value={settings.tapeSizeMm}
          onChange={(e) =>
            update({ tapeSizeMm: Number(e.target.value) as TapeSize })
          }
        >
          {TAPE_SIZES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Margin (px)">
        <input
          type="number"
          className="input w-20"
          min={0}
          max={500}
          value={settings.marginPx}
          onChange={(e) => update({ marginPx: Number(e.target.value) })}
        />
      </Field>

      <Field label="Min length (mm)">
        <input
          type="number"
          className="input w-20"
          min={0}
          max={500}
          value={settings.minLengthMm}
          onChange={(e) => update({ minLengthMm: Number(e.target.value) })}
        />
      </Field>

      <Field label="Justify">
        <select
          className="input w-24"
          value={settings.justify}
          onChange={(e) => update({ justify: e.target.value as Alignment })}
        >
          <option value="left">Left</option>
          <option value="center">Center</option>
          <option value="right">Right</option>
        </select>
      </Field>

      <Field label="FG color">
        <select
          className="input w-24"
          value={settings.foregroundColor}
          onChange={(e) =>
            update({ foregroundColor: e.target.value as LabelColor })
          }
        >
          {LABEL_COLORS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </Field>

      <Field label="BG color">
        <select
          className="input w-24"
          value={settings.backgroundColor}
          onChange={(e) =>
            update({ backgroundColor: e.target.value as LabelColor })
          }
        >
          {LABEL_COLORS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </Field>

      <label className="flex items-center gap-1.5 cursor-pointer">
        <input
          type="checkbox"
          checked={settings.showMargins}
          onChange={(e) => update({ showMargins: e.target.checked })}
        />
        Show margins
      </label>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex items-center gap-1.5">
      <span className="text-gray-600 whitespace-nowrap">{label}</span>
      {children}
    </label>
  );
}
