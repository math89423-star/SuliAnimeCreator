"""human-in-loop 最小链：suggest 只给草稿，confirm 才写库。落盘 data/story_db.json。"""
from flask import Blueprint, request, jsonify
from ..services.disk_store import load, save

bp = Blueprint("story", __name__, url_prefix="/api/v1/story")

_STORE = load("story_db.json", {"drafts": [], "confirmed": []})

def _persist():
    save("story_db.json", _STORE)

def ok(data):
    return jsonify({"code": 0, "data": data})

@bp.post("/suggest")
def suggest():
    b = request.get_json(force=True)
    idea = (b or {}).get("idea", "")
    drafts = [
        {"dir": "A", "logline": f"{idea}：隐喻替换版", "beats": ["起", "转", "落"]},
        {"dir": "B", "logline": f"{idea}：时空平移版", "beats": ["起", "转", "落"]},
        {"dir": "C", "logline": f"{idea}：视角反转版", "beats": ["起", "转", "落"]},
    ]
    _STORE["drafts"] = drafts
    _persist()
    return ok({"drafts": drafts, "tip": "confirm后才落库"})

@bp.post("/confirm")
def confirm():
    b = request.get_json(force=True)
    pick = (b or {}).get("pick", {})
    _STORE.setdefault("confirmed", []).append(pick)
    _persist()
    return ok({"confirmed": pick, "total": len(_STORE["confirmed"])})

@bp.get("/list")
def list_all():
    return ok(_STORE)
