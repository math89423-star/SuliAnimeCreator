"""traffic 蓝图：投流批量方案包（skill canonical 直连）。

skill：skills/traffic/traffic-batch/SKILL.md（任务 → 方案包，只出计划不生成片）。
本蓝图是该 skill 的执行器：解析四字段 → 双来源高光 → 文案草案 → 拼接计划 → 四门质检 → 命名导出。
失败永远回退本地规则，不抛 500（与 draft 轻链同纪律）。
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import json as _json
import os as _os
import re
import shutil as _sh
import subprocess as _sp
import time
import urllib.error as _urlerr
import urllib.request as _urlreq
from datetime import datetime
from ..services.disk_store import load, save

bp = Blueprint("traffic", __name__, url_prefix="/api/v1/traffic")

SKILL_PATH = Path(__file__).resolve().parents[3] / "skills" / "traffic" / "traffic-batch" / "SKILL.md"

HOOKS = [
    {"id": "A1", "name": "冲突直给", "tpl": "最大冲突放第1镜，留一句狠话"},
    {"id": "A2", "name": "悬念提问", "tpl": "黑屏一问+人物反应，停1拍"},
    {"id": "A3", "name": "反差", "tpl": "静空镜1s→硬切冲突"},
    {"id": "A4", "name": "台词爆点", "tpl": "金句前置，贴脸说"},
    {"id": "A5", "name": "动作奇观", "tpl": "最强运镜3秒走完"},
]
COOLS = [
    {"id": "C1", "name": "打脸", "tpl": "身份揭晓+变脸"},
    {"id": "C2", "name": "逆袭", "tpl": "先抑后扬"},
    {"id": "C3", "name": "误会揭晓", "tpl": "回放关键物件"},
    {"id": "C4", "name": "反转", "tpl": "结尾再翻一次"},
]
LIB_POOL = [
    {"id": "LIB-01", "desc": "开箱前对峙"}, {"id": "LIB-02", "desc": "烘干机空转特写"},
    {"id": "LIB-03", "desc": "取衣牌争夺"}, {"id": "LIB-04", "desc": "人物惊愕反应"},
    {"id": "LIB-05", "desc": "摔门离场"}, {"id": "LIB-06", "desc": "深夜洗衣房空镜"},
    {"id": "LIB-07", "desc": "金句贴脸"}, {"id": "LIB-08", "desc": "证据反转"},
]


_TSTORE = load("traffic_db.json", {"packages": {}, "feedbacks": []})


def _tpersist():
    save("traffic_db.json", _TSTORE)


# L-Port 素材库索引（万条规模只走索引，不逐条看内容）
# 容器内挂载 /lport-lib（投流素材库）与 /lport-ads（广告引流素材库），宿主直跑时回退仓库绝对路径。
_LPORT_FLOW = [Path("/lport-lib"),
               Path("/home/administrator/L-Port-Comfy/app/backend/data/libraries/投流素材库")]
_LPORT_ADS = [Path("/lport-ads"),
              Path("/home/administrator/L-Port-Comfy/app/backend/data/libraries/广告引流素材库")]


def _lib_roots():
    """返回 {flow: Path, ads: Path}，缺失的库直接跳过。"""
    out = {}
    for name, cands in (("flow", _LPORT_FLOW), ("ads", _LPORT_ADS)):
        for p in cands:
            try:
                if p.is_dir():
                    out[name] = p
                    break
            except OSError:
                continue
    return out


def _lib_root():
    return _lib_roots().get("flow")


_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v", ".mkv"}

# 文件名 → 钩子/爽点（L1 弱内容信号，不看视频；命中顺序即优先级）
HOOK_KW = [
    ("冲突直给", ["冲突", "对峙", "抢", "争", "夺", "抓", "打", "吵", "威胁", "action"]),
    ("悬念提问", ["悬念", "疑问", "谁", "?", "？", "骤停", "停播", "失踪", "秘密"]),
    ("反差", ["反差", "逆袭", "变身", "变脸", "女仆", "总裁", "首富"]),
    ("台词爆点", ["金句", "台词", "说", "喊", "face", "fun"]),
    ("动作奇观", ["爆炸", "追", "打斗", "动作", "epic", "dream", "calma"]),
]
COOL_KW = [
    ("打脸", ["打脸", "揭晓", "变脸", "证据"]),
    ("逆袭", ["逆袭", "翻身", "登场"]),
    ("误会揭晓", ["误会", "真相", "原来"]),
    ("反转", ["反转", "翻转", "没想到"]),
]

_ASTORE = load("traffic_assets.json", {"assets": {}, "updated_at": 0})


def _apersist():
    save("traffic_assets.json", _ASTORE)


# 视频缩略图：scan 增量抽首帧（ffmpeg），落 backend/data/traffic_thumbs（volume 持久化）
THUMB_DIR = Path(__file__).resolve().parents[2] / "data" / "traffic_thumbs"


def _thumb_name(key):
    return re.sub(r"[^A-Za-z0-9一-鿿_.-]+", "_", key).strip("_")[:120] + ".jpg"


def _ensure_thumb(key, src, mtime=0):
    """有现成且不旧直接用，否则抽一帧；返回 Path 或 None。"""
    if not _sh.which("ffmpeg"):
        return None
    try:
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    dst = THUMB_DIR / _thumb_name(key)
    try:
        if dst.is_file() and dst.stat().st_mtime >= (mtime or 0):
            return dst
    except OSError:
        pass
    try:
        _sp.run(["ffmpeg", "-y", "-ss", "1", "-i", str(src),
                 "-vframes", "1", "-vf", "scale=320:-1", "-q:v", "4", str(dst)],
                capture_output=True, timeout=30)
        return dst if dst.is_file() else None
    except Exception:
        return None


def _parse_name(stem):
    """文件名 parse：desc 取可读干（去 demo/assembled 前缀，下划线转空格），hook/cool 按关键词表命中。"""
    s = stem or ""
    for _ in range(2):
        s = re.sub(r"^(demo_\d+_|assembled_)", "", s)
    desc = (s.replace("_", " ").replace("-", " ").strip() or stem)[:60]
    hook, cool = "", ""
    # 规范命名（钩子_场景_序号）优先按前缀命中，避免单字关键词误伤（如打蛋/打脸误判冲突）
    for name, _kws in HOOK_KW:
        if stem.startswith(name + "_") or stem.startswith(name + "-"):
            hook = name
            break
    if not hook:
        for name, kws in HOOK_KW:
            if any(k in stem for k in kws):
                hook = name
                break
    for name, kws in COOL_KW:
        if any(k in stem for k in kws):
            cool = name
            break
    return desc, hook, cool


def _probe_video(p):
    """ffprobe 取宽/高/时长；失败回 0（不断链，人工复核时再看）。"""
    if not _sh.which("ffprobe"):
        return 0, 0, 0.0
    try:
        r = _sp.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,duration",
             "-show_entries", "format=duration", "-of", "json", str(p)],
            capture_output=True, text=True, timeout=20)
        d = _json.loads(r.stdout or "{}")
        streams = d.get("streams") or [{}]
        w = int(streams[0].get("width") or 0)
        h = int(streams[0].get("height") or 0)
        dur = float(streams[0].get("duration") or (d.get("format") or {}).get("duration") or 0)
        return w, h, round(dur, 1)
    except Exception:
        return 0, 0, 0.0


_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# 产物目录标记：相对路径里出现即整支跳过。
PRODUCT_MARKERS = ("CH01_act1",)

# 库 → 子目录 → 素材种类：视频资源 vs 广告素材（动态/静止图）
# 口径：**素材真源只有这一份** —— L-Port 的 app/backend/data/libraries/{投流素材库,广告引流素材库}
# （容器内挂 /lport-lib、/lport-ads）。L-Port 的产物区 data/outputs/libraries/** 不在计划内：
# 那里的 CH01 分段合成（seg*_composite.mp4/png）、demo_composite.mp4 是**产物**，不是投流素材，
# 纳入会让两侧计数永远对不上（详见 L-Port docs/ASSET_LIBRARY_SSOT.md）。
_SCAN_PLAN = [
    ("flow", "videos", "video"),
    ("flow", "covers", "image"),
    ("ads", "covers", "image"),
    ("ads", "红包样式", "image"),
    ("ads", "CTA按钮", "image"),
    ("ads", "倒计时", "image"),
    ("ads", "挂件角标", "image"),
    ("ads", "字幕花字", "image"),
    ("ads", "优惠券", "image"),
]


def _rescan_assets(force=False):
    """增量扫描：mtime+size 未变直接复用缓存，只探新增/变更。force=True 全量重parse。"""
    import time as _t
    t0 = _t.time()
    roots = _lib_roots()
    if not roots:
        return {"ok": False, "msg": "L-Port 素材库未挂载（/lport-lib、/lport-ads 均缺失）", "total": 0}
    assets = _ASTORE.get("assets") or {}
    if not isinstance(assets, dict):
        assets = {}
    seen, new_n = set(), 0
    for lib, sub, kind in _SCAN_PLAN:
        root = roots.get(lib)
        if root is None:
            continue
        vdir = root / sub
        exts = _VIDEO_EXTS if kind == "video" else _IMAGE_EXTS
        try:
            files = sorted(vdir.rglob("*")) if vdir.is_dir() else []
        except OSError:
            continue
        for f in files:
            if not f.is_file() or f.suffix.lower() not in exts:
                continue
            rel_path = f.relative_to(root).as_posix()
            if any(m in rel_path for m in PRODUCT_MARKERS):
                continue  # 产物不进素材库（CH01 分段合成等）
            try:
                st = f.stat()
            except OSError:
                continue
            key = "%s/%s" % (lib, rel_path)
            seen.add(key)
            old = assets.get(key) if isinstance(assets.get(key), dict) else None
            if old is None:
                # 索引（key 无 lib 前缀）：按文件名找回用量
                for ok_, ov in assets.items():
                    if isinstance(ov, dict) and ov.get("name") == f.name:
                        old = ov
                        break
            if not force and old and old.get("mtime") == st.st_mtime and old.get("size") == st.st_size:
                continue
            w, h, dur = _probe_video(f)
            desc, hook, cool = _parse_name(f.stem)
            # file 保持库内相对路径（L-Port 执行侧按 LIB/file 定位），lib 字段区分归属库
            assets[key] = {"id": f.stem[:48], "file": f.relative_to(root).as_posix(),
                           "lib": lib, "kind": kind,
                           "name": f.name,
                           "desc": desc, "w": w, "h": h, "dur": dur,
                           "hook": hook, "cool": cool,
                           "orient": "portrait" if h >= w and w else ("landscape" if w > h else ""),
                           "mtime": st.st_mtime, "size": st.st_size,
                           # 用量计数重扫保留，不随重parse清零
                           "used": int((old or {}).get("used") or 0),
                           "last_used": int((old or {}).get("last_used") or 0)}
            if kind == "video":
                _ensure_thumb(key, f, st.st_mtime)
            new_n += 1
    removed = [k for k in assets if k not in seen]
    for k in removed:
        assets.pop(k, None)
    # 索引（无 kind/file 前缀）迁移：file 补前缀并标 kind
    _ASTORE["assets"] = assets
    _ASTORE["updated_at"] = int(_t.time() * 1000)
    _apersist()
    kinds: dict = {}
    for v in assets.values():
        if isinstance(v, dict):
            k = v.get("kind") or "video"
            kinds[k] = kinds.get(k, 0) + 1
    return {"ok": True, "total": len(assets), "new": new_n, "removed": len(removed),
            "kinds": kinds,
            "elapsed_ms": int((_t.time() - t0) * 1000),
            "libs": {k: str(v) for k, v in roots.items()}}


def _index_rows():
    assets = _ASTORE.get("assets") or {}
    return [v for v in assets.values() if isinstance(v, dict)]


# ── 索引自动失效 ────────────────────────────────────────────────
# 真源是目录：目录变了，索引必须跟着变。否则删文件/加文件要等到有人手点
# 重扫才生效。
# 做法：节流 + 目录摘要（mtime_ns + 条目数）比对，变了才增量重扫；
# 深层目录内新增/改名不改变上层目录 mtime，所以「重扫」按钮保留为强刷手段。
_SCAN_CACHE: dict = {"t": 0.0, "sig": None}


def _dirs_sig():
    roots = _lib_roots()
    sig = []
    for lib, sub, _kind in _SCAN_PLAN:
        root = roots.get(lib)
        d = (root / sub) if root is not None else None
        try:
            n = sum(1 for _ in d.iterdir())
            sig.append((lib, sub, d.stat().st_mtime_ns, n))
        except OSError:
            sig.append((lib, sub, None, 0))
    return tuple(sig)


def maybe_autoscan(min_interval=60.0):
    """目录摘要变了且距上次扫描 ≥ min_interval 秒 → 增量重扫；返回统计或 None。"""
    now = time.time()
    if now - float(_SCAN_CACHE.get("t") or 0.0) < float(min_interval):
        return None
    sig = _dirs_sig()
    _SCAN_CACHE["t"] = now
    if sig == _SCAN_CACHE.get("sig"):
        return None
    _SCAN_CACHE["sig"] = sig
    try:
        return _rescan_assets()
    except Exception:
        return None


def _sample_index(limit=40):
    """索引抽样：竖屏优先、时长 2-60s，钩子类型轮询保证差异性；
    同桶内用量最少的优先（used+1/last_used 每次出包后累加），新入库默认 used=0 先上。"""
    rows = [r for r in _index_rows()
            if (r.get("kind") or "video") == "video"
            and ((r.get("dur") or 0) >= 2 or not r.get("dur"))]
    rows.sort(key=lambda r: (0 if r.get("orient") == "portrait" else 1, r.get("file") or ""))
    buckets: dict = {}
    for r in rows:
        buckets.setdefault(r.get("hook") or "未分类", []).append(r)
    for b in buckets.values():
        b.sort(key=lambda r: (r.get("used") or 0, r.get("file") or ""))
    order = sorted(buckets, key=lambda k: (k == "未分类", k))
    out, i = [], 0
    while len(out) < limit:
        added = False
        for k in order:
            b = buckets[k]
            if i < len(b):
                r = b[i]
                out.append({"id": r.get("id") or r.get("name", ""),
                            "desc": r.get("desc") or r.get("name", ""),
                            "file": r.get("file", ""), "w": r.get("w", 0),
                            "h": r.get("h", 0), "dur": r.get("dur", 0),
                            "hook": r.get("hook", ""), "cool": r.get("cool", "")})
                added = True
                if len(out) >= limit:
                    break
        if not added:
            break
        i += 1
    return out


def ok(data):
    return jsonify({"code": 0, "data": data})


def skill_version():
    try:
        return SKILL_PATH.stat().st_mtime_ns
    except OSError:
        return 0


def _norm_lib(items):
    out = []
    for x in items or []:
        if isinstance(x, str):
            x = {"id": x, "desc": x}
        if not isinstance(x, dict):
            continue
        lid = str(x.get("id") or x.get("ref") or "").strip()[:24] or ("LIB-%02d" % (len(out) + 1))
        desc = str(x.get("desc") or x.get("duty") or lid).strip()[:60] or lid
        out.append({"id": lid, "desc": desc})
    return out


def _episode_library(mother_id):
    """本集分镜 -> 高光池：duty 即高光描述，演示不断链。失败回 []。"""
    try:
        from ..services import repo as _repo
        rows = _repo.list_shots_by_episode(mother_id or "")
        pool = []
        for s in rows:
            duty = (s.get("duty") or "").strip()
            if not duty:
                continue
            pool.append({"id": s.get("id", ""), "desc": duty[:60]})
        return pool
    except Exception:
        return []


def _resolve_library(b, mother_id, tasks):
    top = _norm_lib((b or {}).get("library"))
    if top:
        return top, "custom"
    merged = []
    for t in tasks or []:
        if isinstance(t, dict):
            merged += _norm_lib(t.get("library"))
    if merged:
        seen, uniq = set(), []
        for x in merged:
            if x["id"] not in seen:
                seen.add(x["id"])
                uniq.append(x)
        return uniq, "custom"
    auto = (b or {}).get("auto_mother", True)
    if (b or {}).get("use_episode") is False or (b or {}).get("from_episode") is False:
        auto = False
    # 万条规模只走索引：L-Port 索引抽样（元数据+文件名parse，不看内容）打底，
    # 本集分镜 duties（纯文本，无需看片）追加；两者都不在才回内置池。
    pool, srcs = [], []
    idx = _sample_index(limit=40)
    if idx:
        pool += idx
        srcs.append("lport-index(%d)" % len(idx))
    if auto and mother_id:
        ep_pool = _episode_library(mother_id)
        if ep_pool:
            have = {x["id"] for x in pool}
            pool += [x for x in ep_pool if x["id"] not in have]
            srcs.append("episode(%d)" % len(ep_pool))
    if pool:
        return pool[:64], "+".join(srcs)
    return list(LIB_POOL), "builtin"


# 高光窗口规则：素材够长就跳过片头/取中段，成片别永远从第 0 秒开始。
# 判断依据只有索引里的时长（不看画面内容）；素材比计划短时起点回 0，交给执行侧循环补帧。
HL_PLAN_S = 15.0        # 计划成片时长（与剪辑单 duration_s 同口径）
HL_SKIP_HEAD_S = 1.2    # 片头常是静帧/黑场，跳过
HL_LONG_S = 20.0        # 超过这个长度按"取中段"处理
HL_LONG_RATIO = 0.25    # 长素材跳过前 25%（开头多是同质空镜）


def _hl_window(src_dur, plan_s=HL_PLAN_S):
    """按素材时长算高光窗口 → (start_s, end_s, note)。end_s 为素材末尾时不越界。"""
    try:
        dur = float(src_dur or 0)
    except (TypeError, ValueError):
        dur = 0.0
    plan = float(plan_s or HL_PLAN_S)
    if dur <= 0:
        return 0.0, None, "无时长信息，从 0 起"
    if dur < plan + HL_SKIP_HEAD_S:
        return 0.0, round(dur, 1), "素材%.1fs<计划%.0fs：全用+循环补帧" % (dur, plan)
    start = HL_SKIP_HEAD_S
    mid = dur >= HL_LONG_S
    if mid:
        start = max(start, round(dur * HL_LONG_RATIO, 1))
    start = min(start, max(0.0, round(dur - plan, 1)))
    end = min(start + plan, dur)
    return round(start, 1), round(end, 1), "跳过片头%.1fs%s" % (start, "（取中段）" if mid else "")


def parse_task(t):
    desc = (t.get("desc") or "").strip()
    mode = t.get("mode") if t.get("mode") in ("gen", "lib") else "lib"
    category = (t.get("category") or "红包点击").strip() or "红包点击"
    try:
        count = max(1, min(120, int(t.get("count") or 15)))
    except (TypeError, ValueError):
        count = 15
    ref_video = (t.get("refVideo") or t.get("ref_video") or "").strip()
    m = t.get("mount") if isinstance(t.get("mount"), dict) else {}
    mount = {"search_word": str(m.get("search_word") or "").strip()[:30],
             "app_name": str(m.get("app_name") or "").strip()[:30],
             "overlay_text": str(m.get("overlay_text") or "").strip()[:40]}
    return {"desc": desc, "mode": mode, "category": category, "count": count, "refVideo": ref_video, "mount": mount}


def _llm_variants(t, n, lib_pool=None):
    """skill驱动的LLM出稿：一次产出该任务的N条钩子/假设/标题/CTA。失败返回None（调用方回退规则）。"""
    import json as _json
    from ..services.llm_opencode import llm_cfg, _post
    cfg = llm_cfg()
    if cfg.get("provider") == "llamacpp":
        if not cfg.get("model"):
            return None
        from ..services.llm_opencode import _post_openai
        model_id, use_local = cfg["model"], True
    else:
        model_id = re.sub(r"^opencode-go/", "", cfg.get("model") or "")
        if not cfg.get("key") or not model_id:
            return None
        use_local = False
    lib_txt = "；".join("%s=%s" % (x["id"], x["desc"]) for x in (lib_pool or LIB_POOL))[:1200]
    prompt = (
        "你是短剧投流批量助手，按skills/traffic/traffic-batch/SKILL.md出N条可测变体。"
        "只输出JSON数组，每项含hook(钩子名,限8字)/hook_line(首句台词,限20字)/"
        "hypothesis(一句测试假设,含测什么)/title(标题,限18字)/cta(结尾行动句,限15字)。"
        "钩子必须在[冲突直给,悬念提问,反差,台词爆点,动作奇观]里轮换，N条之间钩子尽量不重复，相邻两条必须不同。"
        "任务：目标=%s｜方式=%s｜分类=%s｜N=%d｜描述=%s｜素材库=%s"
        % (t.get("desc", "")[:200] or t.get("category", ""), t["mode"], t["category"], n,
           (t.get("desc", "") or "")[:200], lib_txt)
    )
    try:
        if use_local:
            from ..services.llm_opencode import _post_openai
            txt = _post_openai(cfg["base"], cfg.get("key", ""), model_id,
                               [{"role": "user", "content": prompt}], timeout=90)
        else:
            txt = _post(cfg["base"], cfg["key"], model_id, prompt,
                        timeout=90, effort=cfg.get("effort", ""))
    except Exception:
        return None
    try:
        m = re.search(r'\[.*\]', txt or "", re.S)
        if not m:
            return None
        rows = _json.loads(m.group(0))
        if not isinstance(rows, list) or not rows:
            return None
        out = []
        for r in rows[:n]:
            if not isinstance(r, dict):
                continue
            out.append({
                "hook": str(r.get("hook") or "")[:12],
                "hook_line": str(r.get("hook_line") or "")[:24],
                "hypothesis": str(r.get("hypothesis") or "")[:40],
                "title": str(r.get("title") or "")[:20],
                "cta": str(r.get("cta") or "")[:20],
            })
        return out if out else None
    except Exception:
        return None


@bp.get("/skill")
def get_skill():
    try:
        text = SKILL_PATH.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return ok({"path": "skills/traffic/traffic-batch/SKILL.md", "version": skill_version(), "md": text})


@bp.get("/library")
def get_library():
    """高光池预览：?episode_id= 优先返回本集分镜池，否则内置池。"""
    eid = (request.args.get("episode_id") or request.args.get("mother_id") or "").strip()
    if eid:
        pool = _episode_library(eid)
        if pool:
            return ok({"episode_id": eid, "source": "episode", "library": pool, "count": len(pool)})
    return ok({"episode_id": eid, "source": "builtin", "library": list(LIB_POOL), "count": len(LIB_POOL)})


@bp.get("/assets")
def list_assets():
    """L-Port 素材索引查询：kind(video/image)/lib(flow/ads)/q/hook/cool/min_dur/orient/limit/offset，只读索引不碰原视频。"""
    maybe_autoscan()  # 目录变了先自动对齐，页面上的计数不会停在旧快照
    try:
        limit = max(1, min(200, int(request.args.get("limit") or 50)))
    except (TypeError, ValueError):
        limit = 50
    try:
        offset = max(0, int(request.args.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    q = (request.args.get("q") or "").strip()
    kind = (request.args.get("kind") or "").strip()
    lib = (request.args.get("lib") or "").strip()
    hook = (request.args.get("hook") or "").strip()
    cool = (request.args.get("cool") or "").strip()
    orient = (request.args.get("orient") or "").strip()
    try:
        min_dur = float(request.args.get("min_dur") or 0)
    except (TypeError, ValueError):
        min_dur = 0
    rows = _index_rows()
    if kind:
        rows = [r for r in rows if (r.get("kind") or "video") == kind]
    if lib:
        rows = [r for r in rows if r.get("lib") == lib]
    if q:
        rows = [r for r in rows if q in (r.get("name") or "") or q in (r.get("desc") or "")]
    if hook:
        rows = [r for r in rows if r.get("hook") == hook]
    if cool:
        rows = [r for r in rows if r.get("cool") == cool]
    if orient:
        rows = [r for r in rows if r.get("orient") == orient]
    if min_dur:
        rows = [r for r in rows if (r.get("dur") or 0) >= min_dur]
    rows.sort(key=lambda r: ((r.get("hook") or "未分类") == "未分类", r.get("file") or ""))
    hooks: dict = {}
    kinds: dict = {}
    for r in _index_rows():
        k = r.get("hook") or "未分类"
        hooks[k] = hooks.get(k, 0) + 1
        kk = r.get("kind") or "video"
        kinds[kk] = kinds.get(kk, 0) + 1
    return ok({"total": len(rows), "limit": limit, "offset": offset,
               "rows": rows[offset:offset + limit],
               "facets": {"hooks": hooks, "kinds": kinds, "indexed": len(_index_rows())},
               "updated_at": _ASTORE.get("updated_at", 0)})


@bp.get("/asset-file")
def asset_file():
    """索引文件直出（缩略图/预览用）：lib=flow|ads，path 为库内相对路径，禁目录穿越。"""
    from flask import send_file as _send
    maybe_autoscan()
    lib = (request.args.get("lib") or "").strip()
    rel = (request.args.get("path") or "").strip()
    roots = _lib_roots()
    root = roots.get(lib)
    if root is None or not rel or ".." in rel or rel.startswith("/"):
        return jsonify({"code": 4001, "msg": "非法路径"}), 400
    try:
        fp = (root / rel).resolve()
        if root.resolve() not in fp.parents and fp != root.resolve():
            return jsonify({"code": 4001, "msg": "非法路径"}), 400
        if not fp.is_file():
            return jsonify({"code": 4004, "msg": "文件不存在"}), 404
    except OSError:
        return jsonify({"code": 4004, "msg": "文件不存在"}), 404
    return _send(fp)


@bp.delete("/assets")
def delete_assets():
    """批量删除素材：删库文件 + 索引条目 + 缩略图。历史包里的引用不受影响。"""
    b = request.get_json(force=True, silent=True) or {}
    items = b.get("items") or []
    if not isinstance(items, list) or not items:
        return jsonify({"code": 4001, "msg": "缺 items"}), 400
    roots = _lib_roots()
    assets = _ASTORE.get("assets") or {}
    deleted, failed = [], []
    for it in items[:200]:
        if not isinstance(it, dict):
            continue
        lib = str(it.get("lib") or "").strip()
        rel = str(it.get("path") or it.get("file") or "").strip()
        root = roots.get(lib)
        if root is None or not rel or ".." in rel or rel.startswith("/"):
            failed.append({"path": rel, "msg": "非法路径"})
            continue
        try:
            fp = (root / rel).resolve()
            if root.resolve() not in fp.parents or not fp.is_file():
                failed.append({"path": rel, "msg": "文件不存在"})
                continue
            fp.unlink()
        except OSError as e:
            failed.append({"path": rel, "msg": "删除失败:%s" % e})
            continue
        key = "%s/%s" % (lib, rel)
        assets.pop(key, None)
        try:
            th = THUMB_DIR / _thumb_name(key)
            if th.is_file():
                th.unlink()
        except OSError:
            pass
        deleted.append(rel)
    _ASTORE["assets"] = assets
    _apersist()
    return ok({"deleted": deleted, "failed": failed, "count": len(deleted)})


@bp.post("/assets/rename")
def rename_asset():
    """素材重命名：库内改名 + 索引迁移（用量保留，按新名重parse，旧缩略图作废）。"""
    b = request.get_json(force=True, silent=True) or {}
    lib = (b.get("lib") or "").strip()
    rel = (b.get("path") or b.get("file") or "").strip()
    new_name = (b.get("new_name") or b.get("name") or "").strip()
    roots = _lib_roots()
    root = roots.get(lib)
    if root is None or not rel or ".." in rel or rel.startswith("/"):
        return jsonify({"code": 4001, "msg": "非法路径"}), 400
    if not new_name or "/" in new_name or "\\" in new_name or new_name.startswith("."):
        return jsonify({"code": 4001, "msg": "非法文件名"}), 400
    try:
        src = (root / rel).resolve()
        if root.resolve() not in src.parents or not src.is_file():
            return jsonify({"code": 4004, "msg": "文件不存在"}), 404
        if src.suffix.lower() != Path(new_name).suffix.lower():
            return jsonify({"code": 4001, "msg": "不许改扩展名"}), 400
        dst = src.parent / new_name
        if dst.exists():
            return jsonify({"code": 4001, "msg": "同名文件已存在"}), 400
        src.rename(dst)
        st = dst.stat()
    except OSError as e:
        return jsonify({"code": 4001, "msg": "改名失败:%s" % e}), 400
    assets = _ASTORE.get("assets") or {}
    old_key = "%s/%s" % (lib, rel)
    old = assets.pop(old_key, None)
    if not isinstance(old, dict):
        old = {}
    new_rel = dst.relative_to(root).as_posix()
    new_key = "%s/%s" % (lib, new_rel)
    desc, hook, cool = _parse_name(dst.stem)
    w, h, dur = _probe_video(dst)
    if not w and isinstance(old.get("w"), int):
        w, h, dur = old.get("w", 0), old.get("h", 0), old.get("dur", 0)
    assets[new_key] = {"id": dst.stem[:48], "file": new_rel,
                       "lib": lib, "kind": old.get("kind") or ("video" if dst.suffix.lower() in _VIDEO_EXTS else "image"),
                       "name": dst.name,
                       "desc": desc, "w": w, "h": h, "dur": dur,
                       "hook": hook, "cool": cool,
                       "orient": "portrait" if h >= w and w else ("landscape" if w > h else ""),
                       "mtime": st.st_mtime, "size": st.st_size,
                       "used": int(old.get("used") or 0),
                       "last_used": int(old.get("last_used") or 0)}
    _ASTORE["assets"] = assets
    _apersist()
    try:
        old_thumb = THUMB_DIR / _thumb_name(old_key)
        if old_thumb.is_file():
            old_thumb.unlink()
    except OSError:
        pass
    return ok({"old": old_key, "entry": assets[new_key]})


@bp.get("/thumb")
def asset_thumb():
    """视频缩略图：按索引 key 查条目，缺图时懒抽一帧。无 key 直接 404，不做路径拼接。"""
    from flask import send_file as _send2
    lib = (request.args.get("lib") or "").strip()
    rel = (request.args.get("path") or "").strip()
    if not lib or not rel:
        return jsonify({"code": 4001, "msg": "缺参数"}), 400
    assets = _ASTORE.get("assets") or {}
    hit = None
    for k, v in assets.items():
        if isinstance(v, dict) and v.get("lib") == lib and v.get("file") == rel \
                and (v.get("kind") or "video") == "video":
            hit, key = v, k
            break
    if not hit:
        return jsonify({"code": 4004, "msg": "不在索引中"}), 404
    roots = _lib_roots()
    root = roots.get(lib)
    dst = THUMB_DIR / _thumb_name(key)
    if not dst.is_file() and root is not None:
        try:
            src = (root / rel).resolve()
            if root.resolve() in src.parents:
                _ensure_thumb(key, src, hit.get("mtime", 0))
        except OSError:
            pass
    if not dst.is_file():
        return jsonify({"code": 4004, "msg": "缩略图缺失"}), 404
    return _send2(dst, mimetype="image/jpeg")


@bp.post("/assets/rescan")
def rescan_assets():
    """触发 L-Port 素材库增量扫描（ffprobe+文件名parse）。force=1 全量重parse。"""
    b = request.get_json(force=True, silent=True) or {}
    force = str(b.get("force") or request.args.get("force") or "") in ("1", "true", "yes")
    return ok(_rescan_assets(force=force))


@bp.post("/ref-video/analyze")
def ref_video_analyze():
    """参考视频占位分析：文件名 -> 3条高光描述（抽帧+视觉描述是后一步增强，当前先引用跑通）。"""
    b = request.get_json(force=True, silent=True) or {}
    path = (b.get("path") or b.get("refVideo") or b.get("ref_video") or "").strip()
    base = Path(path).name or "参考视频"
    stems = [base[:12] or "参考片", "片内冲突前置", "片尾钩子回放"]
    highs = [{"id": "REF-%s-%d" % ((base[:4] or "REF"), i + 1), "desc": "%s｜%s" % (base[:12], s)}
             for i, s in enumerate(stems)]
    return ok({"path": path, "desc": "参考视频已传，按片内高光出变体",
               "highlights": highs, "note": "全自动抽帧为后一步增强"})


@bp.post("/generate")
def generate():
    b = request.get_json(force=True, silent=True) or {}
    mother_id = (b.get("mother_id") or b.get("episode_id") or "EP-DEMO01").strip() or "EP-DEMO01"
    raw_tasks = b.get("tasks") or ([{"desc": b.get("instruction", ""), "mode": "lib", "category": "红包点击", "count": b.get("n", 15)}] if b.get("instruction") else [])
    tasks = [parse_task(t) for t in raw_tasks if isinstance(t, dict)]
    tasks = [t for t in tasks if t["desc"] or t["refVideo"]]
    if not tasks:
        return jsonify({"code": 4001, "msg": "至少填一个任务描述或参考视频"}), 400
    lib_pool, lib_src = _resolve_library(b, mother_id, raw_tasks)
    if not lib_pool:
        lib_pool = list(LIB_POOL)
        lib_src = "builtin"
    batch = "PKG-TRAFFIC-%s-%s" % (mother_id, datetime.now().strftime("%m%d"))
    variants, highlights, copies, plans, materials = [], [], [], [], []
    seen = set()
    vseq = 0
    engines = []
    for ti, t in enumerate(tasks):
        llm_rows = _llm_variants(t, t["count"], lib_pool)
        engine = "llm" if llm_rows else "template"
        engines.append(engine)
        for i in range(t["count"]):
            hk = HOOKS[i % len(HOOKS)]
            cl = COOLS[(i + ti) % len(COOLS)]
            lib = lib_pool[(i + ti) % len(lib_pool)]
            lr = (llm_rows[i] if llm_rows and i < len(llm_rows) else None)
            hk_name = (lr.get("hook") if lr and lr.get("hook") in [h["name"] for h in HOOKS] else hk["name"]) if lr else hk["name"]
            use_gen = t["mode"] == "gen" and i % 4 == 3
            if t["refVideo"]:
                src, ref, hdesc = "library", "REF-%s" % t["refVideo"][:6], "参考视频%s｜%s" % (t["refVideo"][:12], lib["desc"])
            elif use_gen:
                src, ref, hdesc = "generate", "GEN-%02d" % (i + 1), (t["desc"][:20] or hk["tpl"])
            else:
                src, ref, hdesc = "library", lib["id"], lib["desc"]
            key = (hk_name, cl["id"], ref, t["category"])
            if key in seen:
                continue
            seen.add(key)
            vseq += 1
            vid = "T%d-V%02d" % (ti + 1, i + 1)
            hyp = (lr.get("hypothesis") if lr and lr.get("hypothesis") else "%s测%s" % (hk_name, t["category"]))[:40]
            hook_line = ("｜「%s」" % lr["hook_line"]) if lr and lr.get("hook_line") else ""
            title = (lr.get("title") if lr and lr.get("title") else "%s｜%s" % (t["category"], hk_name))[:20]
            cta = (lr.get("cta") if lr and lr.get("cta") else (t["desc"][:30] or "点红包→看正片"))[:20]
            hid = "H%03d" % vseq
            fname = "%s_%s_%s_1080x1920.mp4" % (batch, vid, hid)
            # 插入点规则化（只看元数据，不看内容）：0s贴片挂载固定，红包图落钩子转场~3s处；
            # 横屏素材统一竖裁中段，竖屏直出。agent 不逐条想插入点。
            w, h = int(lib.get("w") or 0), int(lib.get("h") or 0)
            overlay = ((t.get("mount") or {}).get("overlay_text") or t["category"])[:40]
            inserts = [{"t": "0s", "what": "贴片:%s" % overlay},
                       {"t": "3s", "what": "红包图/特写插入（钩子转场处）"}]
            crop = "竖裁中段1080x1920" if w > h > 0 else "直出1080x1920"
            # 高光窗口：按素材时长算起点（规则，不看内容）——执行侧按 [start_s, end_s] 截取
            hl_start, hl_end, hl_note = _hl_window(lib.get("dur"))
            src_dur = round(float(lib.get("dur") or 0), 1)
            highlights.append({"id": hid, "variant_id": vid, "source": src, "ref": ref, "desc": hdesc,
                               "duration_s": 4, "start_s": hl_start, "end_s": hl_end,
                               "src_dur_s": src_dur, "window_note": hl_note})
            copies.append({"variant_id": vid, "hypothesis": hyp, "hook": "%s｜%s%s" % (hk_name, hdesc, hook_line),
                           "title": title, "cta": cta})
            plans.append({"order": vseq, "variant_id": vid, "highlight_id": hid,
                          "copy_seg": "hook(4s)+body+cta(3s)", "duration_s": 15,
                          "hook": hk_name, "body": hdesc, "cta": cta, "mount": dict(t["mount"]),
                          "inserts": inserts, "crop": crop,
                          "start_s": hl_start, "end_s": hl_end, "src_dur_s": src_dur,
                          "window_note": hl_note})
            materials.append({"variant_id": vid, "highlight_id": hid, "ref": ref,
                              "file": fname, "source": src, "desc": hdesc, "mount": dict(t["mount"]),
                              "start_s": hl_start, "end_s": hl_end,
                              "src_asset": lib.get("file", "")})
            variants.append({
                "variant_id": vid, "task_id": ti + 1, "hypothesis": hyp,
                "hook_text": "%s｜%s%s" % (hk_name, hdesc, hook_line),
                "hl_id": hid, "hl_desc": hdesc,
                "title": title,
                "cta_text": cta,
                "mount": dict(t["mount"]),
                "start_s": hl_start, "end_s": hl_end, "src_dur_s": src_dur,
                "window_note": hl_note,
                "file_name": fname,
                "asset": lib.get("file", ""),
            })
            if len(variants) >= 120:
                break
    # 用量累加：本包引用到的索引素材 used+1，下次抽样自动靠后
    if variants:
        _assets = _ASTORE.get("assets") or {}
        now_ms = int(time.time() * 1000)
        touched = False
        for v in variants:
            f = v.get("asset") or ""
            if f and isinstance(_assets.get(f), dict):
                _assets[f]["used"] = int(_assets[f].get("used") or 0) + 1
                _assets[f]["last_used"] = now_ms
                touched = True
        if touched:
            _ASTORE["assets"] = _assets
            _apersist()
    checks = {
        "skill": "skills/traffic/traffic-batch/SKILL.md",
        "skill_version": skill_version(),
        "engine": "+".join(sorted(set(engines))) if engines else "template",
        "lib_source": lib_src,
        "testable": all(v.get("hypothesis") for v in variants),
        "deduped": len(seen) == len(variants),
        "executable": all(v.get("hl_id") and v.get("hook_text") for v in variants),
        "mount_ok": all(isinstance(v.get("mount"), dict) for v in variants),
        "naming_ok": all(v["file_name"].endswith("_1080x1920.mp4") for v in variants),
        "materials_ok": len(materials) == len(variants),
    }
    pkg = {
        "package_id": batch, "mother_id": mother_id,
        "created_at": int(time.time() * 1000),
        "lib_source": lib_src,
        "library": lib_pool,
        "tasks": [{"desc": t["desc"], "mode": t["mode"], "category": t["category"], "count": t["count"], "refVideo": t["refVideo"], "mount": t["mount"]} for t in tasks],
        "highlights": highlights, "copy_draft": copies, "splice_plan": plans,
        "materials": materials,
        "naming_rule": "{package}_{variant}_{highlight}_1080x1920.mp4｜跑量档720x1280",
        "checks": checks, "variants": variants,
    }
    _TSTORE.setdefault("packages", {})[batch] = pkg
    _tpersist()
    return ok(pkg)


@bp.get("/packages")
def list_packages():
    pkgs = _TSTORE.get("packages", {})
    rows = [{"package_id": k, "mother_id": v.get("mother_id", ""),
             "created_at": v.get("created_at", 0),
             "variants": len(v.get("variants", [])),
             "lib_source": v.get("lib_source", "")} for k, v in pkgs.items()]
    rows.sort(key=lambda r: r.get("created_at", 0), reverse=True)
    return ok({"packages": rows, "count": len(rows)})


@bp.get("/package/<pid>")
def get_package(pid):
    pkg = (_TSTORE.get("packages", {}) or {}).get(pid)
    if not pkg:
        return jsonify({"code": 4004, "msg": "包不存在"}), 404
    fbs = [f for f in (_TSTORE.get("feedbacks", []) or []) if f.get("package_id") == pid]
    out = dict(pkg)
    out["feedbacks"] = fbs
    return ok(out)


@bp.delete("/packages/<pid>")
def delete_package(pid):
    """删除历史包（含其复盘回流记录）。"""
    pkgs = _TSTORE.get("packages", {}) or {}
    if pid not in pkgs:
        return jsonify({"code": 4004, "msg": "包不存在"}), 404
    pkgs.pop(pid, None)
    _TSTORE["packages"] = pkgs
    _TSTORE["feedbacks"] = [f for f in (_TSTORE.get("feedbacks", []) or []) if f.get("package_id") != pid]
    _tpersist()
    return ok({"package_id": pid, "deleted": True})


@bp.get("/export-bundle")
def export_bundle():
    """投流包 ZIP：package.json + materials.csv + splice.txt，一键拷走即交付。"""
    import io as _io
    import zipfile as _zip
    import json as _json
    pid = (request.args.get("package_id") or "").strip()
    pkg = (_TSTORE.get("packages", {}) or {}).get(pid)
    if not pkg:
        return jsonify({"code": 4004, "msg": "包不存在，先 generate"}), 404
    buf = _io.BytesIO()
    with _zip.ZipFile(buf, "w", _zip.ZIP_DEFLATED) as zf:
        zf.writestr("package.json", _json.dumps(pkg, ensure_ascii=False, indent=2))
        lines = ["variant_id,highlight_id,ref,file,source,search_word,app_name,overlay_text,start_s,end_s"]
        for m in pkg.get("materials", []):
            base = [str(m.get(k, "")) for k in ("variant_id", "highlight_id", "ref", "file", "source")]
            mt = m.get("mount") if isinstance(m.get("mount"), dict) else {}
            base += [str(mt.get("search_word", "")), str(mt.get("app_name", "")), str(mt.get("overlay_text", "")),
                     str(m.get("start_s", "")), str(m.get("end_s", "") or "")]
            lines.append(",".join(base))
        zf.writestr("materials.csv", "\n".join(lines))
        sp = []
        for p in pkg.get("splice_plan", []):
            mt = p.get("mount") if isinstance(p.get("mount"), dict) else {}
            mount_txt = "挂载[%s/%s/%s]" % (mt.get("search_word", "") or "-", mt.get("app_name", "") or "-", mt.get("overlay_text", "") or "-")
            win = ""
            if p.get("start_s") is not None:
                win = " 窗口[%ss→%ss]" % (p.get("start_s"), p.get("end_s") if p.get("end_s") else "末")
            sp.append("%s Hook4s[%s] + Body[%s] + CTA3s[%s] %s%s -> %s" % (
                p.get("variant_id"), p.get("hook"), p.get("body"), p.get("cta"), mount_txt, win, p.get("duration_s")))
        zf.writestr("splice.txt", "\n".join(sp))
        zf.writestr("manifest.json", _json.dumps({
            "package_id": pid, "mother_id": pkg.get("mother_id"),
            "variants": len(pkg.get("variants", [])),
            "naming_rule": pkg.get("naming_rule"),
        }, ensure_ascii=False, indent=2))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name="%s.zip" % pid)


# ---- 直投 L-Port：包不用手工搬 ----
# ① 写共享挂载 /lport-lib/packages/（不依赖网络，最稳）；② 调 L-Port API 触发出片。
LPORT_API_BASE = _os.environ.get("LPORT_API_BASE", "http://host.docker.internal:8080")


def _lport_dirs():
    """L-Port 素材库挂载点（容器 /lport-lib；宿主直跑回退绝对路径）。"""
    for p in _LPORT_FLOW:
        try:
            if Path(p).is_dir():
                return Path(p)
        except OSError:
            continue
    return None


def _lport_api(path, body=None, timeout=20):
    url = LPORT_API_BASE.rstrip("/") + path
    data = _json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = _urlreq.Request(url, data=data, method="POST" if data is not None else "GET",
                          headers={"Content-Type": "application/json"} if data is not None else {})
    with _urlreq.urlopen(req, timeout=timeout) as r:
        return _json.loads(r.read().decode("utf-8"))


@bp.post("/push-lport")
def push_lport():
    """直投 L-Port：把本包写进 L-Port 收件箱，可选直接触发出片。

    body: {package_id, run=false, limit=0} → {pushed, pkg_dir, lport, job_id}
    """
    b = request.get_json(force=True, silent=True) or {}
    pid = (b.get("package_id") or "").strip()
    pkg = (_TSTORE.get("packages", {}) or {}).get(pid)
    if not pkg:
        return jsonify({"code": 4004, "msg": "包不存在，先生成"}), 404
    root = _lport_dirs()
    if root is None:
        return jsonify({"code": 4003,
                        "msg": "L-Port 素材库未挂载（/lport-lib 缺失）：先起 L-Port，或用导出ZIP手工搬"}), 400
    pkgdir = root / "packages"
    try:
        pkgdir.mkdir(parents=True, exist_ok=True)
        dst = pkgdir / ("%s.json" % pid)
        dst.write_text(_json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        return jsonify({"code": 4005, "msg": "写 L-Port 收件箱失败：%s" % e}), 500

    out = {"package_id": pid, "pushed": str(dst), "pkg_dir": str(pkgdir),
           "variants": len(pkg.get("variants", [])), "lport": None, "job_id": ""}
    if b.get("run"):
        try:
            limit = int(b.get("limit") or 0) or len(pkg.get("variants", [])) or 1
        except (TypeError, ValueError):
            limit = len(pkg.get("variants", [])) or 1
        try:
            r = _lport_api("/api/touliu/run-traffic", {"package": "%s.json" % pid, "limit": limit})
            data = (r or {}).get("data") or {}
            out["lport"] = data
            out["job_id"] = data.get("job_id", "")
        except (_urlerr.URLError, OSError, ValueError) as e:
            # 包已投递成功：触发出片失败不影响收件，到 L-Port 点「运行」即可
            out["lport"] = {"error": "触发出片失败：%s" % e}
    return ok(out)


@bp.post("/feedback")
def post_feedback():
    """复盘回流：{package_id, variant_id, ctr?, keep3s?, cvr?}，演示可复盘闭环。"""
    b = request.get_json(force=True, silent=True) or {}
    pid = (b.get("package_id") or "").strip()
    vid = (b.get("variant_id") or "").strip()
    if not pid or not vid:
        return jsonify({"code": 4001, "msg": "缺 package_id/variant_id"}), 400
    row = {"package_id": pid, "variant_id": vid,
           "ctr": float(b.get("ctr") or 0), "keep3s": float(b.get("keep3s") or b.get("keep_3s") or 0),
           "cvr": float(b.get("cvr") or 0), "created_at": int(time.time() * 1000)}
    _TSTORE.setdefault("feedbacks", []).append(row)
    _tpersist()
    return ok(row)


@bp.get("/report/<pid>")
def report(pid):
    pkg = (_TSTORE.get("packages", {}) or {}).get(pid)
    if not pkg:
        return jsonify({"code": 4004, "msg": "包不存在"}), 404
    fbs = [f for f in (_TSTORE.get("feedbacks", []) or []) if f.get("package_id") == pid]
    fbs_sorted = sorted(fbs, key=lambda r: (r.get("ctr", 0), r.get("keep3s", 0)), reverse=True)
    return ok({"package_id": pid, "feedbacks": fbs_sorted, "count": len(fbs_sorted),
               "winner": fbs_sorted[0] if fbs_sorted else None,
               "tip": "文件名即测试方向，按 hook/爽点反查哪层赢"})
