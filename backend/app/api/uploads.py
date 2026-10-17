"""uploads 蓝图：真落盘 data/uploads。"""
from flask import Blueprint, request, jsonify, send_from_directory
from pathlib import Path
import os
import urllib.parse
import uuid

bp = Blueprint("uploads", __name__, url_prefix="/api/v1")
ROOT = Path(__file__).resolve().parents[2] / "data" / "uploads"
ROOT.mkdir(parents=True, exist_ok=True)

# 上传上限：视频参考 300MB（与 video-frames 抽帧上限对齐），图片/文件同样受帽，防爆盘
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(300 * 1024 * 1024)))
_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def ok(data):
    return jsonify({"code": 0, "data": data})


def _kind_of(filename, mimetype):
    ext = Path(filename or "").suffix.lower()
    mt = (mimetype or "").lower()
    if ext in _VIDEO_EXTS or mt.startswith("video/"):
        return "video"
    if ext in _IMAGE_EXTS or mt.startswith("image/"):
        return "image"
    return "file"

@bp.post("/uploads")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    ext = Path(f.filename or "").suffix[:10] or ".bin"
    name = uuid.uuid4().hex + ext
    p = ROOT / name
    try:
        size = 0
        with open(p, "wb") as out:
            while True:
                chunk = f.stream.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise ValueError("文件超过 %dMB 上限" % (MAX_UPLOAD_BYTES // 1024 // 1024))
                out.write(chunk)
        if size == 0:
            raise ValueError("空文件")
    except Exception as e:
        try:
            p.unlink()
        except Exception:
            pass
        return jsonify({"code": 4001, "msg": str(e)[:200]}), 400
    kind = _kind_of(f.filename, f.mimetype)
    return ok({"path": name, "url": f"/api/images/{name}", "kind": kind, "bytes": size})

@bp.get("/images/<name>")
def serve(name):
    return send_from_directory(ROOT, name)


# ---- 素材源（拉片室）：uploads 里的视频素材列表 / 删除 ----

@bp.get("/uploads/media")
def media_list():
    """拉片室「素材源」：列 uploads 里的视频素材（mtime 倒序）。"""
    items = []
    for p in ROOT.iterdir():
        try:
            if not p.is_file() or p.suffix.lower() not in _VIDEO_EXTS:
                continue
            st = p.stat()
        except OSError:
            continue
        items.append({"name": p.name, "url": f"/api/images/{urllib.parse.quote(p.name)}",
                      "bytes": st.st_size, "mtime": int(st.st_mtime)})
    items.sort(key=lambda x: -x["mtime"])
    return ok(items)


@bp.delete("/uploads/media/<name>")
def media_delete(name):
    """删 uploads 里的视频素材（只认视频扩展名，防误删/路径穿越）。"""
    nm = Path(name or "").name
    p = ROOT / nm
    if not nm or p.suffix.lower() not in _VIDEO_EXTS or not p.is_file():
        return jsonify({"code": 4004, "msg": "没有这个视频素材"}), 404
    try:
        p.unlink()
    except Exception as e:
        return jsonify({"code": 5001, "msg": "删除失败：%s" % str(e)[:120]}), 500
    return ok({"deleted": nm})
