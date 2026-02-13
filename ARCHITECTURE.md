# Architecture

## Overview

Labelle Web is a monorepo with a React frontend and a Python/Flask backend:

```
labelle-web/
  package.json              # Root: npm workspace for client, dev scripts
  client/                   # Frontend: Vite + React + TypeScript + Tailwind
  server/                   # Backend: Python/Flask, imports labelle as a library
```

The frontend handles all UI and provides instant canvas-based label preview. The backend imports labelle's render engines directly, giving full per-widget style support and foreground/background color control.

## Frontend (`client/`)

### Tech Stack

- **React 19** with TypeScript
- **Vite** for dev server and bundling
- **Tailwind CSS** for styling
- **Zustand** for state management
- **qrcode** for QR code generation
- **JsBarcode** for barcode generation

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
  LabelPreview              # Canvas element with debounced rendering
```

### Canvas Preview Pipeline

The preview re-renders on every state change with a 150ms debounce:

1. Each widget is rendered to an individual `OffscreenCanvas`:
   - **Text** (`lib/textRenderer.ts`): Measures text, calculates font size from line height and scale, draws with alignment and optional frame border
   - **QR** (`lib/qrRenderer.ts`): Generates QR modules via the `qrcode` library, scales to tape height
   - **Barcode** (`lib/barcodeRenderer.ts`): Renders via JsBarcode to a temporary DOM canvas, transfers to OffscreenCanvas

2. The orchestrator (`lib/canvasRenderer.ts`) combines all widget bitmaps:
   - Places widgets horizontally with 4px padding
   - Applies left/right margins
   - Applies justify (left/center/right positioning within the label)
   - Enforces minimum label length
   - Fills background color, draws foreground color
   - Optionally draws red dashed margin guides
   - Scales everything 4x for crisp display

### Type Definitions

All shared types live in `types/label.ts`:

- `TextWidget` -- text, fontStyle, fontScale, frameWidthPx, align
- `QrWidget` -- content
- `BarcodeWidget` -- content, barcodeType, showText
- `LabelSettings` -- tapeSizeMm, marginPx, minLengthMm, justify, foregroundColor, backgroundColor, showMargins
- Union type `LabelWidget = TextWidget | QrWidget | BarcodeWidget`

### Constants

`lib/constants.ts` defines values derived from the labelle Python source:

| Constant | Value | Source |
|----------|-------|--------|
| DPI | 180 | labelle `constants.py` |
| PIXELS_PER_MM | ~7.087 | 180 / 25.4 |
| Tape 6mm height | 32px | labelle device config |
| Tape 9mm height | 48px | labelle device config |
| Tape 12mm height | 64px | labelle device config |
| Tape 19mm height | 96px | labelle device config |
| Default margin | 56px | labelle `DEFAULT_MARGIN_PX` |
| Widget padding | 4px | labelle `HorizontallyCombinedRenderEngine` |
| Font size ratio | 7/8 | labelle `FONT_SIZERATIO` |
| Default font scale | 90% | labelle CLI default |

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
