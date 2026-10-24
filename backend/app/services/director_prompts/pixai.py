"""PixAI 视频（v4.0 系列）组装：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行。纯函数。"""
import re
from .images import first_image, img_url, collect_refs, collect_refs_fell_back, REF_ROLE_PHRASE, MAX_REFS
from .text import CJK, DIALOG, strip_prefix, pixai_preformatted
from .tiers import TIERS, normalize_tier, water_clause
from .genmode import normalize_gen_mode, infer_gen_mode, resolve_gen_mode, GEN_MODE_REF

PIXAI_CAM = {
    "固定": "fixed shot, the camera holds still",
    "推": "the camera slowly pushes in",
    "拉": "the camera pulls back to reveal the composition",
    "摇": "the camera pans smoothly across the scene",
    "移": "the camera trucks sideways with the subject",
    "跟": "the camera tracks alongside the subject",
    "环绕": "the camera orbits the subject in a slow motion",
    "升降": "the camera cranes up",
    "手持": "handheld camera with a slight shake",
    "航拍": "the camera cranes up to a high wide view",
}

PIXAI_SFX = {
    "nsfw": "close breathing — fabric drag against the sheet — a faint creak from the bed frame",
    "sfw": "quiet room tone — a slow breath — soft fabric shift",
}
PIXAI_SFX_DEFAULT = "soft room tone — light fabric movement"
PIXAI_TONE = {
    "nsfw": "breathy, quiet, unsteady",
    "sfw": "clear, calm",
}


# PixAI 视频各型号差异（官方口径）：同一套提示词框架，但这几项按型号分叉
PIXAI_MODELS = {
    "tsubaki-video": {"label": "Tsubaki Video", "max_s": 15, "audio": True, "ref": "multi", "last": True,
                      "cam_in_prompt": True, "durations": [5, 10, 15],
                      "note": "新旗舰视频模型；多图参考 + 音频；官方文档未收录，按 v4.0 家族口径（时长档位以界面为准）"},
    "tsubaki-video-flash": {"label": "Tsubaki Video Flash", "max_s": 15, "audio": True, "ref": "multi",
                            "last": True, "cam_in_prompt": True, "durations": [5, 10, 15],
                            "note": "Tsubaki Video 的快速档；多图参考 + 音频；同上按 v4.0 家族口径"},
    "v4": {"label": "V4.0 Preview / Lite", "max_s": 15, "audio": True, "ref": "multi", "last": True,
           "cam_in_prompt": True,
           "note": "多图+参考视频；参考图是语义锚；Keyframe 与 Multi-Reference 互斥"},
    "v3.2": {"label": "V3.2", "max_s": 10, "audio": True, "ref": "startframe", "last": True,
             "cam_in_prompt": True,
             "note": "精准跟词 + 配音；首/尾帧"},
    "v3.0": {"label": "V3.0 Lite", "max_s": 10, "audio": False,
             "ref": "startframe", "last": True, "cam_in_prompt": True,
             "note": "界面上是 V3.0 Lite（复杂动作、首尾可控）；锁角色强；含舞蹈预设；无音频"},
    "v2.7": {"label": "V2.7 (High Dynamics)", "max_s": 10, "audio": False, "ref": "startframe",
             "last": False, "cam_in_prompt": False, "note": "相机走独立下拉，提示词里不要写运镜；仅首帧；无音频"},
}


def _snap_duration(raw, vcfg):
    """时长归位：有档位的型号贴最近档（并列取小），否则按上限夹。返回 (秒数, 说明或None)。"""
    try:
        raw = float(raw)
    except (TypeError, ValueError):
        raw = 5.0
    tiers = sorted(t for t in (vcfg.get("durations") or []) if t > 0)
    if tiers:
        new = min(tiers, key=lambda x: (abs(x - raw), x))
        if abs(new - raw) < 1e-6:
            return float(new), None
        return float(new), "%gs → %gs（%s档位 %s）" % (raw, new, vcfg["label"], "/".join(str(x) for x in tiers))
    new = min(max(raw, 0.5), float(vcfg["max_s"]))
    if abs(new - raw) < 1e-6:
        return new, None
    return new, "时长按 %s 上限夹到 %ss" % (vcfg["label"], vcfg["max_s"])


def apply_pixai_model_deltas(prompt_out, vcfg, duration):
    """预格式化正文也要按目标型号校准：时长上限 / 有无音频 / 运镜是否写进提示词。
    返回 (新正文, 已应用的调整清单)——清单给前端显示，便于核对。"""
    applied = []
    out = prompt_out

    def _clamp(m):
        try:
            cur = float(m.group(1))
        except (TypeError, ValueError):
            return m.group(0)
        new = min(cur, duration)
        if abs(new - cur) > 1e-6:
            if vcfg.get("durations"):
                applied.append(f"时长 {cur:g}s → {new:g}s（{vcfg['label']}档位 {'/'.join(str(x) for x in sorted(vcfg['durations']))}）")
            else:
                applied.append(f"时长 {cur:g}s → {new:g}s（{vcfg['label']} 上限 {vcfg['max_s']}s）")
        return f"[0-{new:g}s]"
    out = re.sub(r"\[0-(\d+(?:\.\d+)?)s\]", _clamp, out)
    if not vcfg["audio"]:
        if re.search(r"Voice\s*[—\-][^:：]*[:：]\s*「", out):
            out = re.sub(r"Voice\s*[—\-][^:：]*[:：]\s*「([^」]*)」",
                         lambda m: f"Her lips move in a quiet, breathy whisper: 「{m.group(1)}」", out)
            applied.append(f"{vcfg['label']} 无音频：Voice 行改为口型提示")
    if not vcfg["cam_in_prompt"]:
        before = out
        out = re.sub(r"(?:^|(?<=[.\s]))The camera [^.]*\.\s*", "", out)
        if out != before:
            applied.append(f"{vcfg['label']} 运镜走相机下拉：已删除正文中的运镜句")
    return " ".join(out.split()), applied


def build_pixai(shot, character=None, locks=None, style_bible="", tier="", mode="startframe", video_model="tsubaki-video", fallback_refs=None, assume_complete=False):
    """PixAI v4.0 系列格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行。
    mode='startframe' 走 Keyframe（锁首帧构图）；'reference' 走 Multi-Reference（只锚身份，动作自由）。
    fallback_refs：镜级一张图都没有时的兜底（角色立绘 / 本集参考图），按 Multi-Reference 用。
    assume_complete=True 按意图组装（缺图不降级）：提示词假设关键图已存在，
    缺的槽位留占位并记进 ref_note（首帧待生成/尾帧待生成），只给导演页预览用；
    实际投产（导出包/直投）仍走默认结算口径。"""
    """PixAI v4.0 系列格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行。
    mode='startframe' 走 Keyframe（锁首帧构图）；'reference' 走 Multi-Reference（只锚身份，动作自由）。
    fallback_refs：镜级一张图都没有时的兜底（角色立绘 / 本集参考图），按 Multi-Reference 用。"""
    character = character or {}
    locks = locks or []
    style = (style_bible or "").strip() or "2D anime illustration"
    tier = normalize_tier(tier or shot.get("tier") or "")
    tcfg = TIERS.get(tier)
    raw_en = strip_prefix(shot.get("duty_en") or shot.get("key_text_en") or "")
    warnings = []
    if raw_en and CJK.search(raw_en):
        raw_en = ""
    if not raw_en:
        warnings.append("缺可用英文动作（duty_en/key_text_en），beat 用 holds position 站位")
    raw_duty = raw_en or "holds position"
    pre = pixai_preformatted(raw_duty)
    duty = raw_duty if (pre or raw_duty.endswith((".", "!", "?"))) else raw_duty + "."
    if duty and not pre:
        duty = duty[0].upper() + duty[1:]

    cam = shot.get("camera") or {}
    cam_phrase = PIXAI_CAM.get((cam.get("movement") or "固定").strip(), PIXAI_CAM["固定"])
    try:
        duration = float(shot.get("duration_s") or 5)
    except (TypeError, ValueError):
        duration = 5.0
    vcfg = PIXAI_MODELS.get((video_model or "tsubaki-video").strip(), PIXAI_MODELS["tsubaki-video"])
    vkey = (video_model or "tsubaki-video").strip() if (video_model or "tsubaki-video").strip() in PIXAI_MODELS else "tsubaki-video"
    duration, _snap_note = _snap_duration(duration, vcfg)
    multi_ok = vcfg["ref"] == "multi"
    want = normalize_gen_mode(shot.get("gen_mode"))
    if assume_complete:
        # 意图口径：只认镜上意图（没写按素材推），不做缺图降级、不吃兜底；
        # 缺的槽位留占位（name 为空），提示词照全量写，缺失只记状态。
        ordered = collect_refs(shot, None)[0]
        truncated = len(ordered) > MAX_REFS
        ordered = ordered[:MAX_REFS]
        if not want:
            want = infer_gen_mode(shot)
        eff_gen, eff_mode = want, GEN_MODE_REF.get(want, "t2v")
        missing_kinds = []
        if eff_gen in ("i2v-first", "i2v-first-last"):
            if not any(x.get("kind") == "first" for x in ordered):
                ordered.insert(0, {"name": "", "kind": "first", "role": "", "desc": ""})
                missing_kinds.append("first")
        if eff_gen == "i2v-first-last":
            if not any(x.get("kind") == "last" for x in ordered):
                ordered.append({"name": "", "kind": "last", "role": "ending", "desc": ""})
                missing_kinds.append("last")
        fell_back = False
        gen_notes = []
        if eff_gen == "t2v":
            ordered = []
        elif eff_gen == "multi-ref" and not ordered:
            missing_kinds.append("ref")
        if missing_kinds:
            _miss_label = {"first": "首帧待生成", "last": "尾帧待生成"}
            gen_notes.append("、".join(_miss_label.get(k, "参考图待生成") for k in missing_kinds))
    else:
        ordered, truncated = collect_refs(shot, fallback_refs)
        fell_back = collect_refs_fell_back(shot, fallback_refs)
        # 生成方式：镜上写的 gen_mode 是 Suli 定的意图；没写时按素材推，
        # 页面默认值（mode）只在完全没有素材线索时兜底。结算再按型号能力降级。
        if not want:
            want = "multi-ref" if (mode == "reference" and ordered) else ""
        eff_gen, eff_mode, gen_notes = resolve_gen_mode(
            want, shot, multi_ok=multi_ok, last_ok=bool(vcfg.get("last")), fallback_used=fell_back)
    if eff_gen == "i2v-first-last":
        # 首尾帧只吃两张：首帧起点、尾帧收束
        ordered = [x for x in ordered if x.get("kind") in ("first", "last")][:2]
    elif eff_gen != "multi-ref":
        ordered = [x for x in ordered if x.get("kind") != "last"]
    if eff_gen == "t2v":
        ordered = []
    first = next((x for x in ordered if x.get("kind") == "first"), None) or (ordered[0] if ordered else None)
    ref_note = "；".join([n for n in gen_notes if n])
    if fell_back and eff_gen == "multi-ref":
        ref_note = ("；".join([x for x in [ref_note, "本镜无镜级图，已自动用角色立绘/本集参考图作 Multi-Reference"] if x]))
    if truncated:
        ref_note = "；".join([x for x in [ref_note, f"参考图超过 {MAX_REFS} 张上限，只取前 {MAX_REFS} 张"] if x])

    def _en_only(t):
        """英文正文不吃中文锚：角色库字段是中文时整句丢掉，身份交给 @image1 / 参考图。"""
        t = (t or "").strip()
        return "" if re.search(r"[\u3400-\u9fff]", t) else t

    identity = _en_only(character.get("anchor_en") or "") or _en_only(character.get("identity", "")) or "the character"
    anchors = ", ".join([x for x in [
        identity,
        _en_only(f"{character.get('hairstyle', '')} {character.get('face', '')}".strip()),
        _en_only((character.get("outfits_text") or "").strip()[:100]),
        ", ".join([l.get("surface_en", "") for l in locks if l.get("surface_en")])[:120] or "",
    ] if x])

    tagged = [(f"@image{i}", x) for i, x in enumerate(ordered, start=1)]
    ref_entries = [{"tag": tag, "name": x.get("name"), "kind": x.get("kind", "ref"),
                    "role": (x.get("role") or "").strip(), "desc": (x.get("desc") or "").strip(),
                    "url": img_url(x.get("name"))} for tag, x in tagged]
    lines = []
    if pre:
        lines.append(duty)
        if first and "@image" not in duty.lower():
            if first.get("kind") == "first":
                lines.insert(0, "@image1 (from the attached first frame) is the identity and composition anchor.")
            else:
                # 参考图不是首帧：按多图参考口径锚身份，不谎称首帧。
                lines.insert(0, "@image1 is the character reference throughout this video, "
                                "keeping the character exactly as in the reference.")
        tail = f"{style}, anime image-to-video"
        if tcfg and "adult" not in duty.lower():
            tail = tail + (f", {tcfg['anchor']}" if tcfg.get("anchor") else "")
        end_tag = next((tag for tag, x in tagged if x.get("kind") == "last"), "")
        if eff_gen == "i2v-first-last" and end_tag:
            lines.append(f"The clip must end exactly on {end_tag}.")
        prompt_out = re.sub(r"\n{3,}", "\n\n", "\n\n".join(lines + ["", tail + "."]))
        prompt_out, applied_deltas = apply_pixai_model_deltas(prompt_out, vcfg, duration)
        locks_hit = [l.get("id") for l in locks
                     if l.get("surface_en") and l["surface_en"].lower() in prompt_out.lower()]
        return {"shot_id": shot.get("id", ""), "mode": "PixAI-I2V", "engine": "pixai",
                "video_model": vkey, "video_model_label": vcfg["label"], "video_note": vcfg["note"],
                "ref_mode": eff_mode, "gen_mode": want or infer_gen_mode(shot),
                "gen_mode_eff": eff_gen, "preformatted": True,
                "fallback_used": fell_back, "applied": applied_deltas,
                "refs": ref_entries, "ref_note": ref_note,
                "tier": tier, "tier_label": (tcfg or {}).get("label", ""),
                "missing_image": (eff_gen != "t2v" and not bool(first and first.get("name"))),
                "first_image": first.get("name") if first else "",
                "first_image_url": img_url(first.get("name")) if first else "",
                "duration_s": duration, "prompt": prompt_out[:2000], "locks_hit": locks_hit, "warnings": warnings}
    if first:
        if eff_mode == "reference":
            lines.append(f"@image1 is the character reference throughout this video, keeping {anchors} "
                         f"exactly as in the reference.")
        else:
            lines.append(f"@image1 is the first frame and the identity anchor — keep {anchors} "
                         f"and the composition of @image1 unchanged at the start.")
    else:
        lines.append(f"{anchors} as the subject of the clip.")
    if eff_gen in ("multi-ref", "i2v-first-last"):
        for tag, x in tagged:
            if x is first:
                continue
            role = (x.get("role") or "").strip()
            if not role and x.get("kind") == "last":
                role = "ending"
            desc = (x.get("desc") or "").strip()
            if desc and CJK.search(desc):
                warnings.append(f"{tag} 描述含中文已丢弃，只留角色位")
                desc = ""
            phrase = REF_ROLE_PHRASE.get(role, "reference")
            if desc:
                lines.append(f"{tag} — {phrase} reference: {desc}.")
            else:
                lines.append(f"{tag} — {phrase} reference (see attached image).")

    cam_txt = f" {cam_phrase.capitalize()}" if vcfg["cam_in_prompt"] else ""
    beat = f"[0-{duration:g}s] {duty}{cam_txt}"
    duty_l = duty.lower()
    dup_tier = any(k in duty_l for k in ("adult", "pressed flush", "slow rhythm", "mutually"))
    if tcfg and not dup_tier:
        beat += f". {tcfg['clause']}"
    else:
        beat += "."
    w_clause = water_clause(shot.get("water_level")) if tier == "nsfw" else ""
    if w_clause:
        beat = beat.rstrip(".") + ". " + w_clause
    carry_bits = []
    if eff_gen in ("multi-ref", "i2v-first-last"):
        for tag, x in tagged:
            if x is first:
                continue
            role = (x.get("role") or "").strip() or ("ending" if x.get("kind") == "last" else "")
            carry_bits.append(f"the {REF_ROLE_PHRASE.get(role, 'reference')} from {tag}")
    if carry_bits:
        beat = beat.rstrip(".") + ". Carry " + " and ".join(carry_bits) + " into this shot."
    if eff_gen == "i2v-first-last":
        end_tag = next((tag for tag, x in tagged if x.get("kind") == "last"), "")
        if end_tag:
            beat = beat.rstrip(".") + f". The clip must end exactly on {end_tag}."
    lines.append("")
    lines.append(beat if beat.endswith(".") else beat + ".")

    sound = (shot.get("sound") or "").strip()
    if sound:
        m = DIALOG.match(sound)
        if m:
            who, line = m.group(1).strip(), m.group(2).strip()
            tone = PIXAI_TONE.get(tier, "clear, calm")
            lines.append("")
            if vcfg["audio"]:
                lines.append(f"Voice — {tone}: 「{line}」")
            else:
                lines.append(f"Her lips move in a quiet, breathy whisper: 「{line}」")
        elif CJK.search(sound):
            warnings.append("中文 SFX 已丢弃，走默认英文 SFX")
            sound = ""
        else:
            lines.append("")
            lines.append(f"SFX: {sound}")
    sfx = PIXAI_SFX.get(tier, PIXAI_SFX_DEFAULT)
    if not (sound and not DIALOG.match(sound)):
        lines.append("")
        lines.append(f"SFX: {sfx}")
    lines.append("")
    tail = f"{style}, anime image-to-video"
    if tcfg and "adult" not in duty_l:
        tail = tail + (f", {tcfg['anchor']}" if tcfg.get("anchor") else "")
    lines.append(tail + ".")

    prompt = "\n".join(lines).strip()
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)[:2000]
    locks_hit = [l.get("id") for l in locks if l.get("surface_en") and l["surface_en"].lower() in prompt.lower()]
    applied_deltas = [_snap_note] if _snap_note else []
    if vcfg["max_s"] < duration:
        applied_deltas.append(f"时长按 {vcfg['label']} 上限夹到 {vcfg['max_s']}s")
    if not vcfg["audio"] and sound and DIALOG.match(sound):
        applied_deltas.append(f"{vcfg['label']} 无音频：台词改为口型提示")
    if not vcfg["cam_in_prompt"]:
        applied_deltas.append(f"{vcfg['label']} 运镜走相机下拉：正文不写运镜")
    return {"shot_id": shot.get("id", ""), "mode": "PixAI-I2V", "engine": "pixai",
            "video_model": vkey, "video_model_label": vcfg["label"], "video_note": vcfg["note"],
            "applied": applied_deltas,
            "refs": ref_entries, "ref_note": ref_note,
            "ref_mode": eff_mode,
            "gen_mode": want or infer_gen_mode(shot),
            "gen_mode_eff": eff_gen,
            "fallback_used": fell_back,
            "tier": tier, "tier_label": (tcfg or {}).get("label", ""),
            "missing_image": (eff_gen != "t2v" and not bool(first and first.get("name"))),
            "first_image": first.get("name") if first else "",
            "first_image_url": img_url(first.get("name")) if first else "",
            "duration_s": duration, "prompt": prompt, "locks_hit": locks_hit, "warnings": warnings}


# 兼容旧名
_apply_pixai_model_deltas = apply_pixai_model_deltas
