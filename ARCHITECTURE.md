# Architecture

## Overview

Labelle Web is a monorepo with a React frontend and a Python/Flask backend:

```
labelle-web/
  package.json              # Root: npm workspace for client, dev scripts
  client/                   # Frontend: Vite + React + TypeScript + Tailwind
  server/                   # Backend: Python/Flask, imports labelle as a library
```

The frontend handles all UI. Label preview images are rendered server-side by the backend using labelle's render engines directly, giving pixel-perfect output that matches what will be printed.

## Frontend (`client/`)

### Tech Stack

- **React 19** with TypeScript
- **Vite** for dev server and bundling
- **Tailwind CSS** for styling
- **Zustand** for state management

### State Management

A single Zustand store (`state/useLabelStore.ts`) holds all application state:

```
{
  widgets: LabelWidget[]    # Ordered list of text/QR/barcode widgets
  settings: LabelSettings   # Tape size, margins, justify, colors, etc.
}
```

The store exposes actions for widget CRUD (`addTextWidget`, `removeWidget`, `updateWidget`) and settings updates (`updateSettings`). All components subscribe to the store via selectors, so changes automatically trigger re-renders.

### Component Tree

```
App
  SettingsBar               # Tape size, margin, min-length, justify, colors, show-margins
  WidgetList                # Maps widgets[] to WidgetEditor components
    WidgetEditor            # Type badge + delete button + dispatches to:
      TextWidgetEditor      # Textarea, font style/scale, frame, alignment
      QrWidgetEditor        # Content input
      BarcodeWidgetEditor   # Content, type dropdown, show-text toggle
  AddWidgetMenu             # + Text / + QR / + Barcode buttons
  PrintButton               # Print trigger with loading/success/error states
  LabelPreview              # Server-rendered preview image with debounced fetching
```

### Server-Side Preview

The preview updates on every state change with a 300ms debounce. The `LabelPreview` component calls `POST /api/preview` with the current widgets and settings, and displays the returned PNG image. An `AbortController` cancels in-flight requests when state changes again, and previous object URLs are revoked to prevent memory leaks. The preview is pixel-perfect because it uses the same labelle render engines as printing.

### Type Definitions

All shared types live in `types/label.ts`:

- `TextWidget` -- text, fontStyle, fontScale, frameWidthPx, align
- `QrWidget` -- content
- `BarcodeWidget` -- content, barcodeType, showText
- `LabelSettings` -- tapeSizeMm, marginPx, minLengthMm, justify, foregroundColor, backgroundColor, showMargins
- Union type `LabelWidget = TextWidget | QrWidget | BarcodeWidget`

### Constants

`lib/constants.ts` defines shared UI constants:

| Constant | Value | Description |
|----------|-------|-------------|
| `TAPE_SIZES` | [6, 9, 12, 19] | Available tape widths in mm |
| `DEFAULT_MARGIN_PX` | 56 | Default horizontal margin (from labelle) |
| `DEFAULT_FONT_SCALE` | 90 | Default font scale percentage |
| `BARCODE_TYPES` | 15 types | Barcode format options for the dropdown |
| `LABEL_COLORS` | 6 colors | Available foreground/background colors |

## Backend (`server/`)

### Tech Stack

- **Flask** (Python) with flask-cors
- **labelle** imported as a Python library (not called as a CLI subprocess)

### Request Flow

```
POST /api/print
  -> app.py (api_print)
    -> label_builder.print_label(widgets, settings)
      -> _build_render_engines(widgets)     # Per-widget render engines
      -> HorizontallyCombinedRenderEngine   # Combine all widgets
      -> PrintPayloadRenderEngine           # Add margins, justify
      -> DymoLabeler.print(bitmap)          # Send to printer via USB
  <- { status, message }

POST /api/preview
  -> app.py (api_preview)
    -> label_builder.preview_label(widgets, settings)
      -> _build_render_engines(widgets)     # Per-widget render engines
      -> HorizontallyCombinedRenderEngine   # Combine all widgets
      -> PrintPreviewRenderEngine           # Add visual margins/guides
      -> PNG bytes via PIL
  <- image/png
```

### Label Builder (`label_builder.py`)

Converts the widget JSON array into labelle `RenderEngine` instances:

- **Text widgets** → `TextRenderEngine` with per-widget `font_file_name`, `font_size_ratio`, `frame_width_px`, and `align`. Each text widget gets its own font style via `get_font_path(style=...)`.
- **QR widgets** → `QrRenderEngine(content)`
- **Barcode widgets** → `BarcodeRenderEngine(content, barcode_type)` or `BarcodeWithTextRenderEngine(content, font_file_name, barcode_type)` when `showText` is true.

All engines are combined with `HorizontallyCombinedRenderEngine`, then wrapped with either `PrintPayloadRenderEngine` (for printing) or `PrintPreviewRenderEngine` (for preview).

Settings like `marginPx`, `minLengthMm`, `justify`, `tapeSizeMm`, `foregroundColor`, and `backgroundColor` are applied via `RenderContext` and the payload/preview wrapper.

### Flask App (`app.py`)

- `POST /api/print` — validates request, calls `print_label()`, returns JSON status
- `POST /api/preview` — validates request, calls `preview_label()`, returns PNG bytes
- Static file serving from `dist-client/` with SPA fallback to `index.html`

## Build and Deployment

### Development

`npm run dev` uses `concurrently` to start:
- Vite dev server on port 5173 (with HMR)
- Flask dev server on port 5000

Vite proxies `/api/*` requests to the Flask backend.

### Production

`npm run build` runs `vite build` in `client/` (outputs to `server/dist-client/`).

`npm start` runs the Flask server (`python server/app.py`), which serves both the static client bundle and the API on a single port.

### Deployment Diagram

```
Browser (any device on LAN)
    |
    | HTTP :5000
    v
Flask Server (e.g. Raspberry Pi)
    |
    | labelle library (direct Python import)
    |
    | USB
    v
DYMO Label Printer
```
