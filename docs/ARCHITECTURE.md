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
  widgets: LabelWidget[]    # Ordered list of text/QR/barcode/image widgets
  settings: LabelSettings   # Tape size, margins, justify, colors, etc.
  batch: BatchState          # Batch print config: copies, pause, variable rows
}
```

The store exposes actions for widget CRUD (`addTextWidget`, `removeWidget`, `updateWidget`), settings updates (`updateSettings`), and batch management (`updateBatch`, `setBatchRow`, `addBatchRow`, `removeBatchRow`). All components subscribe to the store via selectors, so changes automatically trigger re-renders.

### Component Tree

```
App
  WidgetList                # Maps widgets[] to WidgetEditor components, drag-and-drop reorder
    WidgetEditor            # Drag handle + type badge + delete button + dispatches to:
      TextWidgetEditor      # Textarea, font style/scale, frame, alignment
      QrWidgetEditor        # Content input
      BarcodeWidgetEditor   # Content, type dropdown, show-text toggle
      ImageWidgetEditor     # Thumbnail, filename, replace button
  AddWidgetMenu             # + Text / + QR / + Barcode / + Image buttons
  PrintButton               # Print trigger with loading/success/error states; batch mode
  SaveLoadButtons           # Save/load label JSON files (v2 format with batch data)
  BatchPanel                # Batch print config: copies, pause, variable table
  SettingsBar               # Tape size, margin, min-length, justify, colors, show-margins
  LabelPreview              # Server-rendered preview image with debounced fetching
```

### Server-Side Preview

The preview updates on every state change with a 300ms debounce. The `LabelPreview` component calls `POST /api/preview` with the current widgets and settings, and displays the returned PNG image. An `AbortController` cancels in-flight requests when state changes again, and previous object URLs are revoked to prevent memory leaks. The preview is pixel-perfect because it uses the same labelle render engines as printing.

When batch mode is active and a row is selected, `LabelPreview` substitutes variables before sending to the server, so the preview shows the resolved content for that row.

### Batch Print

The batch print feature allows printing multiple labels with variable content (e.g. name badges, asset tags).

**Variable syntax:** `:varname:` in text, QR, or barcode widget content fields. Variables are auto-detected via regex in `lib/variables.ts` using `detectVariables()`, which runs in components via `useMemo` (derived, not stored).

**`BatchPanel`** is a collapsible `<details>` panel that shows:
- Copies per row and pause time between prints
- An auto-detected variable table based on current widget content
- Editable rows; clicking a row selects it for preview
- Helper text when no variables are detected

**`PrintButton`** switches to batch mode when `batch.enabled` is true: shows "Batch Print (N labels)", streams progress from the server, and offers a cancel button during printing.

### Type Definitions

All shared types live in `types/label.ts`:

- `TextWidget` -- text, fontStyle, fontScale, frameWidthPx, align
- `QrWidget` -- content
- `BarcodeWidget` -- content, barcodeType, showText
- `ImageWidget` -- filename (server-side reference from upload)
- `LabelSettings` -- tapeSizeMm, marginPx, minLengthMm, justify, foregroundColor, backgroundColor, showMargins
- `BatchState` -- enabled, copies, pauseTime, rows (variable value maps), selectedRowIndex
- Union type `LabelWidget = TextWidget | QrWidget | BarcodeWidget | ImageWidget`

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

POST /api/batch-print (SSE streaming)
  -> app.py (api_batch_print)
    -> For each row × copies:
      -> _substitute_widgets(widgets, row)  # Replace :varname: placeholders
      -> label_builder.print_label(...)     # Print one label
      -> SSE event: printing/printed
    -> Check cancellation flag between prints (during pause sleep)
  <- SSE events: started, printing, printed, done/cancelled/error

POST /api/batch-print/cancel
  -> Sets cancelled flag for the running job
  <- { status: "ok" }
```

### Label Builder (`label_builder.py`)

Converts the widget JSON array into labelle `RenderEngine` instances:

- **Text widgets** → `TextRenderEngine` with per-widget `font_file_name`, `font_size_ratio`, `frame_width_px`, and `align`. Each text widget gets its own font style via `get_font_path(style=...)`.
- **QR widgets** → `QrRenderEngine(content)`
- **Barcode widgets** → `BarcodeRenderEngine(content, barcode_type)` or `BarcodeWithTextRenderEngine(content, font_file_name, barcode_type)` when `showText` is true.
- **Image widgets** → `PictureRenderEngine(picture_path)` where the path is resolved from the uploaded filename.

All engines are combined with `HorizontallyCombinedRenderEngine`, then wrapped with either `PrintPayloadRenderEngine` (for printing) or `PrintPreviewRenderEngine` (for preview).

Settings like `marginPx`, `minLengthMm`, `justify`, `tapeSizeMm`, `foregroundColor`, and `backgroundColor` are applied via `RenderContext` and the payload/preview wrapper.

### Flask App (`app.py`)

- `POST /api/print` — validates request, calls `print_label()`, returns JSON status
- `POST /api/preview` — validates request, calls `preview_label()`, returns PNG bytes
- `POST /api/batch-print` — SSE streaming endpoint: substitutes variables per row, prints each label, streams progress events. Only one batch job can run at a time (409 if another is active). Cancellation checked between prints during pause sleep.
- `POST /api/batch-print/cancel` — sets cancelled flag for a running batch job by jobId
- `POST /api/upload-image` — accepts multipart file upload, saves with UUID filename, returns `{ filename }`
- `GET /api/uploads/<filename>` — serves uploaded images (used by the editor thumbnail)
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
