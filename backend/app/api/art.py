"""art 蓝图：美术工具页数据化。7个工具已原生化为前端组件（frontend/src/components/tools/），此处只给索引。
另含出图引擎画像（image-models）：四家生产引擎的提示词形态/质量标签/纪律，craft 归
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
    {
        "key": "mango3", "label": "Mango 3（mage 平台 mango-v3）",
        "form": "natural",
        "quality_tags": "",
        "weight_syntax": "无",
        "hint": "四件套顺序：主体 → 场景 → 光 → 取景（景别+镜头）；逗号串联的连贯短句，主体在最前；光与取景必写",
        "negative_hint": "Mango 无负向栏：不输出负向段；要排除元素用正向改写，或换有负向栏的引擎",
        "notes": "@handle 挂载角色/参考图（Mango 3/3S/2 支持，共享 10 张额度；一代不支持；凭空造的 handle 会被拒）；无 LoRA/ControlNet；分辨率 1K·2K（3S 3K / v2 4K）；比例 9 档（默认 4:5）；seed 可复现",
        "ref": "skills/image/production-image-models/references/mango3.md",
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
import datetime as _dt
import random as _random
import zipfile as _zipfile
import urllib.parse as _urlparse

from ..services.disk_store import load as _load_store, save as _save_store

_ART_DB = _load_store("art_db.json", {"plans": []})
_ENGINE_CAP = 20000  # 单引擎提示词字段上限（防超长灌库）
_ENGINES = ("novelai", "tsubaki3", "seedream", "mango3", "anima", "gpt_image", "flux", "sdxl", "pony", "cloud")
_UPLOADS = _Path(__file__).resolve().parents[2] / "data" / "uploads"
_SCRIPT_PANEL_CAP = 2000   # 单格剧本正文上限
_SCRIPT_MAX_PANELS = 200   # 单本剧本格数上限


def _apersist():
    _save_store("art_db.json", _ART_DB)


def _anow():
    """带时区偏移的 ISO 时间（容器跑 UTC，不带偏移的话前端会当本地时间解析，差 8 小时）。"""
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


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


# 水位档（与 L-Port comic_page_diverge、skills/video/nsfw-directing 同一套四档）
# 空串 = 常规镜（不标档位就是常规）。
_TIERS = ("tease", "undress", "explicit", "closeup")
# 衣物档 L0-L4：L0 完整 → L4 全裸（跨格只许收紧，不许倒退）
_CLOTHING = ("L0", "L1", "L2", "L3", "L4")
_TIER_CN = {"tease": "氛围暗示", "undress": "半露", "explicit": "直白", "closeup": "特写"}


def _norm_tier(raw):
    """水位档归一：空串（常规）或四档之一。旧写法 nsfw/sfw 折到四档。"""
    k = str(raw or "").strip().lower()
    if not k:
        return ""
    if k == "nsfw":
        return "explicit"
    if k == "sfw":
        return "tease"
    return k if k in _TIERS else ""


def _norm_clothing(raw):
    """衣物档归一：空串（未定）或 L0-L4（也接受 0-4 数字写法）。"""
    k = str(raw or "").strip().upper()
    if not k:
        return ""
    if k.isdigit():
        k = "L" + k
    return k if k in _CLOTHING else ""


def _tier_line(tier, clothing):
    """档位 → 意图文本里的水位说明（模型只看文本，档位必须写进去）。"""
    bits = []
    if tier:
        bits.append("【本图水位】%s（%s）" % (tier, _TIER_CN.get(tier, tier)))
    if clothing:
        bits.append("【衣物档】%s" % clothing)
    return "\n".join(bits)


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


_PAGE_OUTLINE_CAP = 12000  # 大纲快照上限（单页带整份大纲会撑爆提示词）


def _norm_page(raw):
    """漫画页上下文归一：集号 / 页序 / 页内格序 / 上一格方案 / 大纲快照 / 本格成图。

    存在 plan.page 里。漫画一页由若干格组成，**一格 = 一个方案**（一次直投 = 一格出图）：
    - index：页序（第几页）
    - panel_index：页内格序（第几格）
    - prev_plan_id：上一格的方案（页内上一格；页内第一格则指上一页的末格）
    - outline_text：大纲快照（整页共享）
    - image：本格成图
    下一格建页时把上一格的 image 自动带进参考图，格与格的连续性就靠它。
    """
    if not isinstance(raw, dict):
        return None
    eid = str(raw.get("episode_id") or "").strip()[:64]
    prev = str(raw.get("prev_plan_id") or "").strip()[:64]
    outline = str(raw.get("outline_text") or "")[:_PAGE_OUTLINE_CAP]
    try:
        idx = int(raw.get("index") or 0)
    except (TypeError, ValueError):
        idx = 0
    try:
        pidx = int(raw.get("panel_index") or 0)
    except (TypeError, ValueError):
        pidx = 0
    img = None
    r = raw.get("image")
    if isinstance(r, dict):
        name = str(r.get("name") or "").strip()[:200]
        path = str(r.get("path") or "").strip()[:500]
        url = str(r.get("url") or "").strip()[:500]
        if name or path:
            base = (path or name).replace("\\", "/").split("/")[-1]
            if not name:
                name = base
            if not path or "/" not in path:
                path = "data/uploads/%s" % base
            if not url:
                url = "/api/images/%s" % _urlparse.quote(base)
            img = {"name": name, "path": path, "url": url}
    if not (eid or idx or pidx or prev or outline or img):
        return None
    return {"episode_id": eid, "index": idx if idx > 0 else 0, "panel_index": pidx if pidx > 0 else 0,
            "prev_plan_id": prev, "outline_text": outline, "image": img}


_migrate_refs()


def _trim(v):
    return str(v or "")[:_ENGINE_CAP]


def _plan_snapshot(p):
    """方案状态快照（变更 diff 的对照基准）：可改字段的归一化值。"""
    return {
        "title": p.get("title") or "",
        "intent_text": p.get("intent_text") or "",
        "engines": list(p.get("engines") or []),
        "ref_images": [
            {"name": r.get("name") or "", "path": r.get("path") or "", "url": r.get("url") or ""}
            for r in (p.get("ref_images") or [])
            if isinstance(r, dict)
        ],
        "note": p.get("note") or "",
        "tier": p.get("tier") or "",
        "clothing_level": p.get("clothing_level") or "",
    }


def _plan_projection(p):
    """列表/详情投影：列表不拉全量提示词正文（只给计数），详情才带 prompts。"""
    pr = p.get("prompts") or {}
    return {
        "id": p.get("id"), "title": p.get("title") or "",
        "intent_text": p.get("intent_text") or "",
        "engines": p.get("engines") or [],
        "ref_images": p.get("ref_images") or [],
        "note": p.get("note") or "",
        "tier": p.get("tier") or "",
        "clothing_level": p.get("clothing_level") or "",
        "status": p.get("status") or "draft",
        "push": p.get("push") or None,
        "page": p.get("page") or None,
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
    d["prev"] = p.get("prev") or None
    d["prev_at"] = p.get("prev_at") or None
    return ok(d)


@bp.get("/plans/<plan_id>/status")
def plan_status(plan_id):
    """轻量状态（回传等待轮询用）：只给状态/引擎清单/投递信息，不带提示词正文。"""
    p = _plan(plan_id)
    if p is None:
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % plan_id}), 404
    pr = p.get("prompts") or {}
    push = p.get("push") or {}
    return ok({
        "id": p.get("id"),
        "status": p.get("status") or "draft",
        "prompt_engines": sorted(pr.keys()),
        "prompt_count": len(pr),
        "prompt_at": max([str((v or {}).get("at") or "") for v in pr.values()] or [""]),
        "package_id": push.get("package_id") or "",
        "pushed_at": push.get("at") or "",
        "updated_at": p.get("updated_at"),
    })


@bp.post("/plans")
def upsert_plan():
    """建/改方案。agent 与主人讨论出的方案也调这里落库（brief 里点名本接口）。

    body: {id?, title?, intent_text?, engines?, ref_images?, note?, source?}
    source=ui 表示是页面上主人自己改的（不带待审快照）；其余来源（agent 写盘）留改前快照 prev。
    """
    b = request.get_json(force=True, silent=True) or {}
    pid = str(b.get("id") or "").strip()
    now = _anow()
    p = _plan(pid) if pid else None
    if p is None:
        pid = pid or ("AP-%s-%04d" % (_time.strftime("%Y%m%d%H%M%S"), _random.randint(0, 9999)))
        p = {"id": pid, "created_at": now, "prompts": {}}
        _ART_DB.setdefault("plans", []).append(p)
    before = _plan_snapshot(p)
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
    if "tier" in b:
        p["tier"] = _norm_tier(b.get("tier"))
    if "clothing_level" in b:
        p["clothing_level"] = _norm_clothing(b.get("clothing_level"))
    if "page" in b:
        p["page"] = _norm_page(b.get("page"))
    # 变更留痕：改盘方不是页面自己时留一份改前快照（前端据此出 diff 卡片）。
    # source=ui 是主人在页面上自己改的——人已经看过了，清掉待审快照。
    if str(b.get("source") or "").strip().lower() == "ui":
        p.pop("prev", None)
        p.pop("prev_at", None)
    elif _plan_snapshot(p) != before:
        p["prev"] = before
        p["prev_at"] = now
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


@bp.get("/comics")
def list_comics():
    """漫画格序列（页条/格条用）：带 page 上下文的方案，按页序+格序升序。

    query: episode_id（给了就只给这一集的格；不给则给全部漫画格）
    """
    eid = str(request.args.get("episode_id") or "").strip()
    rows = []
    for p in (_ART_DB.get("plans") or []):
        pg = p.get("page") or {}
        if not pg:
            continue
        if eid and pg.get("episode_id") != eid:
            continue
        rows.append(_plan_projection(p))
    rows.sort(key=lambda r: (
        ((r.get("page") or {}).get("index") or 0),
        ((r.get("page") or {}).get("panel_index") or 0),
        r.get("updated_at") or "",
    ))
    return ok(rows)


@bp.post("/plans/<plan_id>/image")
def upload_plan_image(plan_id):
    """挂本页成图（漫画页）：传图 → 落 uploads → 写进方案的 page.image。

    下一建页时前端把上一页这张图自动带进参考图，页与页之间人物/服装/画风才接得上。
    """
    p = _plan(plan_id)
    if p is None:
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % plan_id}), 404
    f = request.files.get("file")
    if not f:
        return jsonify({"code": 4001, "msg": "缺文件: file"}), 400
    from .uploads import save_upload
    try:
        row = save_upload(f)
    except ValueError as e:
        return jsonify({"code": 4001, "msg": str(e)}), 400
    pg = _norm_page(p.get("page") or {}) or {"episode_id": "", "index": 0, "prev_plan_id": "",
                                           "outline_text": "", "image": None}
    pg["image"] = {"name": row["path"], "path": "data/uploads/%s" % row["path"], "url": row["url"]}
    p["page"] = pg
    p["updated_at"] = _anow()
    _apersist()
    return ok({"plan_id": plan_id, "image": pg["image"], "bytes": row.get("bytes")})


@bp.delete("/plans/<plan_id>/image")
def delete_plan_image(plan_id):
    """撤掉本页成图（漫画页）：只清 page.image，文件仍留在 uploads。"""
    p = _plan(plan_id)
    if p is None:
        return jsonify({"code": 4003, "msg": "方案不存在：%s" % plan_id}), 404
    pg = p.get("page") or {}
    pg["image"] = None
    p["page"] = pg
    p["updated_at"] = _anow()
    _apersist()
    return ok({"plan_id": plan_id, "image": None})


# ─────────────────────────────────────────────────────────────────────────────
# 漫画剧本：一本剧本 → 拆格 → 每格一个方案 → 直投 L-Port → 回传提示词
#
# 流程是这个顺序，不是"直接写方案意图"：
#   剧本（页/格分条） → 拆格（一格 = 一个方案，带页序/格序/上一格链）
#   → 每格直投 L-Port → L-Port 发散/翻译/精修 → 提示词回传进方案。
# 剧本存 art_db.json 的 comics 段（按集号一份）：{episode_id, title, panels[], updated_at}
# ─────────────────────────────────────────────────────────────────────────────


def _norm_script_panel(raw):
    """一格剧本条目归一：{page, panel, text, dialogue, camera, note, tier, clothing_level}。"""
    if not isinstance(raw, dict):
        return None
    try:
        page = int(raw.get("page") or 0)
    except (TypeError, ValueError):
        page = 0
    try:
        panel = int(raw.get("panel") or 0)
    except (TypeError, ValueError):
        panel = 0
    text = str(raw.get("text") or "").strip()[:_SCRIPT_PANEL_CAP]
    dialogue = str(raw.get("dialogue") or "").strip()[:_SCRIPT_PANEL_CAP]
    camera = str(raw.get("camera") or "").strip()[:200]
    note = str(raw.get("note") or "").strip()[:2000]
    tier = _norm_tier(raw.get("tier"))
    clothing = _norm_clothing(raw.get("clothing_level"))
    if page <= 0:
        page = 1
    if panel <= 0:
        panel = 1
    if not (text or dialogue or camera or note or tier or clothing):
        return None
    return {"page": page, "panel": panel, "text": text, "dialogue": dialogue,
            "camera": camera, "note": note, "tier": tier, "clothing_level": clothing}


def _script_of(eid):
    return (_ART_DB.get("comics") or {}).get(eid)


def _save_script(eid, title, panels, meta=None):
    """存一本漫画剧本（按集号一份）。

    meta：本本元信息 —— premise（前提）/ characters（角色设定）/ style_hint（画风）/ tier（默认水位）。
    """
    meta = meta if isinstance(meta, dict) else {}
    comics = _ART_DB.setdefault("comics", {})
    comics[eid] = {
        "episode_id": eid,
        "title": (title or "").strip()[:200] or ("%s 漫画剧本" % eid),
        "premise": str(meta.get("premise") or "").strip()[:2000],
        "characters": str(meta.get("characters") or "").strip()[:4000],
        "style_hint": str(meta.get("style_hint") or "").strip()[:1000],
        "tier": _norm_tier(meta.get("tier")),
        "panels": panels,
        "updated_at": _anow(),
    }
    _apersist()
    return comics[eid]


def _panel_intent(p):
    """一格剧本 → 方案意图文本（画面/台词/景别/水位，页序由直投时统一补）。"""
    bits = []
    if p.get("text"):
        bits.append("画面：%s" % p["text"])
    if p.get("dialogue"):
        bits.append("台词：%s" % p["dialogue"])
    if p.get("camera"):
        bits.append("景别/运镜：%s" % p["camera"])
    if p.get("tier") or p.get("clothing_level"):
        bits.append(_tier_line(p.get("tier"), p.get("clothing_level")))
    if p.get("note"):
        bits.append("备注：%s" % p["note"])
    return "\n".join(bits)[:_ENGINE_CAP]


def _outline_of(eid):
    """读本集大纲（从 scriptboard 的落盘里取，不跨蓝图直接读文件）。"""
    try:
        from .scriptboard import _EPS
        return (_EPS.get(eid) or {}).get("outline_md") or ""
    except Exception:
        return ""


def _outline_premise(md):
    """从大纲取「方向一句话」（没有就空）。"""
    lines = (md or "").splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("#") and "方向" in s:
            for nx in lines[i + 1:]:
                t = nx.strip()
                if t:
                    return t[:2000]
            return ""
    return ""


def _outline_to_panels(md, per_page=4):
    """从大纲拆成漫画格：优先取大纲里的分镜表（一行 = 一格），取不到就整篇兜成一格。

    分镜表列：镜号 | 内容 | 时长 | 运镜 | 备注 → 格：内容 / 运镜 / 备注。
    """
    rows = []
    for ln in (md or "").splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if any("镜号" in c or set(c) <= set("-: ") for c in cells):
            continue
        content = cells[1] if len(cells) > 1 else ""
        if not content:
            continue
        camera = cells[3] if len(cells) > 3 else ""
        note = cells[4] if len(cells) > 4 else ""
        rows.append({"text": content, "camera": camera, "note": note})
    if not rows:
        body = (md or "").strip()
        if not body:
            return []
        rows = [{"text": body[:_SCRIPT_PANEL_CAP], "camera": "", "note": ""}]
    per_page = max(1, min(8, int(per_page or 4)))
    out = []
    for i, r in enumerate(rows):
        out.append({
            "page": i // per_page + 1,
            "panel": i % per_page + 1,
            "text": r["text"],
            "dialogue": "",
            "camera": r["camera"],
            "note": r["note"],
            "tier": "",
            "clothing_level": "",
        })
    return out[:_SCRIPT_MAX_PANELS]


@bp.get("/comic-script")
def get_comic_script():
    """读本集的漫画剧本（页/格分条 + 本本元信息）。"""
    eid = str(request.args.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    sc = _script_of(eid)
    if sc is None:
        return ok({"episode_id": eid, "title": "", "premise": "", "characters": "",
                   "style_hint": "", "tier": "", "panels": [], "updated_at": "", "exists": False})
    d = dict(sc)
    d["exists"] = True
    return ok(d)


@bp.delete("/comic-script")
def delete_comic_script():
    """删掉本集的漫画剧本（含元信息与格条目）。"""
    eid = str(request.args.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    comics = _ART_DB.get("comics") or {}
    existed = comics.pop(eid, None) is not None
    if existed:
        _apersist()
    return ok({"episode_id": eid, "deleted": existed})


@bp.post("/comic-script")
def save_comic_script():
    """存本集的漫画剧本（整体覆盖）。

    body: {episode_id*, title?, premise?, characters?, style_hint?, tier?,
           panels*: [{page, panel, text, dialogue, camera, note, tier, clothing_level}]}
    """
    b = request.get_json(force=True, silent=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    raw = b.get("panels")
    if not isinstance(raw, list):
        return jsonify({"code": 4001, "msg": "panels 须为数组"}), 400
    panels = []
    for it in raw[:_SCRIPT_MAX_PANELS]:
        p = _norm_script_panel(it)
        if p:
            panels.append(p)
    panels.sort(key=lambda x: (x["page"], x["panel"]))
    d = _save_script(eid, b.get("title"), panels, b)
    return ok({"episode_id": eid, "title": d["title"], "panel_count": len(panels),
               "tier": d["tier"], "updated_at": d["updated_at"]})


@bp.post("/comic-script/from-outline")
def comic_script_from_outline():
    """从本集大纲转成漫画剧本（冷启动用；转完再手工改）。

    body: {episode_id*, per_page?} → {panel_count, panels}
    """
    b = request.get_json(force=True, silent=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    md = _outline_of(eid)
    if not md.strip():
        return jsonify({"code": 4004, "msg": "本集没有大纲：先在剧本分镜页出大纲"}), 400
    panels = _outline_to_panels(md, b.get("per_page") or 4)
    if not panels:
        return jsonify({"code": 4004, "msg": "大纲里没解析出分镜"}), 400
    old = _script_of(eid) or {}
    meta = {
        "premise": b.get("premise") if b.get("premise") is not None else (_outline_premise(md) or old.get("premise") or ""),
        "characters": b.get("characters") if b.get("characters") is not None else (old.get("characters") or ""),
        "style_hint": b.get("style_hint") if b.get("style_hint") is not None else (old.get("style_hint") or ""),
        "tier": b.get("tier") if b.get("tier") is not None else (old.get("tier") or ""),
    }
    d = _save_script(eid, b.get("title"), panels, meta)
    return ok({"episode_id": eid, "title": d["title"], "panel_count": len(panels),
               "premise": d["premise"], "tier": d["tier"], "updated_at": d["updated_at"]})


@bp.post("/comic-script/split")
def comic_script_split():
    """拆格：按剧本一条 = 一个方案（页序/格序/上一格链自动排好）。

    幂等：同一 (页,格) 已有方案就跳过（只补上下文，不重建）。
    body: {episode_id*, engines?} → {created, skipped, plan_ids, panels}
    """
    b = request.get_json(force=True, silent=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    sc = _script_of(eid)
    if not sc or not sc.get("panels"):
        return jsonify({"code": 4004, "msg": "本集没有漫画剧本：先写剧本或从大纲转"}), 400
    engines = _norm_engines(b.get("engines")) or ["novelai", "tsubaki3", "seedream"]
    panels = sorted(sc.get("panels") or [], key=lambda x: (x.get("page") or 0, x.get("panel") or 0))
    outline = _outline_of(eid)

    existing = {}
    for p in (_ART_DB.get("plans") or []):
        pg = p.get("page") or {}
        if pg.get("episode_id") == eid:
            existing[(int(pg.get("index") or 0), int(pg.get("panel_index") or 0))] = p

    now = _anow()
    created, skipped, refreshed, plan_ids = [], [], [], []
    prev_plan_id = ""
    book_tier = _norm_tier(sc.get("tier"))
    for it in panels:
        key = (int(it.get("page") or 1), int(it.get("panel") or 1))
        tier = _norm_tier(it.get("tier")) or book_tier
        clothing = _norm_clothing(it.get("clothing_level"))
        old = existing.get(key)
        if old is not None:
            skipped.append(old.get("id"))
            plan_ids.append(old.get("id"))
            prev_plan_id = old.get("id") or prev_plan_id
            # 已存在的格：未投递的按剧本刷新（剧本改了要跟得上）；已投递/已回传的不动
            if (old.get("status") or "draft") == "draft":
                old["intent_text"] = _panel_intent(it)
                old["tier"] = tier
                old["clothing_level"] = clothing
                old["updated_at"] = now
                refreshed.append(old.get("id"))
            continue
        pid = "AP-%s-%04d" % (_time.strftime("%Y%m%d%H%M%S"), _random.randint(0, 9999))
        p = {
            "id": pid, "created_at": now, "updated_at": now,
            "title": "%s 第%d页 第%d格" % (eid, key[0], key[1]),
            "intent_text": _panel_intent(it),
            "engines": list(engines),
            "ref_images": [],
            "note": "",
            "tier": tier,
            "clothing_level": clothing,
            "status": "draft",
            "prompts": {},
            "page": {
                "episode_id": eid, "index": key[0], "panel_index": key[1],
                "prev_plan_id": prev_plan_id, "outline_text": outline[:_PAGE_OUTLINE_CAP],
                "image": None,
            },
        }
        _ART_DB.setdefault("plans", []).append(p)
        created.append(pid)
        plan_ids.append(pid)
        prev_plan_id = pid
    _apersist()
    return ok({"episode_id": eid, "created": len(created), "skipped": len(skipped),
               "refreshed": len(refreshed),
               "created_ids": created, "plan_ids": plan_ids, "panel_count": len(panels)})


def _comic_plan_to_panels(plan):
    """L-Port comic_page_diverge 的 panel_plan → 本仓剧本格条目。

    字段映射：narrative→画面、dialogue→台词、shot+camera→景别机位、
    action/sfx/continuity/props/light→备注、tier→水位、clothing_level→衣物档。
    """
    out = []
    for pg in ((plan or {}).get("pages") or []):
        try:
            pno = int(pg.get("page") or 0)
        except (TypeError, ValueError):
            pno = 0
        if pno <= 0:
            pno = 1
        for i, pn in enumerate(pg.get("panels") or []):
            if not isinstance(pn, dict):
                continue
            try:
                idx = int(pn.get("index") or 0)
            except (TypeError, ValueError):
                idx = 0
            if idx <= 0:
                idx = i + 1
            cam = " / ".join(x for x in (str(pn.get("shot") or "").strip(),
                                         str(pn.get("camera") or "").strip()) if x)
            note_bits = []
            for label, key in (("动作", "action"), ("拟声", "sfx"), ("连续", "continuity"),
                               ("道具", "props"), ("光", "light"), ("格型", "panel_type")):
                v = str(pn.get(key) or "").strip()
                if v:
                    note_bits.append("%s：%s" % (label, v))
            item = {
                "page": pno,
                "panel": idx,
                "text": str(pn.get("narrative") or "").strip()[:_SCRIPT_PANEL_CAP],
                "dialogue": str(pn.get("dialogue") or "").strip()[:_SCRIPT_PANEL_CAP],
                "camera": cam[:200],
                "note": "｜".join(note_bits)[:2000],
                "tier": _norm_tier(pn.get("tier")),
                "clothing_level": _norm_clothing(pn.get("clothing_level")),
            }
            if not (item["text"] or item["dialogue"] or item["camera"] or item["note"]):
                continue
            out.append(item)
    out.sort(key=lambda x: (x["page"], x["panel"]))
    return out[:_SCRIPT_MAX_PANELS]


@bp.post("/comic-plan/import")
def comic_plan_import():
    """收 L-Port 整页分镜回传（comic_page_diverge 的 panel_plan）→ 落成本集漫画剧本。

    body: {episode_id*, panel_plan? | output?, title?, premise?, characters?, style_hint?, tier?}
    → {panel_count, panels, tier}
    """
    b = request.get_json(force=True, silent=True) or {}
    eid = str(b.get("episode_id") or "").strip()
    if not eid:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id"}), 400
    plan = b.get("panel_plan")
    if not isinstance(plan, dict):
        out = b.get("output")
        plan = out.get("panel_plan") if isinstance(out, dict) else None
    if not isinstance(plan, dict):
        plan = {}
    panels = _comic_plan_to_panels(plan)
    if not panels:
        return jsonify({"code": 4004, "msg": "panel_plan 里没有格：检查 L-Port 回传的是 comic_page_diverge 输出"}), 400
    old = _script_of(eid) or {}

    def _pick(key, fallback=""):
        v = b.get(key)
        return v if v is not None else fallback

    chars = b.get("characters")
    if chars is None:
        arr = plan.get("characters") or []
        if isinstance(arr, list):
            chars = "；".join(
                " ".join(str(x.get(k) or "") for k in ("id", "desc", "anchor") if x.get(k)).strip()
                for x in arr if isinstance(x, dict)
            )
        else:
            chars = old.get("characters") or ""
    d = _save_script(eid, _pick("title", plan.get("title") or old.get("title")), panels, {
        "premise": _pick("premise", old.get("premise") or ""),
        "characters": chars or "",
        "style_hint": _pick("style_hint", plan.get("style_base") or old.get("style_hint") or ""),
        "tier": _pick("tier", old.get("tier") or ""),
    })
    return ok({"episode_id": eid, "title": d["title"], "panel_count": len(panels),
               "tier": d["tier"], "updated_at": d["updated_at"]})


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

    t0 = _time.perf_counter()
    pkg_id = "PKG-ART-%s-%04d" % (_time.strftime("%Y%m%d%H%M%S"), _random.randint(0, 9999))
    # 漫画页：把页上下文（集号/页序/大纲）拼进 intent_text —— L-Port 只认 intent_text，
    # 页面上下文不进它眼里就等于没给。原始意图仍留在方案的 intent_text 里。
    pg = p.get("page") or {}
    intent = (p.get("intent_text") or "").strip()
    tier = _norm_tier(p.get("tier"))
    clothing = _norm_clothing(p.get("clothing_level"))
    # 漫画剧本的本本元信息（前提/角色/画风/默认水位）——直投包要给 L-Port 整页分格用
    sc = _script_of(pg.get("episode_id")) if pg.get("episode_id") else None
    sc = sc or {}
    if not tier:
        tier = _norm_tier(sc.get("tier"))
    ctx_bits = []
    if pg.get("episode_id"):
        ctx_bits.append("本集集号：%s" % pg["episode_id"])
    if pg.get("index"):
        pos = "第 %s 页" % pg["index"]
        if pg.get("panel_index"):
            pos += " 第 %s 格" % pg["panel_index"]
        ctx_bits.append("本格是漫画%s：只画这一格画面，人物/服装/场景/画风与前一格保持一致" % pos)
    if tier:
        ctx_bits.append("本格水位：%s（%s）——按该档位如实画，不降档"
                        % (tier, _TIER_CN.get(tier, tier)))
    if clothing:
        ctx_bits.append("本格衣物档：%s（跨格只许收紧，不许倒退）" % clothing)
    if pg.get("outline_text"):
        ctx_bits.append("本集大纲（作画面依据，不要把文字画进画面）：\n%s" % pg["outline_text"][:6000])
    if ctx_bits:
        intent = (intent + "\n\n【漫画页上下文】\n" + "\n".join(ctx_bits)).strip()[:40000]
    elif tier:
        # 单图方案：水位写进意图文本（模型只读文本）
        intent = (intent + "\n\n" + _tier_line(tier, clothing)).strip()[:40000]
    # 参考图：优先用方案自带的；漫画格自带为空时，接上链上上一格的成图。
    # 拆格时上一格还没出图，成图是后来挂的 —— 衔接只能发生在直投这一刻。
    refs = list(p.get("ref_images") or [])
    ref_from = "plan"
    if not refs and pg.get("prev_plan_id"):
        prev = _plan(pg["prev_plan_id"]) or {}
        pimg = (prev.get("page") or {}).get("image")
        if isinstance(pimg, dict) and pimg.get("name"):
            refs = [pimg]
            ref_from = "prev_panel"
    # 漫画段：L-Port 侧可用 comic_page_diverge 走「整页分格」链路时吃这段
    comic = None
    if pg.get("episode_id"):
        comic = {
            "episode_id": pg.get("episode_id"),
            "index": pg.get("index"),
            "panel_index": pg.get("panel_index"),
            "premise": sc.get("premise") or "",
            "characters": sc.get("characters") or "",
            "style_hint": sc.get("style_hint") or "",
            "tier": tier,
            "clothing_level": clothing,
            "page_count": 1,
            "panels_per_page": 0,
        }
    art_plan = {
        "package_id": pkg_id, "kind": "art_plan",
        "plan_id": pid, "title": p.get("title") or "",
        "intent_text": intent,
        "engines": engines,
        "reference_images": [r.get("name") for r in refs],
        "user_image_instruction": p.get("note") or "",
        "note": p.get("note") or "",
        "tier": tier,
        "clothing_level": clothing,
        "comic_context": pg or None,
        "comic": comic,
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
        "engines": engines, "ref_count": len(refs), "ref_from": ref_from,
        "zip_bytes": len(buf.getvalue()), "elapsed_ms": int((_time.perf_counter() - t0) * 1000),
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


