"""reports 蓝图：分析报告库（拉片 / 深度拆解），文件式一报告一 JSON。

- dsh run 完成时由 dsh.py 自动入库（消息含【拉片请求】/【深度拉片请求】就存），
  不依赖前端存活——浏览器关了、刷新了，报告照样进库。
- 拉片室「报告」页：列表 / 详情 / 删除（复制走详情）。
- 存储：data/reports/<id>.json（id = rep-<yyyymmdd-HHMMSS>-<hex>；report_md 全文 + meta 平铺）。
"""
import json
import re
import secrets
import time
from pathlib import Path

from flask import Blueprint, request, jsonify

bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")
ROOT = Path(__file__).resolve().parents[2] / "data" / "reports"
_ID_RE = re.compile(r"^rep-[0-9a-z\-]{6,64}$")
_META_KEYS = ("id", "title", "kind", "source", "model", "episode_id", "run_id", "created_at", "chars", "image_count")

_TEARDOWN_DEEP = "【深度拉片请求】"
_TEARDOWN_LITE = "【拉片请求】"
_SRC_RE = re.compile(r"参考片[:：]\s*([^（(）)\n]{1,140})")
_IMG_RE = re.compile(r"/api/images/([A-Za-z0-9._\-]{1,120}\.(?:jpg|jpeg|png|webp))")


def ok(data):
    return jsonify({"code": 0, "data": data})


def parse_teardown_message(message):
    """拉片请求消息 → (kind, source)；不是拉片请求 → (None, '')。"""
    m = message or ""
    if _TEARDOWN_DEEP in m:
        kind = "deep"
    elif _TEARDOWN_LITE in m:
        kind = "lite"
    else:
        return None, ""
    mo = _SRC_RE.search(m)
    return kind, (mo.group(1).strip() if mo else "")


def save_report(report_md, kind="lite", source="", model="", episode_id="", run_id="", title=""):
    """入库一份报告 → meta dict；空正文/异常返回 None（绝不抛，调用方可忽略）。"""
    try:
        md = (report_md or "").strip()
        if not md:
            return None
        k = kind if kind in ("deep", "lite") else "lite"
        rid = "rep-%s-%s" % (time.strftime("%Y%m%d-%H%M%S"), secrets.token_hex(3))
        src = (source or "").strip()
        # 报告内嵌图（Agent 写的 /api/images/<name> 配图）→ 抽成索引，供前端「帧带」浏览
        imgs = []
        for name in _IMG_RE.findall(md):
            if name not in imgs:
                imgs.append(name)
        meta = {
            "id": rid,
            "title": (title or "").strip() or (src or "未命名") + (" · 详细设计报告（复刻规格版）" if k == "deep" else " · 拉片报告"),
            "kind": k,
            "source": src,
            "model": (model or "").strip(),
            "episode_id": (episode_id or "").strip(),
            "run_id": (run_id or "").strip(),
            "created_at": int(time.time() * 1000),
            "chars": len(md),
            "image_count": len(imgs),
            "images": imgs[:400],
            "report_md": md,
        }
        ROOT.mkdir(parents=True, exist_ok=True)
        (ROOT / ("%s.json" % rid)).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        return {key: meta[key] for key in _META_KEYS}
    except Exception:
        return None


@bp.get("")
@bp.get("/")
def report_list():
    """报告列表（meta，新在前）；?kind=deep|lite 过滤，?limit= 阀 1-500。"""
    kind = (request.args.get("kind") or "").strip()
    try:
        limit = max(1, min(500, int(request.args.get("limit") or 200)))
    except (ValueError, TypeError):
        limit = 200
    ROOT.mkdir(parents=True, exist_ok=True)
    items = []
    for f in ROOT.glob("rep-*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append({key: d.get(key) for key in _META_KEYS})
    items.sort(key=lambda x: x.get("created_at") or 0, reverse=True)
    if kind in ("deep", "lite"):
        items = [i for i in items if i.get("kind") == kind]
    return ok({"count": len(items), "items": items[:limit]})


@bp.get("/<rid>")
def report_get(rid):
    if not _ID_RE.match(rid or ""):
        return jsonify({"code": 4001, "msg": "非法报告 id"}), 400
    p = ROOT / ("%s.json" % rid)
    if not p.is_file():
        return jsonify({"code": 4004, "msg": "报告不存在"}), 404
    try:
        return ok(json.loads(p.read_text(encoding="utf-8")))
    except Exception as e:
        return jsonify({"code": 5001, "msg": "报告读取失败: %s" % str(e)[:120]}), 500


@bp.delete("/<rid>")
def report_delete(rid):
    if not _ID_RE.match(rid or ""):
        return jsonify({"code": 4001, "msg": "非法报告 id"}), 400
    p = ROOT / ("%s.json" % rid)
    if not p.is_file():
        return jsonify({"code": 4004, "msg": "报告不存在"}), 404
    try:
        p.unlink()
    except Exception as e:
        return jsonify({"code": 5001, "msg": "删除失败: %s" % str(e)[:120]}), 500
    return ok({"deleted": rid})


@bp.post("")
@bp.post("/")
def report_create():
    """手动补存（导入/测试）：body {report_md, kind?, source?, model?, episode_id?, run_id?, title?}。"""
    b = request.get_json(force=True, silent=True) or {}
    meta = save_report(b.get("report_md") or "", kind=b.get("kind") or "lite",
                       source=b.get("source") or "", model=b.get("model") or "",
                       episode_id=b.get("episode_id") or "", run_id=b.get("run_id") or "",
                       title=b.get("title") or "")
    if not meta:
        return jsonify({"code": 4001, "msg": "report_md 为空或写入失败"}), 400
    return ok(meta)
