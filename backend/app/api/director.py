"""director 蓝图（薄路由层）：8-block组装+锁注入（纯文本，不直连生成）。
组装纯函数已拆到 services/director_prompts/（still/h3/pixai/tiers/images/text），
跨蓝图读取一律走 services/repo.py。本文件只剩路由 + 导出包 ZIP。
"""
from flask import Blueprint, request, jsonify, send_file, Response

from ..services.director_prompts import (
    TIERS, tier_list, build_prompt, build_i2va, build_pixai,
    PIXAI_MODELS, shot_images, first_image, img_url,
)
from ..services import repo as _repo

bp = Blueprint("director", __name__, url_prefix="/api/v1/director")


def ok(data):
    return jsonify({"code": 0, "data": data})


@bp.post("/prompts/assemble")
def assemble():
    b = request.get_json(force=True) or {}
    shots = b.get("shots", [])
    style = b.get("style_bible", "")
    character = b.get("character") or {}
    locks = b.get("locks") or []
    out = []
    for s in shots:
        shot = s if isinstance(s, dict) else {"id": s, "duty": s, "camera": {}}
        sid = shot.get("id", s)
        r = build_prompt(shot, character, locks, style)
        out.append({"shot_id": sid, **r, "unresolved_refs": []})
    return ok({"prompts": out, "tip": "复制到 ComfyUI/MJ/即梦/可灵手工生产，本系统不直连生成"})


@bp.get("/tiers")
def tiers():
    """分级清单 sfw/nsfw（前端档位选择器与交付包共用的唯一真源）。"""
    return ok(tier_list())


@bp.get("/engines")
def engines():
    """组装目标引擎清单：h3=MiniMax H3 字段格式；pixai=PixAI 视频（v4.0 系列）格式。"""
    return ok([
        {"key": "h3", "label": "MiniMax H3"},
        {"key": "pixai", "label": "PixAI 视频",
         "models": [{"key": k, "label": v["label"], "max_s": v["max_s"], "audio": v["audio"],
                     "ref": v["ref"], "cam_in_prompt": v["cam_in_prompt"], "note": v["note"]}
                    for k, v in PIXAI_MODELS.items()]},
    ])


@bp.post("/prompts/assemble-i2va")
def assemble_i2va():
    """单图动画组装：每镜独立一段（有首帧直出 / 缺首帧回退）。
    body {shots, character, locks, style_bible, music, tier, engine: h3|pixai, ref_mode: startframe|reference}"""
    b = request.get_json(force=True) or {}
    shots = b.get("shots", [])
    style = b.get("style_bible", "")
    music = b.get("music", "")
    tier = (b.get("tier") or "").strip()
    engine = (b.get("engine") or "h3").strip()
    ref_mode = (b.get("ref_mode") or "startframe").strip()
    video_model = (b.get("pixai_model") or b.get("video_model") or "tsubaki-video").strip()
    character = b.get("character") or {}
    locks = b.get("locks") or []
    if engine == "pixai":
        out = [build_pixai(_repo.resolve_shot(s), character, locks, style, tier, ref_mode, video_model) for s in shots]
    else:
        out = [build_i2va(_repo.resolve_shot(s), character, locks, style, music, tier) for s in shots]
    return ok({"prompts": out, "count": len(out), "tier": tier, "engine": engine, "ref_mode": ref_mode,
               "tip": "I2VA=首帧直出；T2VA-fallback=该镜缺首帧，回分镜页补传后重组"})


@bp.post("/prompts/assemble-i2va-episode/<eid>")
def assemble_i2va_episode(eid):
    """按集批量单图组装：取 scriptboard 实镜（含首帧），逐镜一段视频。"""
    b = request.get_json(force=True) or {}
    style = b.get("style_bible", "")
    music = b.get("music", "")
    tier = (b.get("tier") or "").strip()
    engine = (b.get("engine") or "h3").strip()
    ref_mode = (b.get("ref_mode") or "startframe").strip()
    video_model = (b.get("pixai_model") or b.get("video_model") or "tsubaki-video").strip()
    locks = b.get("locks") or []
    chars = list(_repo.chars_map().values())
    character = b.get("character") or (chars[0] if chars else {})
    rows = _repo.list_shots_by_episode(eid)
    if engine == "pixai":
        out = [build_pixai(s, character, locks, style, tier, ref_mode, video_model) for s in rows]
    else:
        out = [build_i2va(s, character, locks, style, music, tier) for s in rows]
    total = round(sum(float(p["duration_s"]) for p in out), 1)
    return ok({"episode_id": eid, "count": len(out), "total_s": total, "tier": tier,
               "engine": engine, "ref_mode": ref_mode, "prompts": out})


@bp.post("/prompts/assemble-episode/<eid>")
def assemble_episode(eid):
    """按集组装：从 scriptboard 取 shots，character 取首角色。"""
    b = request.get_json(force=True) or {}
    style = b.get("style_bible", "")
    locks = b.get("locks") or []
    chars = list(_repo.chars_map().values())
    character = chars[0] if chars else {}
    rows = [s for s in _repo.shots_map().values() if s.get("episode_id") == eid]
    out = []
    for shot in sorted(rows, key=lambda x: x.get("id", "")):
        r = build_prompt(shot, character, locks, style)
        out.append({"shot_id": shot.get("id"), **r, "unresolved_refs": []})
    return ok({"episode_id": eid, "count": len(out), "prompts": out})


@bp.get("/export")
def export():
    """去程交付包（对齐 POSITIONING §2）：package_id + shots + locks + review。"""
    import time as _time
    eid = request.args.get("episode_id", "")
    style = request.args.get("style_bible", "")
    ep = _repo.get_episode(eid)
    chars = list(_repo.chars_map().values())
    character = chars[0] if chars else {}
    rows = sorted([s for s in _repo.shots_map().values() if not eid or s.get("episode_id") == eid],
                  key=lambda x: x.get("id", ""))
    shots = []
    for shot in rows:
        r = build_prompt(shot, character, [], style)
        imgs = shot_images(shot)
        first = first_image(shot)
        shots.append({"id": shot.get("id"), "assembled_en": r["assembled_en"],
                      "locks_hit": r["locks_hit"],
                      "visual_basis": ([f"首帧 {img_url(first.get('name'))}"] if first else []),
                      "images": [{"name": x.get("name"), "kind": x.get("kind", "ref"),
                                  "url": img_url(x.get("name"))} for x in imgs],
                      "first_image": first.get("name") if first else "",
                      "first_image_url": img_url(first.get("name")) if first else "",
                      "duration_s": shot.get("duration_s", 0),
                      "sound": shot.get("sound", ""),
                      "tier": (shot.get("tier") or ""),
                      "camera": shot.get("camera", {}),
                      "boundaries": {"start": shot.get("start_boundary", {}),
                                     "end": shot.get("end_boundary", {})}})
    pkg = {
        "package_id": f"PKG-{eid or 'NA'}-{int(_time.time())}",
        "episode_id": eid, "verdict": ep.get("verdict", "draft"),
        "shots": shots, "locks": [], "images_base": "/api/images/",
        "review": {"verdict": ep.get("verdict", "draft"), "findings": []},
    }
    return ok(pkg)


@bp.get("/export-bundle")
def export_bundle():
    """去程交付包·文件夹版（对齐 POSITIONING §2 草案形态）：一次下载一个 ZIP，
    内含 manifest.json + character.md/json + ref_image/ + screenplay_draft.md + outline.md +
    beats.json + shots.json + images/ + prompts/。复制即交付，sha 对不上停手。
    query: episode_id, character_id(空=首个角色), engine=h3|pixai(默认pixai),
           pixai_model/video_model, tier, note(方向说明,写入manifest)."""
    import io as _io
    import time as _time
    import hashlib as _hashlib
    import zipfile as _zipfile
    import datetime as _dt
    from pathlib import Path as _Path

    eid = request.args.get("episode_id", "")
    cid = request.args.get("character_id", "")
    engine = (request.args.get("engine") or "pixai").strip() or "pixai"
    video_model = (request.args.get("pixai_model") or request.args.get("video_model") or "tsubaki-video").strip()
    tier = (request.args.get("tier") or "").strip()
    note = (request.args.get("note") or "").strip()[:500]

    ep = _repo.get_episode(eid)
    chars_map = _repo.chars_map()
    chars = list(chars_map.values())
    character = chars_map.get(cid) if cid else (chars[0] if chars else {})
    cid = character.get("id", cid)
    slot_prompts = _repo.slot_prompts_map()
    docs = _repo.character_docs_map()
    dims = _repo.character_dims()
    story = _repo.story_store()
    rows = sorted([s for s in _repo.shots_map().values() if not eid or s.get("episode_id") == eid],
                  key=lambda x: x.get("id", ""))
    uploads = _Path(__file__).resolve().parents[2] / "data" / "uploads"
    pkg_id = f"PKG-{eid or 'NA'}-{int(_time.time())}"

    files = {}   # path -> bytes
    missing = []

    def add_file(path, data):
        files[path] = data if isinstance(data, bytes) else str(data).encode("utf-8")

    def add_upload(name, dest):
        name = _Path(name or "").name
        src = uploads / name
        if name and src.is_file():
            add_file(dest, src.read_bytes())
        elif name:
            missing.append(dest)

    # 1) 角色三件
    if character:
        add_file("character.md",
                 f"# {character.get('name', '')} 设定\n\n" + "\n".join(
                     f"- {k}: {character.get(k, '')}" for k in dims) + "\n")
        add_file("character.json", __import__("json").dumps({
            "id": character.get("id", ""), "name": character.get("name", ""),
            "avatar": character.get("avatar_path", ""),
            "dims": {k: character.get(k, "") for k in dims},
            "outfits_text": character.get("outfits_text", ""),
            "slot_prompts": [{"kind": k, "slot": s, "prompt": p}
                             for (cc, k, s), p in slot_prompts.items() if cc == cid],
        }, ensure_ascii=False, indent=2))
        if character.get("avatar_path"):
            add_upload(character["avatar_path"],
                       f"ref_image/{_Path(character['avatar_path']).name}")
        doc_html = (docs.get(cid) or {}).get("doc_html", "") or ""
        if doc_html.strip():
            add_file("character_doc.html", doc_html)

    # 2) 剧本方案稿 + beats
    add_file("screenplay_draft.md", ep.get("screenplay_md", "") or "")
    if (ep.get("outline_md") or "").strip():
        add_file("outline.md", ep["outline_md"])
    if ep.get("outline_image"):
        add_upload(ep["outline_image"], f"outline_image/{_Path(ep['outline_image']).name}")
    beats = []
    for pick in (story.get("confirmed") or []):
        if isinstance(pick, dict) and pick.get("beats"):
            for i, b in enumerate(pick["beats"], 1):
                beats.append({"beat_id": f"B{i:02d}",
                              "function": b if isinstance(b, str) else str(b),
                              "text_cn": ""})
    if not beats:
        try:
            from ..services.draft import parse_beats_from_screenplay
            beats = parse_beats_from_screenplay(ep.get("screenplay_md", ""), eid)
        except Exception:
            beats = []
    add_file("beats.json", __import__("json").dumps(beats, ensure_ascii=False, indent=2))

    # 3) 分镜 + 媒体 + 提示词
    shots_out, prompts_out = [], {}
    for shot in rows:
        sid = shot.get("id", "")
        shots_out.append({k: shot.get(k) for k in
                          ("id", "episode_id", "ord", "duty", "duty_en", "duration_s",
                           "camera", "sound", "key_text_en", "tier", "images", "image")})
        for x in shot_images(shot):
            if x.get("name"):
                add_upload(x["name"], f"images/{_Path(x['name']).name}")
        r = (build_pixai(shot, character, [], "", tier, "startframe", video_model)
             if engine == "pixai"
             else build_i2va(shot, character, [], "", "", tier))
        prompts_out[sid] = r["prompt"]
        add_file(f"prompts/{sid}.{engine}.txt", r["prompt"])
    add_file("shots.json", __import__("json").dumps(shots_out, ensure_ascii=False, indent=2))
    add_file("prompts.json", __import__("json").dumps(
        {"engine": engine, "video_model": video_model, "tier": tier,
         "prompts": prompts_out}, ensure_ascii=False, indent=2))

    # 4) manifest
    manifest = {
        "package_id": pkg_id,
        "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "episode_id": eid, "character_id": cid,
        "engine": engine, "video_model": video_model if engine == "pixai" else "",
        "tier": tier, "direction": note,
        "verdict": ep.get("verdict", "draft"),
        "files": [{"path": p, "bytes": len(b),
                   "sha256": _hashlib.sha256(b).hexdigest()} for p, b in sorted(files.items())],
        "missing": missing,
    }
    add_file("manifest.json", __import__("json").dumps(manifest, ensure_ascii=False, indent=2))

    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as zf:
        for p, b in sorted(files.items()):
            zf.writestr(p, b)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"{pkg_id}.zip")


@bp.get("/draft-doc")
def draft_doc():
    """方向草案文档（人工搬运给 L-Port 的可读交接件，一个 .md 文件）：
    集信息 + 方案大纲全文 + 方向草案表 + 逐镜组装提示词全文。
    query: episode_id, character_id(空=首个角色), engine=h3|pixai(默认pixai),
           pixai_model/video_model, tier。"""
    import datetime as _dt
    eid = request.args.get("episode_id", "")
    cid = request.args.get("character_id", "")
    engine = (request.args.get("engine") or "pixai").strip() or "pixai"
    video_model = (request.args.get("pixai_model") or request.args.get("video_model") or "tsubaki-video").strip()
    tier = (request.args.get("tier") or "").strip()

    ep = _repo.get_episode(eid)
    chars_map = _repo.chars_map()
    chars = list(chars_map.values())
    character = chars_map.get(cid) if cid else (chars[0] if chars else {})
    rows = _repo.list_shots_by_episode(eid)
    total = round(sum(float(s.get("duration_s") or 0) for s in rows), 1)

    L = []
    L.append(f"# 方向草案 {eid or 'NA'}")
    L.append("")
    L.append(f"- 生成时间：{_dt.datetime.now().isoformat(timespec='seconds')}")
    L.append(f"- 引擎：{engine}" + (f" / {video_model}" if engine == "pixai" else ""))
    L.append(f"- 档位：{tier or '常规'}")
    L.append(f"- 共 {len(rows)} 镜，合计 {total} 秒")
    L.append("")
    L.append("## 方案大纲")
    L.append("")
    L.append((ep.get("outline_md") or "（暂无大纲）").strip())
    L.append("")
    L.append("## 方向草案表")
    L.append("")
    L.append("| 镜号 | 内容一句话 | 时长 | 运镜 | 台词 | 分级 | 首帧 |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s in rows:
        cam = s.get("camera") or {}
        first = first_image(s)
        L.append("| " + " | ".join([
            str(s.get("id", "")),
            str(s.get("duty") or "").replace("|", "/")[:60],
            f"{s.get('duration_s', 0)}秒",
            str(cam.get("movement") or "固定"),
            str(s.get("sound") or "").replace("|", "/")[:40],
            str(s.get("tier") or "常规"),
            ("有" if first else "缺"),
        ]) + " |")
    L.append("")
    L.append("## 逐镜提示词（复制即用）")
    for s in rows:
        sid = s.get("id", "")
        r = (build_pixai(s, character, [], "", tier, "startframe", video_model)
             if engine == "pixai"
             else build_i2va(s, character, [], "", "", tier))
        L.append("")
        L.append(f"### {sid}（{r.get('mode', '')}，{r.get('duration_s', 0)}秒）")
        L.append("")
        L.append("```text")
        L.append(r["prompt"])
        L.append("```")
    L.append("")
    body = "\n".join(L)
    name = f"DRAFT-{eid or 'NA'}.md"
    return Response(body.encode("utf-8"), mimetype="text/markdown",
                    headers={"Content-Disposition": f"attachment; filename={name}"})
