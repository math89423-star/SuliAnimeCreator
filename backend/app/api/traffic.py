"""traffic 蓝图：投流批量方案包（skill canonical 直连）。

skill：skills/traffic/traffic-batch/SKILL.md（任务 → 方案包，只出计划不生成片）。
本蓝图是该 skill 的执行器：解析四字段 → 双来源高光 → 文案草案 → 拼接计划 → 四门质检 → 命名导出。
失败永远回退本地规则，不抛 500（与 draft 轻链同纪律）。
"""
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import re
import time
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
    if auto and mother_id:
        ep_pool = _episode_library(mother_id)
        if ep_pool:
            return ep_pool, "episode"
    return list(LIB_POOL), "builtin"


def parse_task(t):
    desc = (t.get("desc") or "").strip()
    mode = t.get("mode") if t.get("mode") in ("gen", "lib") else "lib"
    category = (t.get("category") or "红包点击").strip() or "红包点击"
    try:
        count = max(1, min(120, int(t.get("count") or 15)))
    except (TypeError, ValueError):
        count = 15
    ref_video = (t.get("refVideo") or t.get("ref_video") or "").strip()
    return {"desc": desc, "mode": mode, "category": category, "count": count, "refVideo": ref_video}


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
            highlights.append({"id": hid, "variant_id": vid, "source": src, "ref": ref, "desc": hdesc, "duration_s": 4})
            copies.append({"variant_id": vid, "hypothesis": hyp, "hook": "%s｜%s%s" % (hk_name, hdesc, hook_line),
                           "title": title, "cta": cta})
            plans.append({"order": vseq, "variant_id": vid, "highlight_id": hid,
                          "copy_seg": "hook(4s)+body+cta(3s)", "duration_s": 15,
                          "hook": hk_name, "body": hdesc, "cta": cta})
            materials.append({"variant_id": vid, "highlight_id": hid, "ref": ref,
                              "file": fname, "source": src, "desc": hdesc})
            variants.append({
                "variant_id": vid, "task_id": ti + 1, "hypothesis": hyp,
                "hook_text": "%s｜%s%s" % (hk_name, hdesc, hook_line),
                "hl_id": hid, "hl_desc": hdesc,
                "title": title,
                "cta_text": cta,
                "file_name": fname,
            })
            if len(variants) >= 120:
                break
    checks = {
        "skill": "skills/traffic/traffic-batch/SKILL.md",
        "skill_version": skill_version(),
        "engine": "+".join(sorted(set(engines))) if engines else "template",
        "lib_source": lib_src,
        "testable": all(v.get("hypothesis") for v in variants),
        "deduped": len(seen) == len(variants),
        "executable": all(v.get("hl_id") and v.get("hook_text") for v in variants),
        "naming_ok": all(v["file_name"].endswith("_1080x1920.mp4") for v in variants),
        "materials_ok": len(materials) == len(variants),
    }
    pkg = {
        "package_id": batch, "mother_id": mother_id,
        "created_at": int(time.time() * 1000),
        "lib_source": lib_src,
        "library": lib_pool,
        "tasks": [{"desc": t["desc"], "mode": t["mode"], "category": t["category"], "count": t["count"], "refVideo": t["refVideo"]} for t in tasks],
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
        lines = ["variant_id,highlight_id,ref,file,source"]
        for m in pkg.get("materials", []):
            lines.append(",".join(str(m.get(k, "")) for k in ("variant_id", "highlight_id", "ref", "file", "source")))
        zf.writestr("materials.csv", "\n".join(lines))
        sp = []
        for p in pkg.get("splice_plan", []):
            sp.append("%s Hook4s[%s] + Body[%s] + CTA3s[%s] -> %s" % (
                p.get("variant_id"), p.get("hook"), p.get("body"), p.get("cta"), p.get("duration_s")))
        zf.writestr("splice.txt", "\n".join(sp))
        zf.writestr("manifest.json", _json.dumps({
            "package_id": pid, "mother_id": pkg.get("mother_id"),
            "variants": len(pkg.get("variants", [])),
            "naming_rule": pkg.get("naming_rule"),
        }, ensure_ascii=False, indent=2))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name="%s.zip" % pid)


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
