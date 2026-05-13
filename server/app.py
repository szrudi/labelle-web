import json
import os
import subprocess
import tempfile
import time
import traceback
import uuid

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

import usb_power
from label_builder import preview_label
from printer_service import list_printers, print_label

# Seconds to wait after power-on before reading status, so the device has
# time to re-enumerate on the USB bus.
POWER_ON_SETTLE_SECONDS = 1.5

app = Flask(__name__, static_folder=None)
CORS(app)

DIST_DIR = os.path.join(os.path.dirname(__file__), "dist-client")
UPLOAD_DIR = tempfile.mkdtemp(prefix="labelle-uploads-")


@app.route("/api/print", methods=["POST"])
def api_print():
    data = request.get_json(silent=True) or {}
    widgets = data.get("widgets")
    settings = data.get("settings", {})
    printer_id = settings.get("printerId")  # Optional printer ID from settings

    if not widgets or not isinstance(widgets, list) or len(widgets) == 0:
        return jsonify(status="error", message="No widgets provided"), 400

    try:
        print_label(widgets, settings, upload_dir=UPLOAD_DIR, printer_id=printer_id)
        return jsonify(status="success", message="Label sent to printer.")
    except Exception as e:
        traceback.print_exc()
        return jsonify(status="error", message=str(e)), 500


@app.route("/api/preview", methods=["POST"])
def api_preview():
    data = request.get_json(silent=True) or {}
    widgets = data.get("widgets")
    settings = data.get("settings", {})

    if not widgets or not isinstance(widgets, list) or len(widgets) == 0:
        return jsonify(status="error", message="No widgets provided"), 400

    try:
        png_bytes = preview_label(widgets, settings, upload_dir=UPLOAD_DIR)
        return app.response_class(png_bytes, mimetype="image/png")
    except Exception as e:
        traceback.print_exc()
        return jsonify(status="error", message=str(e)), 500


@app.route("/api/upload-image", methods=["POST"])
def api_upload_image():
    if "file" not in request.files:
        return jsonify(status="error", message="No file provided"), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify(status="error", message="No file selected"), 400

    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Flatten transparency onto white background so labelle's grayscale
    # conversion doesn't turn transparent pixels black.
    from PIL import Image

    img = Image.open(file.stream)
    if img.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.getchannel("A"))
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(filepath, format="PNG")

    return jsonify(filename=filename)


@app.route("/api/uploads/<filename>")
def api_serve_upload(filename):
    filename = secure_filename(filename)
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/api/printers", methods=["GET"])
def api_printers():
    return jsonify(printers=list_printers())


def _printer_port_or_404():
    port = usb_power.find_or_recall_printer_port()
    if port is None:
        return None, (jsonify(status="error", message="Printer not detected"), 404)
    return port, None


@app.route("/api/power/status", methods=["GET"])
def api_power_status():
    port, err = _printer_port_or_404()
    if err:
        return err
    hub, port_num = port
    return jsonify(hub=hub, port=port_num, **usb_power.get_port_status(hub, port_num))


@app.route("/api/power/on", methods=["POST"])
def api_power_on():
    port, err = _printer_port_or_404()
    if err:
        return err
    hub, port_num = port
    try:
        usb_power.power_on(hub, port_num)
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        return jsonify(status="error", message=str(e)), 500
    time.sleep(POWER_ON_SETTLE_SECONDS)
    return jsonify(
        status="success",
        hub=hub,
        port=port_num,
        **usb_power.get_port_status(hub, port_num),
    )


@app.route("/api/power/off", methods=["POST"])
def api_power_off():
    port, err = _printer_port_or_404()
    if err:
        return err
    hub, port_num = port
    try:
        usb_power.power_off(hub, port_num)
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        return jsonify(status="error", message=str(e)), 500
    return jsonify(
        status="success",
        hub=hub,
        port=port_num,
        **usb_power.get_port_status(hub, port_num),
    )


def _build_info() -> dict:
    """Return {commit, branch} from env vars (set at Docker build time) or git."""
    info = {}
    if sha := os.environ.get("GIT_SHA"):
        info["commit"] = sha
    if branch := os.environ.get("GIT_BRANCH"):
        info["branch"] = branch
    if info:
        return info

    repo_root = os.path.join(os.path.dirname(__file__), "..")
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root, stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
        return {"commit": sha, "branch": branch}
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return {}


@app.route("/api/health", methods=["GET"])
def api_health():
    pkg_path = os.path.join(os.path.dirname(__file__), "..", "package.json")
    with open(pkg_path) as f:
        version = json.load(f)["version"]

    return jsonify(status="ok", version=version, **_build_info())


# --- Static file serving for production (SPA fallback) ---


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    # Try to serve the requested file from dist-client
    full_path = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(DIST_DIR, path)
    # SPA fallback: serve index.html for all other routes
    index = os.path.join(DIST_DIR, "index.html")
    if os.path.isfile(index):
        return send_from_directory(DIST_DIR, "index.html")
    return "Client not built. Run 'npm run build' first.", 404


if __name__ == "__main__":
    from waitress import serve

    port = int(os.environ.get("PORT", 5000))
    print(f"Labelle server running at http://0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port)
