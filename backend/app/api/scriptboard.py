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


def _save_cast(eid, raw_cast, text=""):
    """记本集出镜角色（点名或正文说话人）。返回解析结果；占位不落盘。
    显式点名会覆盖旧记忆；正文自动取角只在没有记忆时补。"""
    from ..services import cast as _cast
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    C = _cast.resolve_cast(raw_cast or ep.get("cast"), text, eid)
    if C["anchored"]:
        if raw_cast:
            ep["cast"] = [{"id": c["id"], "name": c["name"]} for c in C["cast"]]
        elif not (ep.get("cast") or []):
            ep["cast"] = [{"id": c["id"], "name": c["name"]} for c in C["cast"]]
        _persist()
    return C


@bp.get("/cast/<eid>")
def get_cast(eid):
    """本集出镜角色（只算不写）：cast=名1,名2 可临时试算。"""
    from ..services import cast as _cast
    raw = [n.strip() for n in (request.args.get("cast") or "").split(",") if n.strip()]
    ep = _EPS.get(eid, {})
    C = _cast.resolve_cast(raw or None, ep.get("screenplay_md", "") or "", eid)
    return ok({"episode_id": eid, **C})


@bp.put("/cast/<eid>")
def set_cast(eid):
    """手工点名：body {names:[...]} 或 {cast:[{id|name}]}；空数组=清空记忆、回到自动取角。"""
    from ..services import cast as _cast
    b = request.get_json(force=True, silent=True) or {}
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    if "names" in b or "cast" in b:
        rows = b.get("names") if "names" in b else b.get("cast")
        rows = rows if isinstance(rows, list) else []
        rows = [r for r in rows if (r if isinstance(r, dict) else str(r or "").strip())]
        if rows:
            ep["cast"] = [{"id": c["id"], "name": c["name"]} for c in _cast.resolve_cast(rows, "", eid)["cast"]]
        else:
            ep["cast"] = []
        _persist()
    C = _cast.resolve_cast(ep.get("cast"), ep.get("screenplay_md", "") or "", eid)
    return ok({"episode_id": eid, **C})

@bp.put("/screenplay/<eid>")
def save_screenplay(eid):
    b = request.get_json(force=True)
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    md = b.get("screenplay_md", "")
    old = ep.get("screenplay_md", "") or ""
    # 空内容覆盖非空剧本 = 静默清库（2026-10-16 事故：切集/切页时 debounce 的自动保存把 2187 字稿冲空）。
    # 要真清空必须显式带 force:true，前端手动清空会走二次确认 + force。
    if not str(md).strip() and str(old).strip() and not b.get("force"):
        return ok({"episode_id": eid, "chars": len(old), "kept": True,
                   "msg": "拒绝用空内容覆盖已有剧本；确要清空请带 force:true"})
    ep["screenplay_md"] = md
    ep["segs"] = []
    # 正文说话人即出镜名单：存稿时顺手记住（显式 cast 优先，别覆盖手工点名）
    C = _save_cast(eid, b.get("cast"), md)
    return ok({"episode_id": eid, "chars": len(ep["screenplay_md"]), "kept": False,
               "cast": ep.get("cast") or [], "cast_source": C["source"]})

@bp.get("/screenplay/<eid>")
def get_screenplay(eid):
    """取本集剧本底稿（分镜页刷新回填用）。"""
    ep = _EPS.get(eid, {})
    return ok({"episode_id": eid, "screenplay_md": ep.get("screenplay_md", ""),
               "ref_images": ep.get("ref_images", [])})


@bp.post("/screenplay/validate")
@bp.post("/screenplay/validate/<eid>")
def validate_screenplay_ep(eid=""):
    """剧本结构校验：body {screenplay_md?} 为空则读库。返回 findings。"""
    from ..services.draft import validate_screenplay
    b = request.get_json(force=True, silent=True) or {}
    md = b.get("screenplay_md")
    if md is None and eid:
        md = _EPS.get(eid, {}).get("screenplay_md", "")
    findings = validate_screenplay(md or "")
    blockers = sum(1 for f in findings if f["level"] == "blocker")
    return ok({"episode_id": eid, "findings": findings,
               "blockers": blockers, "passed": blockers == 0, "count": len(findings)})


@bp.post("/screenplay/normalize/<eid>")
def normalize_screenplay_ep(eid):
    """规范化：补 H1/SC 编号/压空行，不改台词。body {screenplay_md?, save?=true}。"""
    from ..services.draft import normalize_screenplay
    b = request.get_json(force=True, silent=True) or {}
    md = b.get("screenplay_md")
    if md is None:
        md = _EPS.get(eid, {}).get("screenplay_md", "")
    normed, changes = normalize_screenplay(md or "", eid)
    if b.get("save", True):
        ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
        ep["screenplay_md"] = normed
        ep["segs"] = []
        _persist()
    return ok({"episode_id": eid, "screenplay_md": normed, "changes": changes,
               "chars": len(normed)})


@bp.post("/screenplay/estimate")
@bp.post("/screenplay/estimate/<eid>")
def estimate_screenplay_ep(eid=""):
    """时长估算：body {screenplay_md?} 为空则读库。返回 chars/est_s/是否10-30s。"""
    from ..services.draft import estimate_screenplay
    b = request.get_json(force=True, silent=True) or {}
    md = b.get("screenplay_md")
    if md is None and eid:
        md = _EPS.get(eid, {}).get("screenplay_md", "")
    return ok({"episode_id": eid, **estimate_screenplay(md or "")})


@bp.get("/beats/<eid>")
def beats_from_screenplay(eid):
    """beats 解析：从 screenplay_md 提场景/对白，供 export-bundle 与投流母本用。"""
    from ..services.draft import parse_beats_from_screenplay
    ep = _EPS.get(eid, {})
    beats = parse_beats_from_screenplay(ep.get("screenplay_md", ""), eid)
    return ok({"episode_id": eid, "beats": beats, "count": len(beats)})


@bp.post("/screenplay/revise/<eid>")
def revise_screenplay(eid):
    """定点修订：body {instruction}。LLM优先改写，失败回退追加修订段。不抛500。"""
    b = request.get_json(force=True, silent=True) or {}
    ins = (b.get("instruction") or "").strip()[:500]
    if not ins:
        return jsonify({"code": 4001, "msg": "缺少 instruction"}), 400
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    cur = ep.get("screenplay_md", "") or ""
    new_md, engine = cur, "noop"
    try:
        from ..services.llm_opencode import llm_cfg, _post
        cfg = llm_cfg()
        if cfg.get("provider") == "opencode" and cfg.get("key") and cfg.get("model"):
            import re as _re
            model_id = _re.sub(r"^opencode-go/", "", cfg["model"])
            prompt = ("你是短剧剧本修订助手。保留作者原文，只做用户点名的定点修订，"
                      "不要整篇重写，不要加无关机关。对白保持‘角色：台词’，场景标题保持‘## EP-SC’。"
                      "修订要求：%s\n\n剧本原文：\n%s" % (ins, cur[:4000]))
            txt = _post(cfg["base"], cfg["key"], model_id, prompt, effort=cfg.get("effort", ""))
            if (txt or "").strip() and len((txt or "").strip()) >= 60:
                new_md, engine = txt.strip() + "\n", "llm"
    except Exception:
        pass
    if engine == "noop":
        new_md = (cur.rstrip() + "\n\n[修订 %s] %s\n" % (__import__("datetime").datetime.now().strftime("%m%d%H%M"), ins)).strip() + "\n"
        engine = "template"
    ep["screenplay_md"] = new_md
    ep["segs"] = []
    _persist()
    return ok({"episode_id": eid, "screenplay_md": new_md, "engine": engine,
               "chars": len(new_md)})


@bp.post("/episode/<eid>/freeze")
def freeze_episode(eid):
    """冻结版本：快照 screenplay/outline/shots只数，供精品迭代对比。"""
    import time as _time
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    vers = ep.setdefault("versions", [])
    shots_n = sum(1 for s in _SHOTS.values() if s.get("episode_id") == eid)
    vno = (max([v.get("vno", 0) for v in vers] + [0]) + 1)
    snap = {"vno": vno, "created_at": int(_time.time() * 1000),
            "screenplay_md": ep.get("screenplay_md", ""), "outline_md": ep.get("outline_md", ""),
            "shots": shots_n, "verdict": ep.get("verdict", "draft")}
    vers.append(snap)
    # 只保留最近20版
    ep["versions"] = vers[-20:]
    _persist()
    return ok({"episode_id": eid, "vno": vno, "shots": shots_n})


@bp.get("/episode/<eid>/versions")
def list_versions(eid):
    ep = _EPS.get(eid, {})
    vers = ep.get("versions", []) or []
    lite = [{"vno": v.get("vno"), "created_at": v.get("created_at"),
             "shots": v.get("shots"), "verdict": v.get("verdict"),
             "screenplay_chars": len(v.get("screenplay_md", "") or ""),
             "outline_chars": len(v.get("outline_md", "") or "")} for v in vers]
    return ok({"episode_id": eid, "versions": lite, "count": len(lite)})

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

def _sync_screenplay_from_outline(ep, eid):
    """大纲落盘后同步底稿：仅当 screenplay 为空且 outline 非空时写，不覆盖人工底稿。
    内容=方向一句话 + 分镜表转写 + 合计行；解析失败则回退全文前 800 字。返回是否同步。"""
    try:
        if ((ep.get("screenplay_md") or "").strip()):
            return False
        md = (ep.get("outline_md") or "").strip()
        if not md:
            return False
        lines = md.splitlines()
        direction = ""
        in_dir = False
        for ln in lines:
            s = ln.strip()
            if s.startswith("##") and "方向一句话" in s:
                in_dir = True
                continue
            if in_dir:
                if not s:
                    continue
                if s.startswith("#"):
                    break
                direction = s
                break
        beats = []
        for ln in lines:
            s = ln.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 3:
                continue
            if any("镜号" in c or "---" in c for c in cells):
                continue
            mid, content, dur, move = (cells + ["", "", "", ""])[:4]
            if not content or len(beats) >= 8:
                continue
            tail = f"（{dur}，{move}）" if (dur or move) else ""
            beats.append(f"{mid or '镜'+str(len(beats)+1)}：{content}{tail}")
        total = ""
        for ln in lines:
            if "合计" in ln and ("镜" in ln or "秒" in ln):
                total = ln.strip().lstrip("# ").strip()
                break
        parts = [f"# {eid} 剧本底稿（大纲同步，可改）", ""]
        if direction:
            parts += [direction, ""]
        if beats:
            parts += beats + [""]
        if total:
            parts += [total, ""]
        if not direction and not beats:
            parts += [md[:800]]
        ep["screenplay_md"] = "\n".join(parts).strip() + "\n"
        ep["segs"] = []
        return True
    except Exception:
        return False


@bp.put("/outline/<eid>")
def save_outline(eid):
    b = request.get_json(force=True) or {}
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    kept = False
    if "outline_md" in b:
        new_md = b.get("outline_md", "")
        old_md = ep.get("outline_md", "") or ""
        # 同理：空大纲不许静默覆盖已有大纲（自动保存/切集踩过同类坑）
        if not str(new_md).strip() and str(old_md).strip() and not b.get("force"):
            kept = True
        else:
            ep["outline_md"] = new_md
    if "outline_image" in b:
        from pathlib import Path as _P
        ep["outline_image"] = _P(b.get("outline_image") or "").name
    synced = _sync_screenplay_from_outline(ep, eid)
    _persist()
    return ok({"episode_id": eid, "chars": len(ep.get("outline_md", "")), "kept": kept,
               "screenplay_synced": synced, "screenplay_chars": len(ep.get("screenplay_md", ""))})

@bp.post("/outline/generate/<eid>")
def outline_generate(eid):
    """轻大纲：不走 dsh，直接调 services/draft（LLM 优先，模板回退）并落盘。
    出镜角色走角色库取角（body.cast 可点名覆盖），prompt 里不再写死人名。"""
    from ..services.draft import build_outline_md
    from pathlib import Path as _P
    b = request.get_json(force=True) or {}
    total_s = int(b.get("total_s") or 15)
    engine = (b.get("engine") or "pixai").strip() or "pixai"
    tier = _norm_tier(b.get("tier"))
    hint = (b.get("hint") or b.get("screenplay_md") or "").strip()[:800]
    image = _P(b.get("image") or b.get("outline_image") or "").name
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    raw_cast = b.get("cast") if b.get("cast") else None   # 空数组=没点名，别把记忆清掉
    C = _save_cast(eid, raw_cast, hint or (ep.get("screenplay_md") or ""))
    md, tag = build_outline_md(eid, total_s, engine, tier, hint, image, cast=C["cast"])
    ep["outline_md"] = md
    if image:
        ep["outline_image"] = image
    synced = _sync_screenplay_from_outline(ep, eid)
    _persist()
    return ok({"episode_id": eid, "outline_md": md, "outline_image": ep.get("outline_image", ""),
               "engine": tag, "chars": len(md), "cast": ep.get("cast") or [],
               "cast_source": C["source"],
               "screenplay_synced": synced, "screenplay_chars": len(ep.get("screenplay_md", ""))})

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
    # 幂等：先清本集旧草案（draft=True），保留已定稿镜，防止重复点击堆出 3+3+3…
    # 另带走无内容空镜（duty/duty_en/sound 全空且无配图，多为分镜页“添加行”残留），免得“无内容”卡占时间轴
    def _is_junk(s):
        if s.get("episode_id") != eid:
            return False
        if (s.get("duty") or "").strip() or (s.get("duty_en") or "").strip() or (s.get("sound") or "").strip():
            return False
        if s.get("images") or s.get("image"):
            return False
        return True
    for sid in [sid for sid, s in _SHOTS.items() if s.get("episode_id") == eid and (s.get("draft") or _is_junk(s))]:
        _SHOTS.pop(sid, None)
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
           "note": str(b.get("note", ""))[:500],
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
    if "note" in b:
        s["note"] = str(b.get("note") or "")[:500]
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


@bp.post("/shots/import")
def import_shots():
    """L-Port 回执批量收口（回程）：body {episode_id, shots[], mode=merge|replace, source}。

    shots 同时兼容 anime 原生（id/duty/duration_s/camera/sound/tier）与
    L-Port 6 字段（shot_id/purpose|duty_cn/duration_seconds/crop|framing/sound_cn）。
    merge=按 id upsert（默认），replace=先清空本集再全量写入。
    重型必填（source_refs/location_binding 等）不动，由 Suli 侧后续补。
    """
    b = request.get_json(force=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺少 episode_id"}), 400
    raw = b.get("shots")
    if not isinstance(raw, list) or not raw:
        return jsonify({"code": 4001, "msg": "shots 为空数组"}), 400
    if len(raw) > 64:
        return jsonify({"code": 4001, "msg": "单次最多 64 镜"}), 400
    mode = str(b.get("mode") or "merge").strip().lower()
    source = str(b.get("source") or "lport")[:40]
    if mode == "replace":
        for sid in [k for k, s in _SHOTS.items() if s.get("episode_id") == eid]:
            _SHOTS.pop(sid, None)
    _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    created, updated = [], []
    own = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    used = {s.get("id", "") for s in own}
    top = max([s.get("ord", 0) for s in own] + [-1]) + 1
    n = 1
    for item in raw[:64]:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id") or item.get("shot_id") or "").strip()
        if not sid:
            while True:
                cand = f"SHOT-{eid[-4:]}-M{n:03d}"
                n += 1
                if cand not in used and cand not in _SHOTS:
                    sid = cand
                    break
        duty = str(item.get("duty") or item.get("purpose") or item.get("duty_cn") or "").strip()[:500]
        duty_en = str(item.get("duty_en") or "").strip()[:1000]
        try:
            dur = float(item.get("duration_s", item.get("duration_seconds", 5)) or 5)
        except (TypeError, ValueError):
            dur = 5
        dur = min(max(dur, 1), 30)
        cam = item.get("camera") if isinstance(item.get("camera"), dict) else {}
        framing = item.get("framing") if isinstance(item.get("framing"), dict) else {}
        crop = str(cam.get("crop") or item.get("crop") or framing.get("size") or "medium").strip() or "medium"
        row = _SHOTS.get(sid)
        if row and row.get("episode_id") == eid:
            row["duty"] = duty or row.get("duty", "")
            if duty_en:
                row["duty_en"] = duty_en
            row["duration_s"] = dur
            row["camera"] = {**(row.get("camera") or {}), "crop": crop,
                             "height": cam.get("height", (row.get("camera") or {}).get("height", "eye")),
                             "movement": cam.get("movement", (row.get("camera") or {}).get("movement", "固定"))}
            row["sound"] = str(item.get("sound", item.get("sound_cn", row.get("sound", ""))) or "")
            row["key_text_en"] = str(item.get("key_text_en") or row.get("key_text_en", ""))[:2000]
            row["tier"] = _norm_tier(item.get("tier", row.get("tier", "")))
            row["draft"] = True
            row["note"] = f"{source}回执"[:500]
            updated.append(sid)
        else:
            if sid in _SHOTS:
                continue
            _SHOTS[sid] = {"id": sid, "episode_id": eid, "ord": top,
                           "duty": duty, "duty_en": duty_en, "duration_s": dur,
                           "camera": {"crop": crop, "height": cam.get("height", "eye"),
                                      "movement": cam.get("movement", "固定")},
                           "sound": str(item.get("sound", item.get("sound_cn", "")) or ""),
                           "key_text_en": str(item.get("key_text_en") or "")[:2000],
                           "note": f"{source}回执"[:500],
                           "tier": _norm_tier(item.get("tier")), "draft": True}
            used.add(sid)
            top += 1
            created.append(sid)
    _persist()
    return ok({"episode_id": eid, "mode": mode, "created": created,
               "updated": updated, "count": len(created) + len(updated)})


# ── L-Port 详细提示词回传（提示词收口，2026-10-18）─────────────────────
# 与 shots/import（分镜回执）分两口：这边只把提示词写进"已存在的镜"，
# 不由提示词造镜（造镜归 shots/import）；缺镜只报告 missing，不静默丢。

_LP_PROMPT_CAP = {
    "seg_id": 40, "director_cn": 2000, "camera_note": 300,
    "key_text_en": 2000, "dialogue_cn": 500, "crop": 40, "ref_status": 40,
}


def _norm_prompt_item(item):
    """单条回传提示词归一（纯函数）：无 shot_id 或无正文返回 None。"""
    if not isinstance(item, dict):
        return None
    sid = str(item.get("shot_id") or item.get("id") or "").strip()[:64]
    if not sid:
        return None
    row = {}
    for k, cap in _LP_PROMPT_CAP.items():
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            row[k] = v.strip()[:cap]
    rm = item.get("ref_missing")
    if isinstance(rm, list):
        rm = [str(x).strip()[:100] for x in rm if str(x).strip()][:8]
        if rm:
            row["ref_missing"] = rm
    d = item.get("duration_s")
    try:
        d = float(d) if d is not None else None
    except (TypeError, ValueError):
        d = None
    if d and d > 0:
        row["duration_s"] = round(d, 1)
    # 空提示词不落：只带回 seg_id/labels 的条目不写库（避免假回执）
    if not any(row.get(k) for k in ("director_cn", "camera_note", "key_text_en", "dialogue_cn")):
        return None
    return sid, row


@bp.post("/shots/prompts/import")
def import_shot_prompts():
    """L-Port 详细提示词回传（回程）：body {episode_id, prompts[], source?, package_id?}。

    prompts 每项 {shot_id, seg_id?, director_cn?, camera_note?, key_text_en?,
    dialogue_cn?, ref_status?, ref_missing?, duration_s?, crop?}，
    按 shot_id 写进该镜的 lport_prompts（当前版本，覆盖旧的）；只写本集已存在的镜，
    缺镜报告 missing 不造镜。"""
    import datetime as _dt
    b = request.get_json(force=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺少 episode_id"}), 400
    raw = b.get("prompts")
    if not isinstance(raw, list) or not raw:
        return jsonify({"code": 4001, "msg": "prompts 为空数组"}), 400
    if len(raw) > 64:
        return jsonify({"code": 4001, "msg": "单次最多 64 镜"}), 400
    source = str(b.get("source") or "lport")[:40]
    pkg_id = str(b.get("package_id") or "")[:64]
    updated, missing, skipped = [], [], 0
    for item in raw[:64]:
        norm = _norm_prompt_item(item)
        if not norm:
            skipped += 1
            continue
        sid, row = norm
        s = _SHOTS.get(sid)
        if not s or s.get("episode_id") != eid:
            missing.append(sid)
            continue
        s["lport_prompts"] = {
            "source": source,
            "package_id": pkg_id,
            "at": _dt.datetime.now().isoformat(timespec="seconds"),
            **row,
        }
        updated.append(sid)
    _persist()
    return ok({"episode_id": eid, "updated": updated, "missing": missing,
               "skipped": skipped, "count": len(updated), "source": source})


# ── L-Port 视频提示词回传（PixAI/H3 定稿，落 lport_video_prompts）──────────
# 与上面的中性导演提示词分两口：那边管分镜文本，这边管可直接投产的视频提示词全文。
_LP_VIDEO_CAP = {
    "engine": 20, "video_model": 40, "ref_mode": 20, "tier": 20,
    "prompt": 8000, "ref_note": 500,
}


def _norm_video_prompt_item(item):
    """单条视频提示词归一（纯函数）：无 shot_id 或无 prompt 返回 None。"""
    if not isinstance(item, dict):
        return None
    sid = str(item.get("shot_id") or item.get("id") or "").strip()[:64]
    prompt = item.get("prompt")
    if not sid or not isinstance(prompt, str) or not prompt.strip():
        return None
    row = {}
    for k, cap in _LP_VIDEO_CAP.items():
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            row[k] = v.strip()[:cap]
    refs = []
    for r in (item.get("refs") or [])[:8]:
        if not isinstance(r, dict):
            continue
        refs.append({"tag": str(r.get("tag") or "")[:20],
                     "name": str(r.get("name") or "")[:120],
                     "role": str(r.get("role") or "")[:40]})
    if refs:
        row["refs"] = refs
    applied = [str(x)[:160] for x in (item.get("applied") or []) if str(x).strip()][:8]
    if applied:
        row["applied"] = applied
    d = item.get("duration_s")
    try:
        d = float(d) if d is not None else None
    except (TypeError, ValueError):
        d = None
    if d and d > 0:
        row["duration_s"] = round(d, 1)
    row["prompt"] = prompt.strip()[:8000]
    return sid, row


@bp.post("/shots/video-prompts/import")
def import_shot_video_prompts():
    """L-Port 视频提示词回传（回程）：body {episode_id, prompts[], source?, package_id?}。

    prompts 每项 {shot_id, prompt*, engine?, video_model?, ref_mode?, tier?,
    duration_s?, refs?, ref_note?, applied?}，按 shot_id 写进该镜的 lport_video_prompts
    （当前版本，覆盖旧的）；只写本集已存在的镜，缺镜报告 missing 不造镜。"""
    import datetime as _dt
    b = request.get_json(force=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺少 episode_id"}), 400
    raw = b.get("prompts")
    if not isinstance(raw, list) or not raw:
        return jsonify({"code": 4001, "msg": "prompts 为空数组"}), 400
    if len(raw) > 64:
        return jsonify({"code": 4001, "msg": "单次最多 64 镜"}), 400
    source = str(b.get("source") or "lport")[:40]
    pkg_id = str(b.get("package_id") or "")[:64]
    items = [x for x in (_norm_video_prompt_item(it) for it in raw[:64]) if x]
    if not items:
        return jsonify({"code": 4001, "msg": "prompts 里没有可回传的条目（缺 shot_id 或 prompt）"}), 400
    updated, missing, skipped = [], [], len(raw[:64]) - len(items)
    for sid, row in items:
        s = _SHOTS.get(sid)
        if not s or s.get("episode_id") != eid:
            missing.append(sid)
            continue
        s["lport_video_prompts"] = {
            "source": source,
            "package_id": pkg_id,
            "at": _dt.datetime.now().isoformat(timespec="seconds"),
            **row,
        }
        updated.append(sid)
    _persist()
    return ok({"episode_id": eid, "updated": updated, "missing": missing,
               "skipped": skipped, "count": len(updated), "source": source})


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
    from ..services.draft import build_review
    shots = [s for s in _SHOTS.values() if s["episode_id"] == eid]
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    total = round(sum(float(s.get("duration_s") or 0) for s in shots), 1)
    verdict, findings = build_review(ep.get("screenplay_md", ""), shots, total)
    ep["verdict"] = verdict
    ep["review_findings"] = findings
    ep["review_at"] = __import__("time").time()
    _persist()
    return ok({"episode_id": eid, "verdict": verdict, "findings": findings,
               "shots": len(shots), "total_s": total})


@bp.get("/review/<eid>")
def review_latest(eid):
    ep = _EPS.get(eid, {})
    shots = [s for s in _SHOTS.values() if s.get("episode_id") == eid]
    total = round(sum(float(s.get("duration_s") or 0) for s in shots), 1)
    return ok({"episode_id": eid, "verdict": ep.get("verdict", "draft"),
               "shots": len(shots), "total_s": total,
               "findings": ep.get("review_findings", [])})
