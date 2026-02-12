# Architecture

## Overview

Labelle Web is a monorepo with two npm workspaces:

```
labelle-web/
  package.json              # Root: workspaces, concurrently for dev
  client/                   # Frontend: Vite + React + TypeScript + Tailwind
  server/                   # Backend: Express + TypeScript
```

The frontend handles all UI and provides instant canvas-based label preview. The backend is a thin wrapper that translates widget data into labelle CLI batch-mode invocations.

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

- **Express** with TypeScript
- **tsx** for development (watch mode with hot reload)
- **tsc** for production builds

### Request Flow

```
POST /api/print
  -> routes/print.ts
    -> batchBuilder.buildBatchInput(widgets)    # Widgets -> batch stdin
    -> argBuilder.buildArgs(settings, style)    # Settings -> CLI args
    -> labelleRunner.runLabelle(args, stdin)    # Spawn process
  <- { status, message }
```

### Batch Builder (`lib/batchBuilder.ts`)

Converts the widget array into labelle's batch-mode stdin format:

```
LABELLE-LABEL-SPEC-VERSION:1
TEXT:First line
NEWLINE:Second line
QR:https://example.com
BARCODE#code128:12345
```

- `TEXT:` starts a new text block
- `NEWLINE:` adds lines to the current block
- `QR:` creates a QR code
- `BARCODE#type:` creates a barcode with the specified encoding

### Arg Builder (`lib/argBuilder.ts`)

Maps settings to CLI arguments:

| Setting | CLI Arg |
|---------|---------|
| tapeSizeMm | `--tape-size-mm` |
| marginPx | `--margin-px` |
| minLengthMm | `--min-length` |
| justify | `--justify` |
| fontStyle | `--style` |
| fontScale | `--font-scale` |
| frameWidthPx | `--frame-width-px` |
| align | `--align` |

The `--batch` flag is always included. For the preview endpoint, `--output png` is appended.

**Global style limitation**: The CLI only supports one set of style arguments globally. When multiple text widgets exist with different styles, only the first text widget's style (`--style`, `--font-scale`, `--frame-width-px`, `--align`) is sent.

### Labelle Runner (`lib/labelleRunner.ts`)

Spawns the labelle CLI as a child process, pipes batch data to stdin, and collects stdout/stderr. The executable path defaults to `labelle` but can be overridden with the `LABELLE_PATH` environment variable.

## Build and Deployment

### Development

`npm run dev` uses `concurrently` to start:
- Vite dev server on port 5173 (with HMR)
- Express dev server on port 5000 (with `tsx watch` for auto-restart)

Vite proxies `/api/*` requests to the Express backend.

### Production

`npm run build` runs:
1. `tsc -b` in `client/` (type checking)
2. `vite build` in `client/` (outputs to `server/dist-client/`)
3. `tsc` in `server/` (compiles to `server/dist/`)

`npm start` runs the compiled Express server, which serves both the static client bundle and the API on a single port.

### Deployment Diagram

```
Browser (any device on LAN)
    |
    | HTTP :5000
    v
Express Server (e.g. Raspberry Pi)
    |
    | spawns process, pipes stdin
    v
labelle CLI
    |
    | USB
    v
DYMO Label Printer
```
