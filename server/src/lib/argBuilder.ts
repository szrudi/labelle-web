interface Settings {
  tapeSizeMm?: number;
  marginPx?: number;
  minLengthMm?: number;
  justify?: string;
  foregroundColor?: string;
  backgroundColor?: string;
}

interface TextWidgetStyle {
  fontStyle?: string;
  fontScale?: number;
  frameWidthPx?: number;
  align?: string;
}

/**
 * Build CLI arguments from settings and optional first-text-widget style.
 * Returns an array of strings for spawning the labelle process.
 */
export function buildArgs(
  settings: Settings,
  firstTextStyle: TextWidgetStyle | null,
  output?: string,
): string[] {
  const args: string[] = ["--batch"];

  if (settings.tapeSizeMm != null) {
    args.push("--tape-size-mm", String(settings.tapeSizeMm));
  }
  if (settings.marginPx != null) {
    args.push("--margin-px", String(settings.marginPx));
  }
  if (settings.minLengthMm != null && settings.minLengthMm > 0) {
    args.push("--min-length", String(settings.minLengthMm));
  }
  if (settings.justify && settings.justify !== "left") {
    args.push("--justify", settings.justify);
  }

  // Style from first text widget (CLI limitation: one global style)
  if (firstTextStyle) {
    if (firstTextStyle.fontStyle && firstTextStyle.fontStyle !== "regular") {
      args.push("--style", firstTextStyle.fontStyle);
    }
    if (firstTextStyle.fontScale != null) {
      args.push("--font-scale", String(firstTextStyle.fontScale));
    }
    if (firstTextStyle.frameWidthPx != null && firstTextStyle.frameWidthPx > 0) {
      args.push("--frame-width-px", String(firstTextStyle.frameWidthPx));
    }
    if (firstTextStyle.align && firstTextStyle.align !== "left") {
      args.push("--align", firstTextStyle.align);
    }
  }

  if (output) {
    args.push("--output", output);
  }

  return args;
}
