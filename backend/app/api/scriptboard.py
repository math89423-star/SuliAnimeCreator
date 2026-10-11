"""scriptboard 蓝图：剧本存管 + 自动拆分镜(LLM优先，规则回退) + 结构门。落盘 backend/data/scriptboard_db.json。"""
from flask import Blueprint, request, jsonify
from ..services.disk_store import load, save

bp = Blueprint("scriptboard", __name__, url_prefix="/api/v1/scriptboard")

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
           "duty": b.get("duty", ""), "duration_s": b.get("duration_s", 3),
           "camera": {"crop": cam.get("crop", "medium"), "height": cam.get("height", "eye"),
                      "movement": cam.get("movement", "固定")},
           "sound": b.get("sound", ""), "key_text_en": b.get("key_text_en", "")}
    _SHOTS[sid] = row
    _persist()
    return ok(row)

@bp.put("/shots/<sid>")
def update_shot(sid):
    b = request.get_json(force=True) or {}
    s = _SHOTS.get(sid)
    if not s:
        return jsonify({"code": 4001, "msg": "shot 不存在"}), 400
    for k in ("duty", "duration_s", "sound", "key_text_en", "ord", "image"):
        if k in b:
            s[k] = b[k]
    if "camera" in b and isinstance(b["camera"], dict):
        s["camera"] = {**(s.get("camera") or {}), **b["camera"]}
    _persist()
    return ok(s)

@bp.delete("/shots/<sid>")
def delete_shot(sid):
    _SHOTS.pop(sid, None)
    _persist()
    return ok({"deleted": sid})

@bp.post("/shots/<sid>/image")
def upload_shot_image(sid):
    """分镜配图：落盘 data/uploads。kind=first/last 各占一个槽位（重传替换），kind=ref 可多张追加。
    老单图 image 首次带入 images 后清空归一。取图走 /api/images/<name>。"""
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
    imgs.append({"name": name, "kind": kind})
    s["images"] = imgs
    s["image"] = ""
    _persist()
    return ok({"images": imgs, "url": f"/api/images/{name}"})

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
