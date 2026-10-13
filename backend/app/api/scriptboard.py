"""scriptboard 蓝图：剧本存管 + 自动拆分镜(LLM优先，规则回退) + 结构门。落盘 backend/data/scriptboard_db.json。"""
from flask import Blueprint, request, jsonify
from ..services.disk_store import load, save

bp = Blueprint("scriptboard", __name__, url_prefix="/api/v1/scriptboard")

# 分级只两档：sfw/nsfw（空串=常规镜）。旧四档读到自动归 nsfw。
TIER_KEYS = ("", "sfw", "nsfw")


def _norm_tier(v):
    v = (v or "").strip()
    if v in TIER_KEYS:
        return v
    if v in ("tease", "undress", "explicit", "closeup"):
        return "nsfw"
    return ""

_DB = load("scriptboard_db.json", {"eps": {}, "shots": {}})
_EPS = _DB.get("eps", {})
_SHOTS = _DB.get("shots", {})

def _persist():
    save("scriptboard_db.json", {"eps": _EPS, "shots": _SHOTS})

def ok(data):
    return jsonify({"code": 0, "data": data})

@bp.put("/screenplay/<eid>")
def save_screenplay(eid):
    b = request.get_json(force=True)
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    ep["screenplay_md"] = b.get("screenplay_md", "")
    ep["segs"] = []
    _persist()
    return ok({"episode_id": eid, "chars": len(ep["screenplay_md"])})

@bp.get("/screenplay/<eid>")
def get_screenplay(eid):
    """取本集剧本底稿（分镜页刷新回填用）。"""
    ep = _EPS.get(eid, {})
    return ok({"episode_id": eid, "screenplay_md": ep.get("screenplay_md", ""),
               "ref_images": ep.get("ref_images", [])})

@bp.post("/episode/<eid>/image")
def upload_episode_image(eid):
    """剧本参考图：落盘 data/uploads，记到本集 ref_images。取图走 /api/images/<name>。"""
    from pathlib import Path
    import uuid as _uuid
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    role = _norm_ref_role(request.form.get("role"))
    desc = _norm_ref_desc(request.form.get("desc"))
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    name = _uuid.uuid4().hex + (Path(f.filename or "").suffix[:10] or ".png")
    f.save(root / name)
    imgs = list(ep.get("ref_images") or [])
    imgs.append({"name": name, "role": role, "desc": desc})
    ep["ref_images"] = imgs
    _persist()
    return ok({"images": imgs, "url": f"/api/images/{name}"})

@bp.delete("/episode/<eid>/image/<name>")
def delete_episode_image(eid, name):
    """删剧本参考图挂载（文件留盘，只去登记）。"""
    ep = _EPS.get(eid, {})
    ep["ref_images"] = [x for x in (ep.get("ref_images") or []) if x.get("name") != name]
    _persist()
    return ok({"images": ep["ref_images"], "deleted": name})

@bp.get("/outline/<eid>")
def get_outline(eid):
    """取本集方案大纲（Agent 出大纲的落点，P0 包的 outline.md 来源）。"""
    ep = _EPS.get(eid, {})
    return ok({"episode_id": eid, "outline_md": ep.get("outline_md", ""),
               "outline_image": ep.get("outline_image", "")})

@bp.put("/outline/<eid>")
def save_outline(eid):
    b = request.get_json(force=True) or {}
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    if "outline_md" in b:
        ep["outline_md"] = b.get("outline_md", "")
    if "outline_image" in b:
        from pathlib import Path as _P
        ep["outline_image"] = _P(b.get("outline_image") or "").name
    _persist()
    return ok({"episode_id": eid, "chars": len(ep.get("outline_md", ""))})

@bp.post("/outline/generate/<eid>")
def outline_generate(eid):
    """轻大纲：不走 dsh，直接调 services/draft（LLM 优先，模板回退）并落盘。"""
    from ..services.draft import build_outline_md
    from pathlib import Path as _P
    b = request.get_json(force=True) or {}
    total_s = int(b.get("total_s") or 15)
    engine = (b.get("engine") or "pixai").strip() or "pixai"
    tier = _norm_tier(b.get("tier"))
    hint = (b.get("hint") or b.get("screenplay_md") or "").strip()[:800]
    image = _P(b.get("image") or b.get("outline_image") or "").name
    md, tag = build_outline_md(eid, total_s, engine, tier, hint, image)
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    ep["outline_md"] = md
    if image:
        ep["outline_image"] = image
    _persist()
    return ok({"episode_id": eid, "outline_md": md, "outline_image": ep.get("outline_image", ""),
               "engine": tag, "chars": len(md)})

@bp.post("/draft/from-outline/<eid>")
def draft_from_outline(eid):
    """轻转草案：读已存 outline_md，按表拆成 draft:true 分镜并挂首帧。不走 dsh。"""
    from ..services.draft import split_outline_to_shots
    from pathlib import Path as _P
    b = request.get_json(force=True) or {}
    total_s = int(b.get("total_s") or 15)
    tier = _norm_tier(b.get("tier"))
    ep = _EPS.get(eid, {})
    outline_md = (b.get("outline_md") or ep.get("outline_md") or "").strip()
    if not outline_md:
        return jsonify({"code": 4001, "msg": "本集暂无大纲，先生成大纲"}), 400
    specs, tag = split_outline_to_shots(outline_md, eid, total_s, tier or "")
    own = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    n = 1
    used = {s.get("id", "") for s in own}
    top = max([s.get("ord", 0) for s in own] + [-1]) + 1
    created = []
    for spec in specs:
        while True:
            sid = f"SHOT-{eid[-4:]}-M{n:03d}"
            if sid not in used and sid not in _SHOTS:
                break
            n += 1
        cam = spec.get("camera") if isinstance(spec.get("camera"), dict) else {}
        row = {"id": sid, "episode_id": eid, "ord": top,
               "duty": spec.get("duty", ""), "duty_en": spec.get("duty_en", ""),
               "duration_s": spec.get("duration_s", 3),
               "camera": {"crop": cam.get("crop", "medium"), "height": "eye",
                          "movement": cam.get("movement", "固定")},
               "sound": spec.get("sound", ""), "key_text_en": spec.get("duty_en", ""),
               "tier": _norm_tier(spec.get("tier")), "draft": True}
        _SHOTS[sid] = row
        used.add(sid)
        created.append(sid)
        top += 1
        n += 1
    # 首镜挂大纲配图为首帧（文件必须已在 uploads）
    first_image = _P(ep.get("outline_image") or b.get("image") or "").name
    attached = ""
    if first_image and created:
        from pathlib import Path as _PP
        root = _PP(__file__).resolve().parents[2] / "data" / "uploads"
        if (root / first_image).is_file():
            s0 = _SHOTS.get(created[0], {})
            imgs = list(s0.get("images") or [])
            imgs = [x for x in imgs if x.get("kind") != "first"]
            imgs.append({"name": first_image, "kind": "first"})
            s0["images"] = imgs
            s0["image"] = ""
            attached = created[0]
    _persist()
    return ok({"episode_id": eid, "created": created, "engine": tag,
               "attached_first": attached})

@bp.post("/auto-split/<eid>")
def auto_split(eid):
    from ..services.llm import heuristic_cuts, llm_cuts
    b = request.get_json(force=True) or {}
    max_cuts = int(b.get("max_cuts_per_seg", 3))
    use_llm = bool(b.get("use_llm", True))
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    text = b.get("story_md") or ep.get("screenplay_md", "") or "无剧本占位"
    paras = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
    created = []
    engine_set = set()
    for i, p in enumerate(paras[:6], 1):
        try:
            if use_llm:
                cuts = llm_cuts(p)[:max_cuts]
                eng = "llm"
            else:
                raise ValueError("skip llm")
        except Exception:
            cuts = heuristic_cuts(p, max_cuts)
            eng = "heuristic"
        engine_set.add(eng)
        prefix = "[AI拆]" if eng == "llm" else "[规则拆]"
        for j, c in enumerate(cuts, 1):
            sid = f"SHOT-{eid[-4:]}-{i:03d}-{j}"
            _SHOTS[sid] = {"id": sid, "episode_id": eid,
                           "duty": prefix + c.get("duty", ""),
                           "duration_s": c.get("duration_s", 5),
                           "camera": {"crop": c.get("crop", "medium"), "height": "eye"},
                           "sound": c.get("sound", ""), "key_text_en": c.get("key_text_en", "")}
            created.append(sid)
    engine = "llm" if engine_set == {"llm"} else ("heuristic" if engine_set == {"heuristic"} else "mixed")
    _persist()
    return ok({"created": created, "engine": engine})

@bp.get("/shots")
def list_shots():
    eid = request.args.get("episode_id", "")
    rows = [s for s in _SHOTS.values() if not eid or s["episode_id"] == eid]
    rows.sort(key=lambda x: x.get("id", ""))
    # 老数据补 ord（按镜号顺序）与 images（单图 image 归一为参考）；新数据按 ord 排
    dirty = False
    for i, s in enumerate(rows):
        if "ord" not in s:
            s["ord"] = i
            dirty = True
        if not s.get("images") and s.get("image"):
            s["images"] = [{"name": s["image"], "kind": "ref"}]
            dirty = True
    if dirty:
        _persist()
    rows.sort(key=lambda x: (x.get("ord", 0), x.get("id", "")))
    return ok(rows)

@bp.post("/shots")
def create_shot():
    """手工加镜（一行一行排）：body {episode_id, duty, duration_s, sound, camera, key_text_en}。"""
    b = request.get_json(force=True) or {}
    eid = b.get("episode_id", "")
    if not eid:
        return jsonify({"code": 4001, "msg": "缺少 episode_id"}), 400
    own = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    n = 1
    used = {s.get("id", "") for s in own}
    while True:
        sid = f"SHOT-{eid[-4:]}-M{n:03d}"
        if sid not in used and sid not in _SHOTS:
            break
        n += 1
    top = max([s.get("ord", 0) for s in own] + [-1]) + 1
    cam = b.get("camera") if isinstance(b.get("camera"), dict) else {}
    row = {"id": sid, "episode_id": eid, "ord": top,
           "duty": b.get("duty", ""), "duty_en": b.get("duty_en", ""),
           "duration_s": b.get("duration_s", 3),
           "camera": {"crop": cam.get("crop", "medium"), "height": cam.get("height", "eye"),
                      "movement": cam.get("movement", "固定")},
           "sound": b.get("sound", ""), "key_text_en": b.get("key_text_en", ""),
           "tier": _norm_tier(b.get("tier")), "draft": bool(b.get("draft", False))}
    _SHOTS[sid] = row
    _persist()
    return ok(row)

@bp.put("/shots/<sid>")
def update_shot(sid):
    b = request.get_json(force=True) or {}
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    for k in ("duty", "duty_en", "duration_s", "sound", "key_text_en", "ord", "image"):
        if k in b:
            s[k] = b[k]
    if "draft" in b:
        s["draft"] = bool(b.get("draft"))
    if "tier" in b:
        s["tier"] = _norm_tier(b.get("tier"))
    if "camera" in b and isinstance(b["camera"], dict):
        s["camera"] = {**(s.get("camera") or {}), **b["camera"]}
    _persist()
    return ok(s)

@bp.delete("/shots/<sid>")
def delete_shot(sid):
    _SHOTS.pop(sid, None)
    _persist()
    return ok({"deleted": sid})

REF_ROLES = ("character", "outfit", "style", "face", "pose", "scene", "prop")


def _norm_ref_role(v):
    v = (v or "").strip().lower()
    return v if v in REF_ROLES else ""


def _norm_ref_desc(v):
    return (v or "").strip()[:200]


def _norm_ref_label(v):
    return (v or "").strip()[:40]


@bp.post("/episode/<eid>/image/meta")
def set_episode_image_meta(eid):
    """给剧本参考图命名/补角色描述。body {name, label?, role?, desc?}。"""
    from pathlib import Path
    b = request.get_json(force=True) or {}
    ep = _EPS.get(eid)
    if not ep:
        return jsonify({"code": 4001, "msg": "episode 不存在"}), 400
    name = Path(b.get("name") or "").name
    hit = next((x for x in (ep.get("ref_images") or []) if x.get("name") == name), None)
    if not hit:
        return jsonify({"code": 4004, "msg": "图片未挂载"}), 404
    if "label" in b:
        hit["label"] = _norm_ref_label(b.get("label"))
    if "role" in b:
        hit["role"] = _norm_ref_role(b.get("role"))
    if "desc" in b:
        hit["desc"] = _norm_ref_desc(b.get("desc"))
    _persist()
    return ok({"images": ep["ref_images"]})


@bp.post("/shots/<sid>/image")
def upload_shot_image(sid):
    """分镜配图：落盘 data/uploads。kind=first/last 各占一个槽位（重传替换），kind=ref 可多张追加。
    form 可带 role/desc（见 attach）。老单图 image 首次带入 images 后清空归一。取图走 /api/images/<name>。"""
    from pathlib import Path
    import uuid as _uuid
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    kind = (request.form.get("kind") or "ref").strip()
    if kind not in ("ref", "first", "last"):
        kind = "ref"
    role = _norm_ref_role(request.form.get("role"))
    desc = _norm_ref_desc(request.form.get("desc"))
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    name = _uuid.uuid4().hex + (Path(f.filename or "").suffix[:10] or ".png")
    f.save(root / name)
    imgs = list(s.get("images") or [])
    legacy = s.get("image") or ""
    if legacy and not any(x.get("name") == legacy for x in imgs):
        imgs.append({"name": legacy, "kind": "ref"})
    if kind in ("first", "last"):
        imgs = [x for x in imgs if x.get("kind") != kind]
    imgs.append({"name": name, "kind": kind, "role": role, "desc": desc})
    s["images"] = imgs
    s["image"] = ""
    _persist()
    return ok({"images": imgs, "url": f"/api/images/{name}"})

@bp.post("/shots/<sid>/image/attach")
def attach_shot_image(sid):
    """把已上传的图片挂到分镜上（不重新传文件，供 Agent 单图导演用）。
    body {name, kind=first|last|ref, role?, desc?}，name 只取 basename，防目录穿越。
    role 限 character/outfit/style/face/pose/scene/prop；desc 为英文可见特征（≤200字）。"""
    from pathlib import Path
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    b = request.get_json(force=True) or {}
    name = Path(b.get("name") or "").name
    if not name:
        return jsonify({"code": 4001, "msg": "缺少 name"}), 400
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    if not (root / name).is_file():
        return jsonify({"code": 4001, "msg": "uploads 里没有这个文件"}), 400
    kind = (b.get("kind") or "first").strip()
    if kind not in ("ref", "first", "last"):
        kind = "ref"
    role = _norm_ref_role(b.get("role"))
    desc = _norm_ref_desc(b.get("desc"))
    imgs = list(s.get("images") or [])
    legacy = s.get("image") or ""
    if legacy and not any(x.get("name") == legacy for x in imgs):
        imgs.append({"name": legacy, "kind": "ref"})
    if kind in ("first", "last"):
        imgs = [x for x in imgs if x.get("kind") != kind]
    if not any(x.get("name") == name and x.get("kind") == kind for x in imgs):
        imgs.append({"name": name, "kind": kind, "role": role, "desc": desc})
    s["images"] = imgs
    s["image"] = ""
    _persist()
    return ok({"images": imgs, "url": f"/api/images/{name}"})


@bp.post("/shots/<sid>/image/meta")
def set_shot_image_meta(sid):
    """给已挂的图片补角色/描述（供多图参考导演用）。body {name, role?, desc?}。"""
    from pathlib import Path
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    b = request.get_json(force=True) or {}
    name = Path(b.get("name") or "").name
    hit = next((x for x in (s.get("images") or []) if x.get("name") == name), None)
    if not hit:
        return jsonify({"code": 4001, "msg": "这镜没挂这张图"}), 400
    if "role" in b:
        hit["role"] = _norm_ref_role(b.get("role"))
    if "desc" in b:
        hit["desc"] = _norm_ref_desc(b.get("desc"))
    _persist()
    return ok({"images": s["images"]})


@bp.delete("/shots/<sid>/image/<name>")
def delete_shot_image(sid, name):
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    s["images"] = [x for x in (s.get("images") or []) if x.get("name") != name]
    if (s.get("image") or "") == name:
        s["image"] = ""
    _persist()
    return ok({"images": s["images"], "deleted": name})

@bp.post("/clear/<eid>")
def clear_episode(eid):
    """级联清理（只清登记，文件留盘）：target=shots 仅草案分镜；
    outline 连带草案；script 连带大纲+草案+剧本参考图。"""
    b = request.get_json(force=True) or {}
    target = (b.get("target") or "shots").strip()
    if target not in ("shots", "outline", "script"):
        return jsonify({"code": 4001, "msg": "target 非法"}), 400
    cleared = []
    for sid in [sid for sid, s in _SHOTS.items() if s.get("episode_id") == eid]:
        _SHOTS.pop(sid, None)
        cleared.append(sid)
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    if target in ("outline", "script"):
        ep["outline_md"] = ""
        ep["outline_image"] = ""
    if target == "script":
        ep["screenplay_md"] = ""
        ep["ref_images"] = []
    _persist()
    return ok({"episode_id": eid, "target": target, "shots": cleared,
               "shot_count": len(cleared)})

@bp.post("/review/run/<eid>")
def review_run(eid):
    shots = [s for s in _SHOTS.values() if s["episode_id"] == eid]
    findings = []
    if not shots:
        findings.append({"level": "blocker", "rule": "SHT-01", "fix": "无SHOT覆盖"})
    verdict = "BLOCK" if findings else "PASS"
    _EPS.setdefault(eid, {}).update({"verdict": verdict})
    _persist()
    return ok({"verdict": verdict, "findings": findings})

@bp.get("/review/<eid>")
def review_latest(eid):
    ep = _EPS.get(eid, {})
    shots = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    total = round(sum(float(s.get("duration_s") or 0) for s in shots), 1)
    return ok({"verdict": ep.get("verdict", "draft"), "shots": len(shots), "total_s": total})
