import type { BarcodeType, TapeSize } from "../types/label";

export const DPI = 180;
export const MM_PER_INCH = 25.4;
export const PIXELS_PER_MM = DPI / MM_PER_INCH; // ~7.087

export const TAPE_HEIGHT_PX: Record<TapeSize, number> = {
  6: 32,
  9: 48,
  12: 64,
  19: 96,
};

export const TAPE_SIZES: TapeSize[] = [6, 9, 12, 19];

export const DEFAULT_MARGIN_PX = 56;
export const WIDGET_PADDING_PX = 4;
export const DEFAULT_FONT_SCALE = 90;
export const FONT_SIZE_RATIO = 7 / 8;

export const BARCODE_TYPES: { value: BarcodeType; label: string }[] = [
  { value: "code128", label: "CODE128" },
  { value: "code39", label: "CODE39" },
  { value: "codabar", label: "CODABAR" },
  { value: "ean13", label: "EAN13" },
  { value: "ean8", label: "EAN8" },
  { value: "upc", label: "UPC" },
  { value: "upca", label: "UPCA" },
  { value: "itf", label: "ITF" },
  { value: "isbn", label: "ISBN" },
  { value: "isbn10", label: "ISBN10" },
  { value: "isbn13", label: "ISBN13" },
  { value: "ean", label: "EAN" },
  { value: "ean14", label: "EAN14" },
  { value: "gs1", label: "GS1" },
  { value: "gs1_128", label: "GS1-128" },
];

/** JsBarcode-supported formats for client-side preview */
export const JSBARCODE_FORMAT_MAP: Partial<Record<BarcodeType, string>> = {
  code128: "CODE128",
  code39: "CODE39",
  ean13: "EAN13",
  ean8: "EAN8",
  upc: "UPC",
  upca: "UPC",
  itf: "ITF",
  codabar: "codabar",
};

export const LABEL_COLORS = [
  "white",
  "black",
  "yellow",
  "blue",
  "red",
  "green",
] as const;

export const PREVIEW_SCALE = 4;
