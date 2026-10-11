"""projects 蓝图：顶栏项目切换。落盘 backend/data/projects_db.json。"""
from flask import Blueprint, request, jsonify
import uuid
from ..services.disk_store import load, save

bp = Blueprint("projects", __name__, url_prefix="/api/v1/projects")

_STORE = load("projects_db.json", {"items": []})

def _persist():
    save("projects_db.json", _STORE)

def ok(data):
    return jsonify({"code": 0, "data": data})

@bp.get("")
def list_all():
    return ok(_STORE.get("items", []))

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    row = {"id": "PRJ-" + uuid.uuid4().hex[:6].upper(), "name": b.get("name", "新项目")}
    _STORE.setdefault("items", []).append(row)
    _persist()
    return ok(row)

@bp.put("/<pid>")
def rename(pid):
    b = request.get_json(force=True) or {}
    for r in _STORE.get("items", []):
        if r["id"] == pid:
            r["name"] = b.get("name", r["name"])
    _persist()
    return ok({"id": pid, "name": b.get("name", "")})
