"""human-in-loop 最小链：suggest/expand 只给草稿，confirm 才写库。落盘 data/story_db.json。
expand 走 services/draft，不走 dsh；suggest 保留模板。
正文/底稿的说话人一律经 services/cast 解析（点名 → 集内正文 → 角色库 → 占位）。"""
from flask import Blueprint, request, jsonify
from ..services.disk_store import load, save
from ..services import cast as cast_svc
import uuid

bp = Blueprint("story", __name__, url_prefix="/api/v1/story")

_STORE = load("story_db.json", {"drafts": [], "confirmed": []})


def _persist():
    save("story_db.json", _STORE)


def ok(data):
    return jsonify({"code": 0, "data": data})


def _new_story_id():
    return "STORY-" + uuid.uuid4().hex[:6].upper()


def _ensure_pick_id(pick):
    if not isinstance(pick, dict):
        return {"id": _new_story_id()}
    if not str(pick.get("id") or "").strip():
        pick["id"] = _new_story_id()
    return pick


def _match_confirmed_index(rows, key):
    k = str(key or "").strip()
    if not k:
        return -1
    for i, r in enumerate(rows or []):
        if isinstance(r, dict) and str(r.get("id") or "") == k:
            return i
    try:
        idx = int(k)
        if 0 <= idx < len(rows or []):
            return idx
    except (ValueError, TypeError):
        pass
    for i, r in enumerate(rows or []):
        if isinstance(r, dict) and str(r.get("logline") or "") == k:
            return i
    return -1


def _ep_screenplay(eid):
    """本集已定稿正文（取角第 2 顺位用）；读不到就当空。"""
    try:
        from .scriptboard import _EPS
        return (_EPS.get(eid, {}) or {}).get("screenplay_md", "") or ""
    except Exception:
        return ""


def _cast_meta(eid, cast=None, text=""):
    """统一取角 + 落盘记忆：解析结果非占位才写回 ep['cast']，下次生成沿用同一批人。"""
    C = cast_svc.resolve_cast(cast, text or _ep_screenplay(eid), eid)
    if C["anchored"]:
        try:
            from .scriptboard import _EPS, _persist as _sb_persist
            ep = _EPS.setdefault(eid or "EP-DEMO01", {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
            ep["cast"] = [{"id": c["id"], "name": c["name"]} for c in C["cast"]]
            _sb_persist()
        except Exception:
            pass
    return C

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
    pick = _ensure_pick_id(pick)
    _STORE.setdefault("confirmed", []).append(pick)
    _persist()
    return ok({"confirmed": pick, "total": len(_STORE["confirmed"])})


@bp.get("/cast/<eid>")
def cast_view(eid):
    """本集这次生成会用谁：GET 只算不写盘。cast=名字1,名字2 可临时试算。"""
    raw = request.args.get("cast", "")
    names = [n.strip() for n in raw.split(",") if n.strip()]
    C = cast_svc.resolve_cast(names or None, _ep_screenplay(eid), eid)
    return ok({"episode_id": eid, **C})


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
    C = _cast_meta(episode_id, b.get("cast"), idea or logline)
    md, engine = build_screenplay_md(idea, logline or idea, beats, target_s, episode_id,
                                     cast=C["cast"])
    return ok({"screenplay_md": md, "engine": engine, "chars": len(md),
               "episode_id": episode_id, "cast": C["cast"], "cast_source": C["source"],
               "tip": "确认后调 confirm-to-episode 落底稿"})


@bp.post("/confirm-to-episode")
def confirm_to_episode():
    """Story确认一键落底稿：confirmed + scriptboard.screenplay_md（仅空盘写入，不覆盖人工稿）。"""
    from ..services.draft import pick_to_screenplay_md
    from ..services.disk_store import load as _load, save as _save
    b = request.get_json(force=True, silent=True) or {}
    pick = b.get("pick") or {}
    pick = _ensure_pick_id(pick)
    episode_id = (b.get("episode_id") or "").strip() or "EP-DEMO01"
    _STORE.setdefault("confirmed", []).append(pick)
    _persist()
    doc = _load("scriptboard_db.json", {"eps": {}, "shots": {}})
    eps = doc.get("eps", {})
    ep = eps.setdefault(episode_id, {"id": episode_id, "screenplay_md": "", "segs": [], "verdict": "draft"})
    wrote = False
    C = _cast_meta(episode_id, b.get("cast") or pick.get("cast"),
                   pick.get("logline") or "")
    if not (ep.get("screenplay_md") or "").strip():
        ep["screenplay_md"] = pick_to_screenplay_md({**pick, "cast": C["cast"]}, episode_id)
        ep["segs"] = []
        wrote = True
    ep["cast"] = [{"id": c["id"], "name": c["name"]} for c in C["cast"]]
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


@bp.delete("/confirmed/<key>")
def delete_confirmed_one(key):
    rows = _STORE.setdefault("confirmed", [])
    idx = _match_confirmed_index(rows, key)
    if idx < 0:
        return jsonify({"code": 4040, "msg": "已确认方向不存在"}), 404
    removed = rows.pop(idx)
    _persist()
    return ok({"removed": removed, "total": len(rows)})


@bp.delete("/confirmed")
def clear_confirmed():
    n = len(_STORE.get("confirmed", []) or [])
    _STORE["confirmed"] = []
    _persist()
    return ok({"cleared": n, "total": 0})


@bp.delete("/drafts")
def clear_drafts():
    n = len(_STORE.get("drafts", []) or [])
    _STORE["drafts"] = []
    _persist()
    return ok({"cleared": n, "total": 0})
