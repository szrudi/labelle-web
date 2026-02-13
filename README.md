# Labelle Web

A web interface for [labelle](https://github.com/labelle-org/labelle) DYMO label printers. Compose labels with text, QR codes, and barcodes in your browser, with a live server-side preview and one-click printing.

Built as a modern replacement for the original PyQt6 desktop GUI, designed to run on a headless server (e.g. Raspberry Pi) and be accessed from any device on the network.

## Features

- **Text widgets** -- multiline text with font style (regular/bold/italic/narrow), scale, frame border, and alignment
- **QR code widgets** -- encode any text or URL
- **Barcode widgets** -- CODE128, CODE39, EAN13, EAN8, UPC, ITF, and more, with optional human-readable text
- **Pixel-perfect preview** -- live server-side rendering via labelle's own render engines, so what you see is exactly what prints
- **Label settings** -- tape size, margins, minimum length, justify, foreground/background colors
- **Per-widget font styles** -- each text widget can have its own font style, scale, frame, and alignment
- **Print via labelle** -- sends labels to the printer using the labelle Python library over USB

## Prerequisites

- **Docker** (recommended) or **Node.js** >= 18 (for client build) + **Python** >= 3.10 with **labelle** installed
- A supported DYMO label printer connected via USB (for printing)

## Quick Start (Docker)

The easiest way to run Labelle Web, and the recommended approach for [Komodo](https://komo.do/) or any Docker-based deployment.

```bash
docker compose up -d
```

The app will be available at `http://<host>:5000`.

The container includes Python and the labelle library -- no host-level Python installation needed. USB passthrough is configured in `compose.yaml` so the container can talk to your DYMO printer.

### Komodo

To deploy with Komodo, point a **Stack** at this repository. Komodo will pick up the `compose.yaml` automatically. Make sure the host machine has the DYMO printer connected via USB.

### Building the image manually

```bash
docker build -t labelle-web .
docker run -d -p 5000:5000 --privileged -v /dev/bus/usb:/dev/bus/usb labelle-web
```

## Quick Start (bare metal)

If you prefer to run without Docker, you need Node.js >= 18 (for building the client) and Python >= 3.10 with [labelle](https://github.com/labelle-org/labelle#installation) installed.

```bash
# Install dependencies
npm install
pip install -r server/requirements.txt

# Development (Vite dev server + Flask with hot reload)
npm run dev

# Production build
npm run build

# Start production server
npm start
```

In development, the Vite dev server runs on `http://localhost:5173` and proxies API requests to the Flask backend on port 5000.

In production, Flask serves both the API and the built client on port 5000.

## Project Structure

```
labelle-web/
  client/                   # Vite + React + TypeScript frontend
    src/
      components/           # React UI components
      lib/                  # API client, constants
      state/                # Zustand store
      types/                # TypeScript type definitions
  server/                   # Python/Flask backend
    app.py                  # Flask application with routes and static serving
    label_builder.py        # Converts widget JSON to labelle render engines
    requirements.txt        # Python dependencies
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## Configuration

| Environment Variable | Default    | Description                          |
|---------------------|------------|--------------------------------------|
| `PORT`              | `5000`     | Server listen port                   |

## API Endpoints

### `POST /api/print`

Print a label to the connected DYMO printer.

**Request body:**
```json
{
  "widgets": [
    { "type": "text", "text": "Hello\nWorld", "fontStyle": "bold", "fontScale": 90, "frameWidthPx": 0, "align": "center" },
    { "type": "qr", "content": "https://example.com" },
    { "type": "barcode", "content": "12345", "barcodeType": "code128", "showText": true }
  ],
  "settings": {
    "tapeSizeMm": 12,
    "marginPx": 56,
    "minLengthMm": 0,
    "justify": "center"
  }
}
```

**Response:** `{ "status": "success", "message": "Label sent to printer." }`

### `POST /api/preview`

Generate a server-side PNG preview using labelle's render engines.

Same request body as `/api/print`. Returns `image/png`.

## Known Limitations

- **No image widget**: The desktop GUI supports image widgets; the web version does not (file upload from browser to server would require additional handling).

## License

This project wraps the [labelle](https://github.com/labelle-org/labelle) CLI. Labelle is not affiliated with DYMO. See labelle's license and disclaimers for details.
