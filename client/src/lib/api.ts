import type { LabelWidget, LabelSettings } from "../types/label";

interface PrintResponse {
  status: string;
  message: string;
}

export async function printLabel(
  widgets: LabelWidget[],
  settings: LabelSettings,
): Promise<PrintResponse> {
  const res = await fetch("/api/print", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ widgets, settings }),
  });
  return res.json() as Promise<PrintResponse>;
}

export async function uploadImage(
  file: File,
): Promise<{ filename: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/upload-image", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = (await res.json()) as PrintResponse;
    throw new Error(err.message);
  }
  return res.json() as Promise<{ filename: string }>;
}

export async function fetchServerPreview(
  widgets: LabelWidget[],
  settings: LabelSettings,
  signal?: AbortSignal,
): Promise<string> {
  const res = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ widgets, settings }),
    signal,
  });
  if (!res.ok) {
    const err = (await res.json()) as PrintResponse;
    throw new Error(err.message);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
