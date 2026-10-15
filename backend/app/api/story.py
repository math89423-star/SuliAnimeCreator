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


@bp.post("/screenplay/generate")
def screenplay_generate():
    """精品剧本正文：pick/idea -> 规范 screenplay_md（LLM优先，模板回退，不抛500）。"""
    from ..services.draft import build_screenplay_md
    b = request.get_json(force=True, silent=True) or {}
    idea = (b.get("idea") or "").strip()[:500]
    pick = b.get("pick") or {}
    logline = str(pick.get("logline") or b.get("logline") or "").strip()[:200]
    beats = pick.get("beats") or b.get("beats") or []
    try:
        target_s = max(10, min(90, int(b.get("target_s") or b.get("total_s") or 30)))
    except (ValueError, TypeError):
        target_s = 30
    episode_id = (b.get("episode_id") or "").strip() or "EP-DEMO01"
    md, engine = build_screenplay_md(idea, logline or idea, beats, target_s, episode_id)
    return ok({"screenplay_md": md, "engine": engine, "chars": len(md),
               "episode_id": episode_id, "tip": "确认后调 confirm-to-episode 落底稿"})


@bp.post("/confirm-to-episode")
def confirm_to_episode():
    """Story确认一键落底稿：confirmed + scriptboard.screenplay_md（仅空盘写入，不覆盖人工稿）。"""
    from ..services.draft import pick_to_screenplay_md
    from ..services.disk_store import load as _load, save as _save
    b = request.get_json(force=True, silent=True) or {}
    pick = b.get("pick") or {}
    episode_id = (b.get("episode_id") or "").strip() or "EP-DEMO01"
    _STORE.setdefault("confirmed", []).append(pick)
    _persist()
    doc = _load("scriptboard_db.json", {"eps": {}, "shots": {}})
    eps = doc.get("eps", {})
    ep = eps.setdefault(episode_id, {"id": episode_id, "screenplay_md": "", "segs": [], "verdict": "draft"})
    wrote = False
    if not (ep.get("screenplay_md") or "").strip():
        ep["screenplay_md"] = pick_to_screenplay_md(pick, episode_id)
        ep["segs"] = []
        wrote = True
    _save("scriptboard_db.json", doc)
    # 同步内存镜像（scriptboard 蓝图持有 _EPS 引用时尽力同步）
    try:
        from ..api.scriptboard import _EPS as _SB_EPS
        if episode_id in _SB_EPS and not (_SB_EPS[episode_id].get("screenplay_md") or "").strip():
            _SB_EPS[episode_id]["screenplay_md"] = ep["screenplay_md"]
            _SB_EPS[episode_id]["segs"] = []
    except Exception:
        pass
    return ok({"confirmed": pick, "total": len(_STORE["confirmed"]),
               "episode_id": episode_id, "screenplay_wrote": wrote,
               "screenplay_chars": len(ep.get("screenplay_md", ""))})

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
