"""receipts 蓝图：执行回执登记（只存事实，不触发重生成）。落盘 backend/data/receipts_db.json。
回执字段由我方定（A向裁定），l-port 按此交回执。"""
from flask import Blueprint, request, jsonify
import time
from ..services.disk_store import load, save

bp = Blueprint("receipts", __name__, url_prefix="/api/v1/receipts")

_STORE = load("receipts_db.json", {"items": []})

def _persist():
    save("receipts_db.json", _STORE)

def ok(data):
    return jsonify({"code": 0, "data": data})

REQUIRED = ["package_id", "shot_id", "task_id", "engine", "status"]

@bp.get("")
def list_all():
    package_id = request.args.get("package_id", "")
    rows = _STORE.get("items", [])
    if package_id:
        rows = [r for r in rows if r.get("package_id") == package_id]
    return ok(sorted(rows, key=lambda r: r.get("created_at", 0), reverse=True))

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    missing = [k for k in REQUIRED if not b.get(k)]
    if missing:
        return jsonify({"code": 4001, "msg": "缺字段: " + ",".join(missing)}), 400
    row = {
        "package_id": b["package_id"], "shot_id": b["shot_id"],
        "task_id": b["task_id"], "engine": b["engine"],
        "provider": b.get("provider", ""), "media_url": b.get("media_url", ""),
        "status": b["status"], "log_tail": (b.get("log_tail") or "")[:2000],
        "deviations": b.get("deviations") or [],
        "created_at": int(time.time() * 1000),
    }
    _STORE.setdefault("items", []).append(row)
    _persist()
    return ok(row)
