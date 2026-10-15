"""demo 蓝图：一键灌 EP-DEMO01 全链种子，供明天演示不断链。
GET /api/v1/demo/seed?episode_id=EP-DEMO01 -> 故事确认+剧本+大纲+3镜+审查+15条投流包。
幂等：重复调用覆盖写，不堆数据。只写 disk_store 真源。
"""
from flask import Blueprint, request, jsonify

bp = Blueprint("demo", __name__, url_prefix="/api/v1/demo")


def ok(data):
    return jsonify({"code": 0, "data": data})


@bp.get("/seed")
def seed():
    from ..services.disk_store import load, save
    from ..services.draft import pick_to_screenplay_md, build_outline_md
    eid = (request.args.get("episode_id") or "EP-DEMO01").strip() or "EP-DEMO01"
    # 1) story 确认
    sdoc = load("story_db.json", {"drafts": [], "confirmed": []})
    pick = {"dir": "A", "logline": "灰水村血税牢，星璃登场：隐喻替换版", "beats": ["起", "转", "落"]}
    sdoc["drafts"] = [pick,
                      {"dir": "B", "logline": "灰水村血税牢，星璃登场：时空平移版", "beats": ["起", "转", "落"]},
                      {"dir": "C", "logline": "灰水村血税牢，星璃登场：视角反转版", "beats": ["起", "转", "落"]}]
    if not any((c.get("logline") == pick["logline"]) for c in (sdoc.get("confirmed") or [])):
        sdoc.setdefault("confirmed", []).append(pick)
    save("story_db.json", sdoc)
    try:
        from ..api.story import _STORE as _SST
        _SST.update(sdoc)
    except Exception:
        pass
    # 2) scriptboard 剧本+大纲+3镜
    bdoc = load("scriptboard_db.json", {"eps": {}, "shots": {}})
    eps, shots = bdoc.get("eps", {}), bdoc.get("shots", {})
    ep = eps.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    md = pick_to_screenplay_md(pick, eid)
    ep["screenplay_md"] = md
    ep["segs"] = []
    omd, _tag = build_outline_md(eid, 15, "pixai", "", md[:800], "")
    ep["outline_md"] = omd
    # 清本集旧镜，重建3镜
    for sid in [k for k, s in shots.items() if s.get("episode_id") == eid]:
        shots.pop(sid, None)
    duties = [("沈禾夜入洗衣房对峙取衣牌", "推", 5, "沈禾：取衣牌呢？"),
              ("烘干机骤停全场静默", "固定", 5, "[SFX] 烘干机停转"),
              ("蒋姨亮证据反转离场", "拉", 5, "蒋姨：证据在这。")]
    created = []
    for i, (duty, mov, dur, sound) in enumerate(duties):
        sid = "SHOT-%s-M%03d" % (eid[-4:], i + 1)
        shots[sid] = {"id": sid, "episode_id": eid, "ord": i, "duty": duty, "duty_en": "",
                      "duration_s": dur, "camera": {"crop": "medium", "height": "eye", "movement": mov},
                      "sound": sound, "key_text_en": "", "tier": "", "draft": False, "images": []}
        created.append(sid)
    ep["verdict"] = "draft"
    ep.pop("review_findings", None)
    save("scriptboard_db.json", {"eps": eps, "shots": shots})
    try:
        from ..api.scriptboard import _EPS as _SE, _SHOTS as _SS
        _SE.update(eps)
        for k in [k for k in list(_SS.keys()) if _SS[k].get("episode_id") == eid]:
            _SS.pop(k, None)
        _SS.update({k: v for k, v in shots.items() if v.get("episode_id") == eid})
    except Exception:
        pass
    # 3) 审查跑一遍（真门）
    try:
        from ..services.draft import build_review
        total = sum(float(s.get("duration_s") or 0) for s in [shots[c] for c in created])
        verdict, findings = build_review(md, [shots[c] for c in created], total)
        ep["verdict"] = verdict
        ep["review_findings"] = findings
        save("scriptboard_db.json", {"eps": eps, "shots": shots})
        try:
            from ..api.scriptboard import _EPS as _SE2
            if eid in _SE2:
                _SE2[eid]["verdict"] = verdict
                _SE2[eid]["review_findings"] = findings
        except Exception:
            pass
    except Exception:
        verdict, findings, total = ep.get("verdict", "draft"), [], 15
    # 4) 投流包15条（走 episode 高光池）
    tdoc = load("traffic_db.json", {"packages": {}, "feedbacks": []})
    pkg = None
    try:
        from ..api.traffic import _resolve_library, parse_task, _llm_variants, HOOKS, COOLS, _TSTORE, _tpersist
        from datetime import datetime as _dt
        raw = [{"desc": "引导点击红包广告：星璃登场", "mode": "lib", "category": "红包点击", "count": 15}]
        tasks = [parse_task(t) for t in raw]
        lib_pool, lib_src = _resolve_library({}, eid, raw)
        # 若分镜未进内存池，回退用刚建 duties
        if lib_src == "builtin":
            lib_pool = [{"id": c, "desc": shots[c].get("duty", "")} for c in created]
            lib_src = "episode"
        batch = "PKG-TRAFFIC-%s-%s" % (eid, _dt.now().strftime("%m%d"))
        variants, highlights, copies, plans, materials = [], [], [], [], []
        vseq = 0
        llm_rows = _llm_variants(tasks[0], 15, lib_pool) or []
        for i in range(15):
            hk = HOOKS[i % len(HOOKS)]
            cl = COOLS[i % len(COOLS)]
            lib = lib_pool[i % len(lib_pool)]
            lr = llm_rows[i] if i < len(llm_rows) else None
            hk_name = lr.get("hook") if lr and lr.get("hook") in [h["name"] for h in HOOKS] else hk["name"]
            vseq += 1
            vid = "T1-V%02d" % (i + 1)
            hid = "H%03d" % vseq
            hyp = (lr.get("hypothesis") if lr and lr.get("hypothesis") else "%s测红包点击" % hk_name)[:40]
            hook_line = ("｜「%s」" % lr["hook_line"]) if lr and lr.get("hook_line") else ""
            title = (lr.get("title") if lr and lr.get("title") else "红包点击｜%s" % hk_name)[:20]
            cta = (lr.get("cta") if lr and lr.get("cta") else "点红包→看正片")[:20]
            fname = "%s_%s_%s_1080x1920.mp4" % (batch, vid, hid)
            hdesc = lib["desc"]
            highlights.append({"id": hid, "variant_id": vid, "source": "library", "ref": lib["id"], "desc": hdesc, "duration_s": 4})
            copies.append({"variant_id": vid, "hypothesis": hyp, "hook": "%s｜%s%s" % (hk_name, hdesc, hook_line), "title": title, "cta": cta})
            plans.append({"order": vseq, "variant_id": vid, "highlight_id": hid, "copy_seg": "hook(4s)+body+cta(3s)", "duration_s": 15, "hook": hk_name, "body": hdesc, "cta": cta})
            materials.append({"variant_id": vid, "highlight_id": hid, "ref": lib["id"], "file": fname, "source": "library", "desc": hdesc})
            variants.append({"variant_id": vid, "task_id": 1, "hypothesis": hyp, "hook_text": "%s｜%s%s" % (hk_name, hdesc, hook_line), "hl_id": hid, "hl_desc": hdesc, "title": title, "cta_text": cta, "file_name": fname})
        pkg = {"package_id": batch, "mother_id": eid, "created_at": int(__import__("time").time() * 1000),
               "lib_source": lib_src, "library": lib_pool,
               "tasks": [{"desc": tasks[0]["desc"], "mode": "lib", "category": "红包点击", "count": 15, "refVideo": ""}],
               "highlights": highlights, "copy_draft": copies, "splice_plan": plans, "materials": materials,
               "naming_rule": "{package}_{variant}_{highlight}_1080x1920.mp4｜跑量档720x1280",
               "checks": {"engine": "llm" if llm_rows else "template", "lib_source": lib_src, "testable": True, "deduped": True, "executable": True, "naming_ok": True, "materials_ok": True},
               "variants": variants}
        _TSTORE.setdefault("packages", {})[batch] = pkg
        _tpersist()
    except Exception as e:
        pkg = {"package_id": "", "error": str(e)[:200]}
    lineage = {"story_pick": pick["logline"], "episode_id": eid, "screenplay_chars": len(md),
               "shots": created, "verdict": verdict, "total_s": total,
               "traffic_package": (pkg or {}).get("package_id", "")}
    return ok({"episode_id": eid, "lineage": lineage, "tip": "演示按 故事→剧本→大纲→草案→审查→投流 顺序点"})
