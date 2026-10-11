"""uploads 蓝图：真落盘 data/uploads。"""
from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import uuid

bp = Blueprint("uploads", __name__, url_prefix="/api/v1")
ROOT = Path(__file__).resolve().parents[2] / "data" / "uploads"
ROOT.mkdir(parents=True, exist_ok=True)

def ok(data):
    return jsonify({"code": 0, "data": data})

@bp.post("/uploads")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    ext = Path(f.filename or "").suffix[:10] or ".bin"
    name = uuid.uuid4().hex + ext
    p = ROOT / name
    f.save(p)
    return ok({"path": name, "url": f"/api/images/{name}", "kind": "image"})

@bp.get("/images/<name>")
def serve(name):
    return send_from_directory(ROOT, name)
