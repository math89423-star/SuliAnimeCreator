"""character 蓝图：原创角色设计（承接 CharacterMaker）。落盘 backend/data/character_db.json。
skill catalog说明：本会话仅有 openviking-memory（记忆库），与脚手架任务不匹配，未调用；用常规读写完成。
"""
from flask import Blueprint, request, jsonify
import uuid
import time
from ..services.disk_store import load, save
from ..services.character_prompts import build_slot_prompt, SLOT_CN

bp = Blueprint("character", __name__, url_prefix="/api/v1/characters")

SECTIONS = ["head", "half", "full"]
ATTIRES = ["undressed", "dressed"]
SLOTS = ["front", "side", "back"]
OUTFIT_CATS = ["headwear", "top", "bottom", "shoes"]
DIMS = ["hairstyle", "face", "physique", "identity", "anchor_en"]

_DB = load("character_db.json", {})
_CHARS = _DB.get("chars", {})
_ASSETS = {int(k): v for k, v in _DB.get("assets", {}).items()}
_SLOT_PROMPTS = {tuple(k.split("|")): v for k, v in _DB.get("slot_prompts", {}).items()}
_SLOT_SVGS = {tuple(k.split("|")): v for k, v in _DB.get("slot_svgs", {}).items()}
_OUTFITS = {int(k): v for k, v in _DB.get("outfits", {}).items()}
_OUTFIT_CATS_MAP = {tuple(k.split("|")): v for k, v in _DB.get("outfit_cats", {}).items()}
_DOCS = _DB.get("docs", {})
_VERSIONS = _DB.get("versions", {})
_SEQ = _DB.get("seq", {"asset": 1, "outfit": 1, "version": 1})

def _persist():
    save("character_db.json", {
        "chars": _CHARS,
        "assets": {str(k): v for k, v in _ASSETS.items()},
        "slot_prompts": {"|".join(k): v for k, v in _SLOT_PROMPTS.items()},
        "slot_svgs": {"|".join(k): v for k, v in _SLOT_SVGS.items()},
        "outfits": {str(k): v for k, v in _OUTFITS.items()},
        "outfit_cats": {"|".join(k): v for k, v in _OUTFIT_CATS_MAP.items()},
        "docs": _DOCS, "versions": _VERSIONS, "seq": _SEQ,
    })

def ok(data):
    return jsonify({"code": 0, "data": data})

def _now():
    return int(time.time() * 1000)

@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    cid = "CHAR-" + uuid.uuid4().hex[:6].upper()
    _CHARS[cid] = {"id": cid, "name": b.get("name", "新角色"),
        "hairstyle": b.get("hairstyle", ""), "face": b.get("face", ""),
        "physique": b.get("physique", ""), "identity": b.get("identity", ""),
        "anchor_en": b.get("anchor_en", ""),
        "avatar_path": "", "created_at": _now(), "updated_at": _now()}
    _DOCS[cid] = {"doc_html": ""}
    _VERSIONS[cid] = []
    _persist()
    return ok(_CHARS[cid])

@bp.get("")
def list_all():
    return ok(list(_CHARS.values()))

@bp.get("/gallery")
def gallery():
    """展览首页聚合：头像url+四维摘要+服装数+版本数+槽位提示词数。注意放 /<cid> 前。"""
    rows = []
    for c in _CHARS.values():
        cid = c["id"]
        av = c.get("avatar_path", "")
        rows.append({
            "id": cid, "name": c.get("name", ""),
            "avatar_url": f"/api/images/{av}" if av else "",
            "hairstyle": c.get("hairstyle", ""), "face": c.get("face", ""),
            "physique": c.get("physique", ""), "identity": c.get("identity", ""),
            "outfits": sum(1 for o in _OUTFITS.values() if o.get("character_id") == cid),
            "versions": len(_VERSIONS.get(cid, [])),
            "slots": sum(1 for (cc, _k, _s) in _SLOT_PROMPTS if cc == cid),
            "updated_at": c.get("updated_at", 0),
        })
    rows.sort(key=lambda r: r["updated_at"], reverse=True)
    return ok(rows)

@bp.get("/<cid>")
def get_one(cid):
    return ok(_CHARS.get(cid, {}))

@bp.put("/<cid>")
def update_one(cid):
    b = request.get_json(force=True) or {}
    c = _CHARS.get(cid)
    if not c:
        return ok({})
    for k in ["name", "hairstyle", "face", "physique", "identity", "anchor_en"]:
        if k in b:
            c[k] = b[k]
    c["updated_at"] = _now()
    _persist()
    return ok(c)

@bp.delete("/<cid>")
def delete_one(cid):
    """删角色：连带清掉它在各子表里的行（docs / versions / slot_prompts / slot_svgs / assets）。

    只 pop 主表的话，删完角色库里还挂着它的槽位提示词与版本记录，属于残渣。
    """
    existed = cid in _CHARS
    _CHARS.pop(cid, None)
    _DOCS.pop(cid, None)
    _VERSIONS.pop(cid, None)
    for k in [k for k in _SLOT_PROMPTS if k and k[0] == cid]:
        _SLOT_PROMPTS.pop(k, None)
    for k in [k for k in _SLOT_SVGS if k and k[0] == cid]:
        _SLOT_SVGS.pop(k, None)
    for aid in [aid for aid, a in _ASSETS.items() if (a or {}).get("character_id") == cid]:
        _ASSETS.pop(aid, None)
    _persist()
    return ok({"deleted": cid, "existed": existed})

@bp.delete("")
def delete_all():
    """清空角色库：角色、设定图、槽位提示词、文档、版本记录一起抹掉。

    单独删角色只清它自己的行；历史上删掉的角色会在子表里留下孤儿行
    （docs / versions / slot_prompts），要彻底干净就走这个口。
    """
    counts = {
        "chars": len(_CHARS),
        "assets": len(_ASSETS),
        "slot_prompts": len(_SLOT_PROMPTS),
        "slot_svgs": len(_SLOT_SVGS),
        "outfits": len(_OUTFITS),
        "outfit_cats": len(_OUTFIT_CATS_MAP),
        "docs": len(_DOCS),
        "versions": len(_VERSIONS),
    }
    _CHARS.clear()
    _ASSETS.clear()
    _SLOT_PROMPTS.clear()
    _SLOT_SVGS.clear()
    _OUTFITS.clear()
    _OUTFIT_CATS_MAP.clear()
    _DOCS.clear()
    _VERSIONS.clear()
    _persist()
    return ok({"cleared": counts})


def _kind(section, attire):
    return f"{section}_{attire}"

@bp.get("/<cid>/assets")
def list_assets(cid):
    return ok([a for a in _ASSETS.values() if a["character_id"] == cid])

@bp.post("/<cid>/assets")
def upsert_asset_meta(cid):
    b = request.get_json(force=True) or {}
    aid = _SEQ["asset"]; _SEQ["asset"] += 1
    row = {"id": aid, "character_id": cid, "kind": b.get("kind", "head_dressed"),
           "slot": b.get("slot", "front"), "path": b.get("path", ""),
           "url": b.get("url", ""), "note": b.get("note", ""),
           "created_at": _now(), "updated_at": _now()}
    _ASSETS[aid] = row
    _persist()
    return ok(row)

@bp.delete("/<cid>/assets/<int:aid>")
def delete_asset(cid, aid):
    _ASSETS.pop(aid, None)
    _persist()
    return ok({"deleted": aid})

@bp.delete("/<cid>/assets")
def clear_assets(cid):
    """清除槽位图（角色页「清除」按钮的图侧）：按 kind(+slot) 批量删。
    不传 slot → 清该 kind 的 front/side/back 三槽；kind、slot 都不传 → 清该角色全部槽位图。
    顺带删 uploads 里的真文件（只删 data/uploads 下的裸文件名，删不动不影响库内清除）。"""
    from pathlib import Path
    b = request.get_json(silent=True) or {}
    kind = str(b.get("kind") or request.args.get("kind") or "").strip()
    slot = str(b.get("slot") or request.args.get("slot") or "").strip()
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    hit = []
    for aid, a in list(_ASSETS.items()):
        if a.get("character_id") != cid:
            continue
        if kind and a.get("kind") != kind:
            continue
        if slot and a.get("slot") != slot:
            continue
        hit.append(aid)
        name = str(a.get("path") or "")
        if name and "/" not in name and "\\" not in name:
            try:
                (root / name).unlink(missing_ok=True)
            except OSError:
                pass
        _ASSETS.pop(aid, None)
    if hit:
        _persist()
    return ok({"cleared": len(hit), "kind": kind, "slot": slot})

@bp.post("/<cid>/avatar/from-asset")
def avatar_from_asset(cid):
    b = request.get_json(force=True) or {}
    c = _CHARS.get(cid, {})
    c["avatar_path"] = str(b.get("asset_id", ""))
    _persist()
    return ok({"avatar_path": c.get("avatar_path", "")})

@bp.get("/<cid>/slot-prompts")
def list_slot_prompts(cid):
    return ok([{"kind": k, "slot": s, "prompt": p} for (cc, k, s), p in _SLOT_PROMPTS.items() if cc == cid])

@bp.put("/<cid>/slot-prompts")
def set_slot_prompt(cid):
    b = request.get_json(force=True) or {}
    _SLOT_PROMPTS[(cid, b.get("kind", ""), b.get("slot", ""))] = b.get("prompt", "")
    _persist()
    return ok({"kind": b.get("kind"), "slot": b.get("slot"), "prompt": b.get("prompt")})

@bp.delete("/<cid>/slot-prompts")
def clear_slot_prompts(cid):
    """清除槽位提示词（角色页「清空」按钮）：{kind, slot, which=both|cn|en}。
    不传 slot → 清该组的 front/side/back；不传 kind → 清该角色全部槽位提示词。
    `front` 与 `front_cn` 视为同一槽（cn 是英文槽 +_cn 后缀）。"""
    b = request.get_json(silent=True) or {}
    kind = str(b.get("kind") or request.args.get("kind") or "").strip()
    slot = str(b.get("slot") or request.args.get("slot") or "").strip()
    which = str(b.get("which") or request.args.get("which") or "both").strip().lower()
    if which not in ("both", "cn", "en"):
        which = "both"
    base = slot[:-3] if slot.endswith("_cn") else slot
    hit = []
    for key in list(_SLOT_PROMPTS):
        parts = list(key) if isinstance(key, (tuple, list)) else str(key).split("|")
        if len(parts) != 3:  # 脏键不动它
            continue
        c0, k0, s0 = parts[0], parts[1], str(parts[2])
        if c0 != cid:
            continue
        if kind and k0 != kind:
            continue
        s_base = s0[:-3] if s0.endswith("_cn") else s0
        if base and s_base != base:
            continue
        is_cn = s0.endswith("_cn")
        if which == "cn" and not is_cn:
            continue
        if which == "en" and is_cn:
            continue
        hit.append(key)
    for key in hit:
        _SLOT_PROMPTS.pop(key, None)
    if hit:
        _persist()
    return ok({"cleared": len(hit), "kind": kind, "slot": base, "which": which})

# SLOT_CN 见 services/character_prompts（唯一真源，此处保留导入名兼容）


@bp.post("/<cid>/slot-prompts/generate")
def gen_slot_prompt(cid):
    """槽位提示词：按目标出图引擎出稿（novelai=tag 轨 / tsubaki3=五槽自然语言 / seedream=用途+连贯描述）。
    不传 engine 时保持默认行为。craft 归 skills/image/production-image-models。"""
    b = request.get_json(force=True) or {}
    kind, slot = b.get("kind", ""), b.get("slot", "")
    engine = (b.get("engine") or "").strip()
    c = _CHARS.get(cid, {})
    prompt = build_slot_prompt(c, kind, slot, engine)
    _SLOT_PROMPTS[(cid, kind, slot)] = prompt
    _persist()
    return ok({"kind": kind, "slot": slot, "prompt": prompt, "mocked": True, "engine": engine or "default"})

@bp.get("/<cid>/slot-svgs")
def list_slot_svgs(cid):
    return ok([{"kind": k, "slot": s, "svg": v} for (cc, k, s), v in _SLOT_SVGS.items() if cc == cid])

@bp.post("/<cid>/slot-svg/generate")
def gen_slot_svg(cid):
    b = request.get_json(force=True) or {}
    kind, slot = b.get("kind", ""), b.get("slot", "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400">'
           f'<rect width="300" height="400" fill="#f7f7f7"/>'
           f'<text x="20" y="200" font-size="16">{cid} {kind}/{slot}</text></svg>')
    _SLOT_SVGS[(cid, kind, slot)] = svg
    _persist()
    return ok({"kind": kind, "slot": slot, "svg": svg, "mocked": True})

@bp.get("/constants")
def constants():
    return ok({"sections": SECTIONS, "attires": ATTIRES, "slots": SLOTS,
               "outfit_categories": OUTFIT_CATS, "dims": DIMS})

@bp.get("/<cid>/outfits")
def list_outfits(cid):
    return ok([o for o in _OUTFITS.values() if o["character_id"] == cid])

@bp.post("/<cid>/outfits")
def create_outfit(cid):
    b = request.get_json(force=True) or {}
    oid = _SEQ["outfit"]; _SEQ["outfit"] += 1
    row = {"id": oid, "character_id": cid, "name": b.get("name", "新服装"),
           "description": b.get("description", ""), "category": b.get("category", "top"),
           "cover_asset_id": None, "cover_path": "", "is_active": 0,
           "created_at": _now(), "updated_at": _now()}
    _OUTFITS[oid] = row
    _persist()
    return ok(row)

@bp.put("/<cid>/outfits/<int:oid>")
def update_outfit(cid, oid):
    b = request.get_json(force=True) or {}
    o = _OUTFITS.get(oid, {})
    for k in ["name", "description", "category", "cover_asset_id"]:
        if k in b:
            o[k] = b[k]
    o["updated_at"] = _now()
    _persist()
    return ok(o)

@bp.delete("/<cid>/outfits/<int:oid>")
def delete_outfit(cid, oid):
    _OUTFITS.pop(oid, None)
    _persist()
    return ok({"deleted": oid})

@bp.post("/<cid>/outfits/<int:oid>/activate")
def activate_outfit(cid, oid):
    for o in _OUTFITS.values():
        if o["character_id"] == cid:
            o["is_active"] = 1 if o["id"] == oid else 0
    _persist()
    return ok(_OUTFITS.get(oid, {}))

@bp.get("/<cid>/outfit-categories")
def list_cats(cid):
    return ok([{"category": c, "description": _OUTFIT_CATS_MAP.get((cid, c), "")} for c in OUTFIT_CATS])

@bp.put("/<cid>/outfit-categories")
def save_cat(cid):
    b = request.get_json(force=True) or {}
    _OUTFIT_CATS_MAP[(cid, b.get("category", ""))] = b.get("description", "")
    _persist()
    return ok({"category": b.get("category"), "description": b.get("description")})

@bp.get("/<cid>/doc")
def get_doc(cid):
    return ok(_DOCS.get(cid, {"doc_html": ""}))

@bp.put("/<cid>/doc")
def save_doc(cid):
    b = request.get_json(force=True) or {}
    _DOCS[cid] = {"doc_html": b.get("doc_html", "")}
    _persist()
    return ok(_DOCS[cid])

@bp.post("/<cid>/iterate")
def iterate(cid):
    b = request.get_json(force=True) or {}
    dim, ins = b.get("dimension", "identity"), b.get("instruction", "")
    c = _CHARS.get(cid, {})
    if dim in c and ins:
        c[dim] = (c.get(dim, "") + "；" + ins).strip("；")
    vno = _SEQ["version"]; _SEQ["version"] += 1
    v = {"id": vno, "version_no": vno, "dimension": dim, "instruction": ins,
         "note": "本地规则迭代", "frozen": 0, "created_at": _now(), "snapshot": dict(c)}
    _VERSIONS.setdefault(cid, []).append(v)
    _persist()
    return ok({"character": c, "version_no": vno, "changed": True,
               "issues": [], "checks": [], "dimension": dim, "mocked": True})

@bp.get("/<cid>/versions")
def list_versions(cid):
    return ok(_VERSIONS.get(cid, []))

@bp.post("/<cid>/rollback")
def rollback(cid):
    b = request.get_json(force=True) or {}
    vid = b.get("version_id")
    for v in _VERSIONS.get(cid, []):
        if v["id"] == vid:
            _CHARS[cid] = dict(v["snapshot"])
            _persist()
            return ok({"character": _CHARS[cid], "version_no": v["version_no"]})
    return ok({"character": _CHARS.get(cid, {})})

@bp.post("/<cid>/freeze")
def freeze(cid):
    vs = _VERSIONS.get(cid, [])
    if vs:
        vs[-1]["frozen"] = 1
    _persist()
    return ok({"frozen": True, "total": len(vs)})

@bp.get("/<cid>/pack")
def pack(cid):
    c = _CHARS.get(cid, {})
    return ok({"pack": c, "markdown": f"# {c.get('name','')} 设定\n\n" + "\n".join(
        [f"- {k}: {c.get(k,'')}" for k in DIMS]),
        "prompts": [{"kind": k, "slot": s, "prompt": p}
            for (cc, k, s), p in _SLOT_PROMPTS.items() if cc == cid]})

@bp.post("/<cid>/vision")
def vision(cid):
    return ok({"palette": [], "silhouette": "占位：待接VLM", "hairstyle": "",
               "outfit": "", "materials": "", "composition": "", "suggestions": "先用槽位提示词顶住"})

@bp.post("/<cid>/avatar")
def upload_avatar(cid):
    from pathlib import Path
    import uuid as _uuid
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    name = _uuid.uuid4().hex + (Path(f.filename or "").suffix[:10] or ".png")
    f.save(root / name)
    if cid in _CHARS:
        _CHARS[cid]["avatar_path"] = name
        _persist()
    return ok({"path": name, "url": f"/api/images/{name}"})

@bp.post("/<cid>/assets/file")
def upload_asset_file(cid):
    from pathlib import Path
    import uuid as _uuid
    f = request.files.get("file")
    kind = request.form.get("kind", "head_dressed")
    slot = request.form.get("slot", "front")
    if not f:
        return jsonify({"code": 4001, "msg": "no file"}), 400
    root = Path(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    name = _uuid.uuid4().hex + (Path(f.filename or "").suffix[:10] or ".png")
    f.save(root / name)
    aid = _SEQ["asset"]; _SEQ["asset"] += 1
    row = {"id": aid, "character_id": cid, "kind": kind, "slot": slot,
           "path": name, "url": f"/api/images/{name}", "note": "",
           "created_at": _now(), "updated_at": _now()}
    _ASSETS[aid] = row
    _persist()
    return ok(row)
