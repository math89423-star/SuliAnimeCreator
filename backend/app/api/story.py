"""human-in-loop 最小链：suggest/expand 只给草稿，confirm 才写库。落盘 data/story_db.json。
轻链（2026-10-13）：expand 走 services/draft，不走 dsh；suggest 保留兼容模板。"""
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

@bp.post("/expand")
def expand():
    """轻发散：不走 dsh，直接调 draft.expand_idea（LLM 优先，模板回退）。"""
    from ..services.draft import expand_idea
    b = request.get_json(force=True) or {}
    idea = (b.get("idea") or "").strip()
    try:
        n = max(2, min(int(b.get("n", 3)), 5))
    except (ValueError, TypeError):
        n = 3
    drafts, engine = expand_idea(idea, n)
    _STORE["drafts"] = drafts
    _persist()
    return ok({"drafts": drafts, "engine": engine, "tip": "confirm后才落库"})

@bp.get("/list")
def list_all():
    return ok(_STORE)
