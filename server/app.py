import copy
import json
import os
import re
import tempfile
import threading
import time
import traceback
import uuid

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from label_builder import preview_label, print_label

app = Flask(__name__, static_folder=None)
CORS(app)

DIST_DIR = os.path.join(os.path.dirname(__file__), "dist-client")
UPLOAD_DIR = tempfile.mkdtemp(prefix="labelle-uploads-")

# Batch job tracking
_batch_jobs: dict[str, dict] = {}
_batch_lock = threading.Lock()


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


def _substitute_widgets(widgets, values):
    """Replace :varname: placeholders in widget text/content fields."""
    result = copy.deepcopy(widgets)
    pattern = re.compile(r":([a-zA-Z_]\w*):")
    for widget in result:
        for field in ("text", "content"):
            if field in widget and isinstance(widget[field], str):
                widget[field] = pattern.sub(
                    lambda m: values.get(m.group(1), m.group(0)), widget[field]
                )
    return result


@app.route("/api/batch-print", methods=["POST"])
def api_batch_print():
    data = request.get_json(silent=True) or {}
    widgets = data.get("widgets")
    settings = data.get("settings", {})
    rows = data.get("rows", [])
    copies = max(1, int(data.get("copies", 1)))
    pause_time = max(0.0, float(data.get("pauseTime", 0)))

    if not widgets or not isinstance(widgets, list) or len(widgets) == 0:
        return jsonify(status="error", message="No widgets provided"), 400
    if not rows or not isinstance(rows, list):
        return jsonify(status="error", message="No rows provided"), 400

    # Check for existing running batch job
    with _batch_lock:
        running = [j for j in _batch_jobs.values() if not j.get("done")]
        if running:
            return jsonify(status="error", message="Another batch job is already running"), 409

        job_id = uuid.uuid4().hex
        _batch_jobs[job_id] = {"cancelled": False, "done": False}

    # Build print list: each row × copies
    print_list = []
    for row in rows:
        for _ in range(copies):
            print_list.append(row)

    total = len(print_list)

    def generate():
        try:
            yield f"data: {json.dumps({'event': 'started', 'jobId': job_id, 'total': total})}\n\n"

            for idx, row_values in enumerate(print_list):
                job = _batch_jobs.get(job_id, {})
                if job.get("cancelled"):
                    yield f"data: {json.dumps({'event': 'cancelled', 'printed': idx})}\n\n"
                    return

                yield f"data: {json.dumps({'event': 'printing', 'index': idx, 'total': total})}\n\n"

                substituted = _substitute_widgets(widgets, row_values)
                try:
                    print_label(substituted, settings, upload_dir=UPLOAD_DIR)
                except Exception as e:
                    traceback.print_exc()
                    yield f"data: {json.dumps({'event': 'error', 'index': idx, 'message': str(e)})}\n\n"
                    return

                yield f"data: {json.dumps({'event': 'printed', 'index': idx, 'total': total})}\n\n"

                # Pause between prints (except after last)
                if pause_time > 0 and idx < total - 1:
                    elapsed = 0.0
                    while elapsed < pause_time:
                        if _batch_jobs.get(job_id, {}).get("cancelled"):
                            yield f"data: {json.dumps({'event': 'cancelled', 'printed': idx + 1})}\n\n"
                            return
                        time.sleep(min(0.1, pause_time - elapsed))
                        elapsed += 0.1

            yield f"data: {json.dumps({'event': 'done', 'total': total})}\n\n"
        finally:
            with _batch_lock:
                if job_id in _batch_jobs:
                    _batch_jobs[job_id]["done"] = True

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/batch-print/cancel", methods=["POST"])
def api_batch_cancel():
    data = request.get_json(silent=True) or {}
    job_id = data.get("jobId", "")

    with _batch_lock:
        job = _batch_jobs.get(job_id)
        if not job:
            return jsonify(status="error", message="Job not found"), 404
        job["cancelled"] = True

    return jsonify(status="ok")


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
