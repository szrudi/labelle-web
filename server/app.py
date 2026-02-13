import os
import tempfile
import traceback
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from label_builder import preview_label, print_label

app = Flask(__name__, static_folder=None)
CORS(app)

DIST_DIR = os.path.join(os.path.dirname(__file__), "dist-client")
UPLOAD_DIR = tempfile.mkdtemp(prefix="labelle-uploads-")


@app.route("/api/print", methods=["POST"])
def api_print():
    data = request.get_json(silent=True) or {}
    widgets = data.get("widgets")
    settings = data.get("settings", {})

    if not widgets or not isinstance(widgets, list) or len(widgets) == 0:
        return jsonify(status="error", message="No widgets provided"), 400

    try:
        print_label(widgets, settings, upload_dir=UPLOAD_DIR)
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
    port = int(os.environ.get("PORT", 5000))
    print(f"Labelle server running at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
