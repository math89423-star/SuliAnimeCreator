"""art 蓝图：美术工具页数据化。7个工具已原生化为前端组件（frontend/src/components/tools/），此处只给索引。
另含出图引擎画像（image-models）：三家生产引擎的提示词形态/质量标签/纪律，craft 归
skills/image/production-image-models（本文件只给机器可读真源，不重写规范）。
"""
from flask import Blueprint, jsonify, request

bp = Blueprint("art", __name__, url_prefix="/api/v1/art")

TOOLS = [
    {"id": "composition-camera", "name": "构图机位", "desc": "220卡30页：景别/机位/透视/构图，高级镜头+拆解"},
    {"id": "costume", "name": "服装穿搭", "desc": "18流派198单品+搭配台，S1-3b选型用"},
    {"id": "palette", "name": "配色", "desc": "15系764色+和色465，主辅点三层取色"},
    {"id": "flowers", "name": "花语", "desc": "101花三层花语+booru tag"},
    {"id": "naming", "name": "取名", "desc": "75招+91撞名自检"},
    {"id": "shot-grammar", "name": "镜头语法", "desc": "运镜31/机位21/景别7，拼prompt"},
    {"id": "nsfw-guide", "name": "分级", "desc": "九槽+模型分流+成年锚"},
]

# 出图引擎画像（真源）：form=提示词形态；quality_tags=模型自带质量标签（写了就重复，别手写）
IMAGE_MODELS = [
    {
        "key": "novelai", "label": "NovelAI Diffusion（V5 / V4.5 / V4 / Anime V3）",
        "form": "tags",
        "quality_tags": ", very aesthetic, masterpiece, no text",
        "weight_syntax": "{ } 强化 / [ ] 弱化（各 ×1.05）；数值 1.5::x :: 仅 V4+",
        "hint": "逗号 tag 为主，可夹短句；质量标签走开关不手写；一次只加 1-2 个关键权重",
        "negative_hint": "每镜现配、短、只点名真实风险：extra digits, cropped head, child, minor, underage, loli, shota, aged_down",
        "notes": "多角色用 Character Prompts（V4≤6 / V5≤22）；Precise Reference 分角色/风格且多张会融合；V4+ 约 512 T5 token",
        "ref": "skills/image/production-image-models/references/novelai.md",
    },
    {
        "key": "tsubaki3", "label": "PixAI Tsubaki.3",
        "form": "natural",
        "quality_tags": "",
        "weight_syntax": "无（用词的顺序与具体度控制权重）",
        "hint": "五槽顺序：主体 → 细节 → 构图机位 → 光 → 风格；介词动词比形容词值钱；禁 tag 堆",
        "negative_hint": "自然语言模型无负向栏；要排除的东西用正面写法或换参考图",
        "notes": "可中文/日文/韩文直写，专有名词与技术词留英文；参考图分 base image 与 reference slot 两通道；图上文字写内容+位置+职责",
        "ref": "skills/image/production-image-models/references/tsubaki3.md",
    },
    {
        "key": "seedream", "label": "Seedream（火山方舟 doubao-seedream 4.0/4.5/5.0）",
        "form": "natural",
        "quality_tags": "",
        "weight_syntax": "无",
        "hint": "一句用途开头 + 主体/行为/环境连贯短句 + 风格/色彩/光影/构图；避免碎片堆叠",
        "negative_hint": "无负向栏；用正向描述与参考图约束",
        "notes": "编辑用增加/删除/替换/修改 + 箭头线框涂鸦定位；参考图写“参考对象 + 生成画面”两部分；组图用“一系列/一套/组图”或给张数；限流约 500 IPM",
        "ref": "skills/image/production-image-models/references/seedream.md",
    },
]


def ok(data):
    return jsonify({"code": 0, "data": data})


@bp.get("/tools")
def tools():
    return ok(TOOLS)


@bp.get("/image-models")
def image_models():
    return ok(IMAGE_MODELS)


# ─────────────────────────────────────────────────────────────────────────────
# 单图创作（art plan）：方案 → 直投 L-Port → L-Port 发散/翻译/精修 → 提示词回传
#
# 与剧本创作同构：Suli 起草方案（意图文本 + 目标引擎 + 参考图），直投 L-Port 收件箱
# suli_packages/<pkg_id>/（包型 art_plan）；L-Port 侧跑 intent_divergence →
# intent_blueprint → blueprint_to_<engine> 后调 push-art-prompts-to-suli 回传，
# 本文件 /prompts/import 收口逐引擎落进方案 prompts（当前版本语义：重传整条覆盖）。
# 数据：backend/data/art_db.json。
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path as _Path
from io import BytesIO as _BytesIO
import json as _json
import time as _time
import random as _random
import zipfile as _zipfile
import urllib.parse as _urlparse

from ..services.disk_store import load as _load_store, save as _save_store

_ART_DB = _load_store("art_db.json", {"plans": []})
_ENGINE_CAP = 20000  # 单引擎提示词字段上限（防超长灌库）
_ENGINES = ("novelai", "tsubaki3", "seedream", "anima", "gpt_image", "flux", "sdxl", "pony", "cloud")
_UPLOADS = _Path(__file__).resolve().parents[2] / "data" / "uploads"


def _apersist():
    _save_store("art_db.json", _ART_DB)


def _anow():
    return _time.strftime("%Y-%m-%dT%H:%M:%S")


def _plan(pid):
    for p in _ART_DB.get("plans") or []:
        if p.get("id") == pid:
            return p
    return None


def _norm_engines(raw):
    out = []
    for x in (raw if isinstance(raw, (list, tuple)) else []):
        k = str(x or "").strip().lower()
        if k in _ENGINES and k not in out:
            out.append(k)
    return out


def _norm_refs(raw):
    """参考图归一：[{name, path, url}]，最多 6 张（对齐 L-Port ref_images 上限）。

    path 统一成相对 backend 的 uploads 路径（直投打包按它找文件）；url 缺省按 basename
    补 /api/images/<name>，前端缩略图直接用——agent 只给 path 的旧写法也能看图。
    """
    out = []
    for it in (raw if isinstance(raw, (list, tuple)) else []):
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "").strip()[:200]
        path = str(it.get("path") or "").strip()[:500]
        url = str(it.get("url") or "").strip()[:500]
        if not (name or path):
            continue
        base = (path or name).replace("\\", "/").split("/")[-1]
        if not name:
            name = base
        if not path or "/" not in path:
            path = "data/uploads/%s" % base
        if not url:
            url = "/api/images/%s" % _urlparse.quote(base)
        out.append({"name": name, "path": path, "url": url})
    return out[:6]


def _ref_file(r):
    """参考图落盘位置：path 原样 → data/uploads/<basename> 兜底。"""
    base = _Path(str(r.get("path") or r.get("name") or "")).name
    for cand in (str(r.get("path") or ""), str(_UPLOADS / base) if base else ""):
        if not cand:
            continue
        p = _Path(cand)
        if p.is_file():
            return p
    return None


def _migrate_refs():
    """老数据兼容：只有 name/path、没有 url 的参考图，进内存时补齐（缩略图与直投打包都要用）。"""
    dirty = False
    for p in _ART_DB.get("plans") or []:
        raw = p.get("ref_images")
        if not isinstance(raw, list):
            continue
        fixed = _norm_refs(raw)
        if fixed != raw:
            p["ref_images"] = fixed
            dirty = True
    if dirty:
        _apersist()


_migrate_refs()


def _trim(v):
    return str(v or "")[:_ENGINE_CAP]


def _plan_projection(p):
    """列表/详情投影：列表不拉全量提示词正文（只给计数），详情才带 prompts。"""
    pr = p.get("prompts") or {}
    return {
        "id": p.get("id"), "title": p.get("title") or "",
        "intent_text": p.get("intent_text") or "",
        "engines": p.get("engines") or [],
        "ref_images": p.get("ref_images") or [],
        "note": p.get("note") or "",
        "status": p.get("status") or "draft",
        "push": p.get("push") or None,
        "prompt_engines": sorted(pr.keys()),
        "prompt_count": len(pr),
        "created_at": p.get("created_at"), "updated_at": p.get("updated_at"),
    }


@bp.get("/plans")
def list_plans():
    rows = sorted((_ART_DB.get("plans") or []), key=lambda p: p.get("updated_at") or "", reverse=True)
    return ok([_plan_projection(p) for p in rows])


@bp.get("/plans/<plan_id>")
def get_plan(plan_id):
    p = _plan(plan_id)
    if p is None:
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % plan_id}), 404
    d = _plan_projection(p)
    d["prompts"] = p.get("prompts") or {}
    d["blueprint"] = p.get("blueprint") or None
    return ok(d)


@bp.post("/plans")
def upsert_plan():
    """建/改方案。agent 与主人讨论出的方案也调这里落库（brief 里点名本接口）。

    body: {id?, title?, intent_text?, engines?, ref_images?, note?}
    """
    b = request.get_json(force=True, silent=True) or {}
    pid = str(b.get("id") or "").strip()
    now = _anow()
    p = _plan(pid) if pid else None
    if p is None:
        pid = pid or ("AP-%s-%04d" % (_time.strftime("%Y%m%d%H%M%S"), _random.randint(0, 9999)))
        p = {"id": pid, "created_at": now, "prompts": {}}
        _ART_DB.setdefault("plans", []).append(p)
    if "title" in b:
        p["title"] = str(b.get("title") or "").strip()[:200]
    if "intent_text" in b:
        p["intent_text"] = _trim(b.get("intent_text"))
    if "engines" in b:
        p["engines"] = _norm_engines(b.get("engines"))
    if "ref_images" in b:
        p["ref_images"] = _norm_refs(b.get("ref_images"))
    if "note" in b:
        p["note"] = _trim(b.get("note"))
    p["updated_at"] = now
    p.setdefault("status", "draft")
    _apersist()
    return ok(_plan_projection(p))


@bp.delete("/plans/<plan_id>")
def delete_plan(plan_id):
    rows = _ART_DB.get("plans") or []
    keep = [p for p in rows if p.get("id") != plan_id]
    if len(keep) == len(rows):
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % plan_id}), 404
    _ART_DB["plans"] = keep
    _apersist()
    return ok({"deleted": plan_id})


def _inbox_root():
    """L-Port 收件箱根：复用投流/导演的共享挂载（容器 /lport-lib）。"""
    try:
        from .traffic import _lport_dirs
        return _lport_dirs()
    except Exception:
        return None


@bp.post("/push-lport")
def push_lport():
    """单图方案直投 L-Port：写收件箱 suli_packages/<pkg_id>/（包型 art_plan）。

    body: {plan_id*} → {package_id, pkg_dir, engines, ref_count, hint}
    """
    b = request.get_json(force=True, silent=True) or {}
    pid = str(b.get("plan_id") or "").strip()
    if not pid:
        return jsonify({"code": 4001, "msg": "缺字段: plan_id"}), 400
    p = _plan(pid)
    if p is None:
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % pid}), 404
    if not (p.get("intent_text") or "").strip():
        return jsonify({"code": 4002, "msg": "方案还没有意图文本（intent_text）：先与 agent 讨论出方案再直投"}), 400
    engines = p.get("engines") or []
    if not engines:
        return jsonify({"code": 4002, "msg": "方案没有选目标引擎（engines）"}), 400

    root = _inbox_root()
    if root is None:
        return jsonify({"code": 4004,
                        "msg": "L-Port 素材库未挂载（/lport-lib 缺失）：先起 L-Port"}), 400

    pkg_id = "PKG-ART-%s-%04d" % (_time.strftime("%Y%m%d%H%M%S"), _random.randint(0, 9999))
    art_plan = {
        "package_id": pkg_id, "kind": "art_plan",
        "plan_id": pid, "title": p.get("title") or "",
        "intent_text": p.get("intent_text") or "",
        "engines": engines,
        "reference_images": [r.get("name") for r in (p.get("ref_images") or [])],
        "user_image_instruction": p.get("note") or "",
        "note": p.get("note") or "",
        "created_at": _anow(),
    }
    manifest = {
        "package_id": pkg_id, "kind": "art_plan", "version": 1,
        "source": "SuliAnimeCreator", "plan_id": pid,
        "engines": engines,
        "files": ["art_plan.json", "manifest.json", "refs.json"],
        "direction": "单图创作方案：意图发散 → 15 维蓝图 → 各引擎提示词（方向/引擎由 Suli 定，L-Port 只管发散翻译精修）",
        "hint": "L-Port 侧载入 art_plan.json 跑 intent_divergence → intent_blueprint → blueprint_to_<engine>，"
                "完成后 POST /api/pipeline/push-art-prompts-to-suli 回传（plan_id=%s）" % pid,
    }
    refs = p.get("ref_images") or []
    buf = _BytesIO()
    with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as z:
        z.writestr("art_plan.json", _json.dumps(art_plan, ensure_ascii=False, indent=2))
        z.writestr("manifest.json", _json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("refs.json", _json.dumps(refs, ensure_ascii=False, indent=2))
        for r in refs:
            src = _ref_file(r)
            if src is None:
                continue
            try:
                z.write(str(src), "ref_images/%s" % (r.get("name") or src.name))
            except OSError:
                continue

    pkgdir = root / "suli_packages" / pkg_id
    try:
        pkgdir.mkdir(parents=True, exist_ok=True)
        (pkgdir / ("%s.zip" % pkg_id)).write_bytes(buf.getvalue())
        (pkgdir / "manifest.json").write_text(
            _json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (pkgdir / "art_plan.json").write_text(
            _json.dumps(art_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        return jsonify({"code": 4005, "msg": "写 L-Port 收件箱失败：%s" % e}), 500

    p["push"] = {"package_id": pkg_id, "at": _anow(), "pkg_dir": str(pkgdir), "engines": engines}
    p["status"] = "pushed"
    p["updated_at"] = _anow()
    _apersist()
    return ok({
        "package_id": pkg_id, "plan_id": pid, "pkg_dir": str(pkgdir),
        "engines": engines, "ref_count": len(refs),
        "hint": "已落 L-Port 收件箱 suli_packages/%s（art_plan.json）：L-Port 侧跑发散翻译精修后调 "
                "push-art-prompts-to-suli 回传（plan_id=%s），本页刷新即见各引擎提示词。" % (pkg_id, pid),
    })


@bp.post("/prompts/import")
def prompts_import():
    """单图提示词回传收口（L-Port 发散/翻译/精修产物回流；当前版本语义：重传整条覆盖）。

    body: {plan_id? | package_id?, source?, engines: {<engine>: {positive*, negative?,
           params?, note?}}, blueprint?}
    → {plan_id, updated: [...], skipped: n, source, package_id}
    """
    b = request.get_json(force=True, silent=True) or {}
    pid = str(b.get("plan_id") or "").strip()
    pkg = str(b.get("package_id") or "").strip()
    p = _plan(pid) if pid else None
    if p is None and pkg:
        for row in (_ART_DB.get("plans") or []):
            if ((row.get("push") or {}).get("package_id")) == pkg:
                p = row
                break
    if p is None:
        return jsonify({"code": 4003,
                        "msg": "未找到方案：plan_id/package_id 都对不上（不新建方案，防假回执）"}), 404

    raw = b.get("engines")
    if not isinstance(raw, dict) or not raw:
        return jsonify({"code": 4001, "msg": "缺字段: engines（{<engine>: {positive...}}）"}), 400

    source = (str(b.get("source") or "lport").strip()[:80]) or "lport"
    now = _anow()
    updated, skipped = [], []
    prompts = p.setdefault("prompts", {})
    for eng, val in raw.items():
        key = str(eng or "").strip().lower()
        item = val if isinstance(val, dict) else {}
        positive = _trim(item.get("positive") or item.get("prompt") or "")
        negative = _trim(item.get("negative") or "")
        if not (positive or negative):
            skipped.append(key or "(空引擎名)")
            continue  # 空正文不落，防假回执
        prompts[key] = {
            "positive": positive, "negative": negative,
            "params": item.get("params") if isinstance(item.get("params"), dict) else {},
            "note": _trim(item.get("note") or "")[:2000],
            "source": source,
            "package_id": pkg or (p.get("push") or {}).get("package_id") or "",
            "at": now,
        }
        updated.append(key)
    if isinstance(b.get("blueprint"), dict):
        p["blueprint"] = b.get("blueprint")
    if updated:
        p["status"] = "returned"
    p["updated_at"] = now
    _apersist()
    return ok({
        "plan_id": p.get("id"), "updated": updated, "skipped": len(skipped),
        "skipped_engines": skipped, "source": source,
        "package_id": pkg or (p.get("push") or {}).get("package_id") or "",
    })


