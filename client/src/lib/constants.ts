import type { BarcodeType, TapeSize } from "../types/label";

export const TAPE_SIZES: TapeSize[] = [6, 9, 12, 19];

export const DEFAULT_MARGIN_PX = 56;
export const DEFAULT_FONT_SCALE = 90;

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

export const LABEL_COLORS = [
  "white",
  "black",
  "yellow",
  "blue",
  "red",
  "green",
] as const;
