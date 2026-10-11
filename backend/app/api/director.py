"""director 蓝图：8-block组装+锁注入（纯文本，不直连生成）。
skill归属：8-block/风格头/Vague ban归 illustration-prompt；机位归 composition-camera；
锁面逐字注入归 short-drama-storyboard；本文件只做字符串拼接+校验。
"""
from flask import Blueprint, request, jsonify
import re

bp = Blueprint("director", __name__, url_prefix="/api/v1/director")

VAGUE_BAN = ["cinematic", "epic", "stunning", "spectacular", "perfect", "premium", "8k", "high quality", "texture-rich"]

def ok(data):
    return jsonify({"code": 0, "data": data})

def _clean(text):
    for w in VAGUE_BAN:
        text = re.sub(r"\b" + re.escape(w) + r"\b", "", text, flags=re.I)
    return " ".join(text.split())

def build_prompt(shot, character=None, locks=None, style_bible=""):
    character = character or {}
    locks = locks or []
    style = style_bible or "high-quality 2D anime illustration, anime key visual, cel-shaded"
    subject = f"1girl, solo, {character.get('identity', 'young woman')}"
    appearance = f"{character.get('hairstyle', '')} {character.get('face', '')}".strip() or "black long straight hair, dark eyes"
    outfit = (character.get("outfits_text") or "school uniform with red bow")[:120]
    pose = shot.get("duty", "standing").replace("[规则拆]", "").replace("[AI拆]", "")[:60] or "standing"
    scene = shot.get("scene_text") or "classroom interior, desks and windows"
    cam = shot.get("camera") or {}
    camera = f"{cam.get('crop', 'medium')} shot, {cam.get('height', 'eye')}-level, straight-on zero tilt"
    light = "soft key light from upper left, warm 3200K, muted indigo and amber palette"
    lock_txt = ", ".join([l.get("surface_en", "") for l in locks if l.get("surface_en")])[:200]
    parts = [style, subject, appearance, outfit, pose, scene, camera, light]
    if lock_txt:
        parts.insert(3, lock_txt)
    parts.append("score_9, masterpiece, best quality, sharp lineart")
    en = _clean(", ".join([p for p in parts if p]))[:900]
    locks_hit = [l.get("id") for l in locks if l.get("surface_en") and l["surface_en"].lower() in en.lower()]
    return {"assembled_en": en, "locks_hit": locks_hit}

@bp.post("/prompts/assemble")
def assemble():
    b = request.get_json(force=True) or {}
    shots = b.get("shots", [])
    style = b.get("style_bible", "")
    character = b.get("character") or {}
    locks = b.get("locks") or []
    # 兼容：shots 可能是 id 字符串，也可能是 shot 对象
    out = []
    for s in shots:
        shot = s if isinstance(s, dict) else {"id": s, "duty": s, "camera": {}}
        sid = shot.get("id", s)
        r = build_prompt(shot, character, locks, style)
        out.append({"shot_id": sid, **r, "unresolved_refs": []})
    return ok({"prompts": out, "tip": "复制到 ComfyUI/MJ/即梦/可灵手工生产，本系统不直连生成"})

@bp.post("/prompts/assemble-episode/<eid>")
def assemble_episode(eid):
    """按集组装：从 scriptboard 取 shots，character 取首角色。"""
    from ..api.scriptboard import _SHOTS
    from ..api.character import _CHARS
    b = request.get_json(force=True) or {}
    style = b.get("style_bible", "")
    locks = b.get("locks") or []
    chars = list(_CHARS.values())
    character = chars[0] if chars else {}
    rows = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    out = []
    for shot in sorted(rows, key=lambda x: x.get("id", "")):
        r = build_prompt(shot, character, locks, style)
        out.append({"shot_id": shot.get("id"), **r, "unresolved_refs": []})
    return ok({"episode_id": eid, "count": len(out), "prompts": out})

@bp.get("/export")
def export():
    """去程交付包（对齐 POSITIONING §2）：package_id + shots + locks + review。"""
    import time as _time
    from ..api.scriptboard import _SHOTS, _EPS
    from ..api.character import _CHARS
    eid = request.args.get("episode_id", "")
    style = request.args.get("style_bible", "")
    ep = _EPS.get(eid, {})
    chars = list(_CHARS.values())
    character = chars[0] if chars else {}
    rows = sorted([s for s in _SHOTS.values() if not eid or s.get("episode_id") == eid],
                  key=lambda x: x.get("id", ""))
    shots = []
    for shot in rows:
        r = build_prompt(shot, character, [], style)
        shots.append({"id": shot.get("id"), "assembled_en": r["assembled_en"],
                      "locks_hit": r["locks_hit"], "visual_basis": [],
                      "camera": shot.get("camera", {}),
                      "boundaries": {"start": shot.get("start_boundary", {}),
                                     "end": shot.get("end_boundary", {})}})
    pkg = {
        "package_id": f"PKG-{eid or 'NA'}-{int(_time.time())}",
        "episode_id": eid, "verdict": ep.get("verdict", "draft"),
        "shots": shots, "locks": [],
        "review": {"verdict": ep.get("verdict", "draft"), "findings": []},
    }
    return ok(pkg)
