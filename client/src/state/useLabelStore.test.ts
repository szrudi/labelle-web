import { describe, it, expect, beforeEach } from "vitest";
import { useLabelStore } from "./useLabelStore";
import { DEFAULT_MARGIN_PX, DEFAULT_FONT_SCALE } from "../lib/constants";
import type { LabelWidget, LabelSettings, PrinterInfo } from "../types/label";

beforeEach(() => {
  // Reset store to initial state before each test
  useLabelStore.setState(useLabelStore.getInitialState());
});

describe("Widget CRUD", () => {
  it("addTextWidget adds a text widget with defaults", () => {
    useLabelStore.getState().addTextWidget();
    const widgets = useLabelStore.getState().widgets;
    // Initial "Hello" widget + new one
    expect(widgets).toHaveLength(2);
    const added = widgets[1]!;
    expect(added.type).toBe("text");
    if (added.type === "text") {
      expect(added.text).toBe("");
      expect(added.fontStyle).toBe("regular");
      expect(added.fontScale).toBe(DEFAULT_FONT_SCALE);
      expect(added.frameWidthPx).toBe(0);
      expect(added.align).toBe("left");
    }
  });

  it("addQrWidget adds a QR widget", () => {
    useLabelStore.getState().addQrWidget();
    const widgets = useLabelStore.getState().widgets;
    expect(widgets).toHaveLength(2);
    const added = widgets[1]!;
    expect(added.type).toBe("qr");
    if (added.type === "qr") {
      expect(added.content).toBe("");
    }
  });

  it("addBarcodeWidget adds a barcode widget", () => {
    useLabelStore.getState().addBarcodeWidget();
    const widgets = useLabelStore.getState().widgets;
    expect(widgets).toHaveLength(2);
    const added = widgets[1]!;
    expect(added.type).toBe("barcode");
    if (added.type === "barcode") {
      expect(added.content).toBe("");
      expect(added.barcodeType).toBe("code128");
      expect(added.showText).toBe(false);
    }
  });

  it("addImageWidget adds an image widget with given filename", () => {
    useLabelStore.getState().addImageWidget("photo.png");
    const widgets = useLabelStore.getState().widgets;
    expect(widgets).toHaveLength(2);
    const added = widgets[1]!;
    expect(added.type).toBe("image");
    if (added.type === "image") {
      expect(added.filename).toBe("photo.png");
    }
  });

  it("removeWidget removes by ID", () => {
    const initialId = useLabelStore.getState().widgets[0]!.id;
    useLabelStore.getState().removeWidget(initialId);
    expect(useLabelStore.getState().widgets).toHaveLength(0);
  });

  it("moveWidget reorders widgets", () => {
    useLabelStore.getState().addQrWidget();
    const before = useLabelStore.getState().widgets;
    const firstId = before[0]!.id;
    const secondId = before[1]!.id;

    useLabelStore.getState().moveWidget(0, 1);

    const after = useLabelStore.getState().widgets;
    expect(after[0]!.id).toBe(secondId);
    expect(after[1]!.id).toBe(firstId);
  });

  it("moveWidget is no-op when fromIndex === toIndex", () => {
    const before = useLabelStore.getState().widgets;
    useLabelStore.getState().moveWidget(0, 0);
    const after = useLabelStore.getState().widgets;
    // Same reference (no state update)
    expect(after).toBe(before);
  });

  it("updateWidget merges partial updates", () => {
    const id = useLabelStore.getState().widgets[0]!.id;
    useLabelStore.getState().updateWidget(id, { text: "Updated" } as Partial<LabelWidget>);
    const widget = useLabelStore.getState().widgets[0]!;
    expect(widget.type).toBe("text");
    if (widget.type === "text") {
      expect(widget.text).toBe("Updated");
      // Other fields preserved
      expect(widget.fontStyle).toBe("regular");
    }
  });
});

describe("Settings", () => {
  it("updateSettings merges partial settings", () => {
    useLabelStore.getState().updateSettings({ tapeSizeMm: 19 });
    const settings = useLabelStore.getState().settings;
    expect(settings.tapeSizeMm).toBe(19);
    // Other settings preserved
    expect(settings.justify).toBe("center");
  });

  it("default settings match expected values", () => {
    const settings = useLabelStore.getState().settings;
    expect(settings).toEqual({
      tapeSizeMm: 12,
      marginPx: DEFAULT_MARGIN_PX,
      minLengthMm: 0,
      justify: "center",
      foregroundColor: "black",
      backgroundColor: "white",
      showMargins: false,
    });
  });
});

describe("Printers", () => {
  it("setAvailablePrinters stores printer list", () => {
    const printers: PrinterInfo[] = [
      { id: "usb:1", name: "DYMO", vendorProductId: "0922:1002" },
    ];
    useLabelStore.getState().setAvailablePrinters(printers);
    expect(useLabelStore.getState().availablePrinters).toEqual(printers);
  });
});

describe("Load", () => {
  it("loadLabel replaces widgets and settings", () => {
    const widgets: LabelWidget[] = [
      { id: "new-1", type: "qr", content: "hello" },
    ];
    const settings: LabelSettings = {
      tapeSizeMm: 6,
      marginPx: 20,
      minLengthMm: 10,
      justify: "left",
      foregroundColor: "blue",
      backgroundColor: "yellow",
      showMargins: true,
    };

    useLabelStore.getState().loadLabel(widgets, settings);

    expect(useLabelStore.getState().widgets).toEqual(widgets);
    expect(useLabelStore.getState().settings).toEqual(settings);
  });
});
