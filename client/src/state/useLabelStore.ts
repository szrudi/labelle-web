import { create } from "zustand";
import { v4 as uuidv4 } from "uuid";
import type {
  LabelWidget,
  LabelSettings,
  TextWidget,
  QrWidget,
  BarcodeWidget,
  ImageWidget,
} from "../types/label";
import { DEFAULT_MARGIN_PX, DEFAULT_FONT_SCALE } from "../lib/constants";

interface LabelStore {
  widgets: LabelWidget[];
  settings: LabelSettings;

  addTextWidget: () => void;
  addQrWidget: () => void;
  addBarcodeWidget: () => void;
  addImageWidget: (filename: string) => void;
  removeWidget: (id: string) => void;
  moveWidget: (fromIndex: number, toIndex: number) => void;
  updateWidget: (id: string, patch: Partial<LabelWidget>) => void;
  updateSettings: (patch: Partial<LabelSettings>) => void;
  loadLabel: (widgets: LabelWidget[], settings: LabelSettings) => void;
}

export const useLabelStore = create<LabelStore>((set) => ({
  widgets: [
    {
      id: uuidv4(),
      type: "text",
      text: "Hello",
      fontStyle: "regular",
      fontScale: DEFAULT_FONT_SCALE,
      frameWidthPx: 0,
      align: "left",
    } satisfies TextWidget,
  ],

  settings: {
    tapeSizeMm: 12,
    marginPx: DEFAULT_MARGIN_PX,
    minLengthMm: 0,
    justify: "center",
    foregroundColor: "black",
    backgroundColor: "white",
    showMargins: false,
  },

  addTextWidget: () =>
    set((s) => ({
      widgets: [
        ...s.widgets,
        {
          id: uuidv4(),
          type: "text",
          text: "",
          fontStyle: "regular",
          fontScale: DEFAULT_FONT_SCALE,
          frameWidthPx: 0,
          align: "left",
        } satisfies TextWidget,
      ],
    })),

  addQrWidget: () =>
    set((s) => ({
      widgets: [
        ...s.widgets,
        {
          id: uuidv4(),
          type: "qr",
          content: "",
        } satisfies QrWidget,
      ],
    })),

  addBarcodeWidget: () =>
    set((s) => ({
      widgets: [
        ...s.widgets,
        {
          id: uuidv4(),
          type: "barcode",
          content: "",
          barcodeType: "code128",
          showText: false,
        } satisfies BarcodeWidget,
      ],
    })),

  addImageWidget: (filename: string) =>
    set((s) => ({
      widgets: [
        ...s.widgets,
        {
          id: uuidv4(),
          type: "image",
          filename,
        } satisfies ImageWidget,
      ],
    })),

  removeWidget: (id) =>
    set((s) => ({ widgets: s.widgets.filter((w) => w.id !== id) })),

  moveWidget: (fromIndex, toIndex) =>
    set((s) => {
      if (fromIndex === toIndex) return s;
      const moved = s.widgets[fromIndex];
      if (!moved) return s;
      const widgets = s.widgets.filter((_, i) => i !== fromIndex);
      widgets.splice(toIndex, 0, moved);
      return { widgets };
    }),

  updateWidget: (id, patch) =>
    set((s) => ({
      widgets: s.widgets.map((w) =>
        w.id === id ? ({ ...w, ...patch } as LabelWidget) : w,
      ),
    })),

  updateSettings: (patch) =>
    set((s) => ({ settings: { ...s.settings, ...patch } })),

  loadLabel: (widgets, settings) => set({ widgets, settings }),
}));
