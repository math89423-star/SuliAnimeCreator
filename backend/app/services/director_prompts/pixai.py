"""PixAI 视频（v4.0 系列）组装：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行。纯函数。"""
import re
from .images import first_image, img_url, collect_refs, REF_ROLE_PHRASE, MAX_REFS
from .text import DIALOG, strip_prefix, pixai_preformatted
from .tiers import TIERS

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
    "explicit": "close breathing — fabric drag against the sheet — a faint creak from the bed frame",
    "closeup": "damp skin contact — uneven breathing — a faint creak from the bed frame",
    "tease": "quiet room tone — a slow breath — soft fabric shift",
    "undress": "quiet room tone — a slow breath — fabric sliding against skin",
}
PIXAI_SFX_DEFAULT = "soft room tone — light fabric movement"
PIXAI_TONE = {
    "explicit": "breathy, quiet, unsteady",
    "closeup": "breathy, close to the mic, unsteady",
    "tease": "soft, hushed",
    "undress": "soft, a little unsteady",
}


# PixAI 视频各型号差异（官方口径）：同一套提示词框架，但这几项按型号分叉
PIXAI_MODELS = {
    "tsubaki-video": {"label": "Tsubaki Video", "max_s": 15, "audio": True, "ref": "multi", "cam_in_prompt": True,
                      "note": "新旗舰视频模型；多图参考 + 音频；官方文档未收录，按 v4.0 家族口径（时长档位以界面为准）"},
    "tsubaki-video-flash": {"label": "Tsubaki Video Flash", "max_s": 15, "audio": True, "ref": "multi",
                            "cam_in_prompt": True,
                            "note": "Tsubaki Video 的快速档；多图参考 + 音频；同上按 v4.0 家族口径"},
    "v4": {"label": "V4.0 Preview / Lite", "max_s": 15, "audio": True, "ref": "multi", "cam_in_prompt": True,
           "note": "多图+参考视频；参考图是语义锚；Keyframe 与 Multi-Reference 互斥"},
    "v3.2": {"label": "V3.2", "max_s": 10, "audio": True, "ref": "startframe", "cam_in_prompt": True,
             "note": "精准跟词 + 配音；首/尾帧"},
    "v3.0": {"label": "V3.0 Lite", "max_s": 10, "audio": False,
             "ref": "startframe", "cam_in_prompt": True,
             "note": "界面上是 V3.0 Lite（复杂动作、首尾可控）；锁角色强；含舞蹈预设；无音频"},
    "v2.7": {"label": "V2.7 (High Dynamics)", "max_s": 10, "audio": False, "ref": "startframe",
             "cam_in_prompt": False, "note": "相机走独立下拉，提示词里不要写运镜；仅首帧；无音频"},
}


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
        new = min(cur, float(vcfg["max_s"]))
        if abs(new - cur) > 1e-6:
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


def build_pixai(shot, character=None, locks=None, style_bible="", tier="", mode="startframe", video_model="tsubaki-video"):
    """PixAI v4.0 系列格式：@image1 参考行 + [0-Xs] beat + 相机动词 + Voice/SFX 行。
    mode='startframe' 走 Keyframe（锁首帧构图）；'reference' 走 Multi-Reference（只锚身份，动作自由）。"""
    character = character or {}
    locks = locks or []
    style = (style_bible or "").strip() or "2D anime illustration"
    tier = (tier or shot.get("tier") or "").strip()
    tcfg = TIERS.get(tier)
    if not tcfg:
        tier = ""
    raw_duty = strip_prefix(shot.get("duty_en") or shot.get("duty")) or "holds position"
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
    duration = min(max(duration, 0.5), float(vcfg["max_s"]))
    multi_ok = vcfg["ref"] == "multi"
    first = first_image(shot)
    ordered, truncated = collect_refs(shot)
    extras = [x for x in ordered if x is not first]
    ref_note = ""
    if truncated:
        ref_note = f"参考图超过 {MAX_REFS} 张上限，只取前 {MAX_REFS} 张"
    if extras and not multi_ok:
        ref_note += ("；" if ref_note else "") + f"{vcfg['label']}不支持多图参考，已忽略 {len(extras)} 张额外参考"
    eff_mode = mode
    if not multi_ok:
        eff_mode = "startframe"
    elif extras and mode == "startframe":
        eff_mode = "reference"
        ref_note += ("；" if ref_note else "") + f"含 {len(extras)} 张多图参考，已按 Multi-Reference 出（与 Keyframe 互斥）"

    identity = character.get("identity", "the character") or "the character"
    anchors = ", ".join([x for x in [
        identity,
        f"{character.get('hairstyle', '')} {character.get('face', '')}".strip(),
        (character.get("outfits_text") or "").strip()[:100],
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
            lines.insert(0, "@image1 (from the attached first frame) is the identity and composition anchor.")
        tail = f"{style}, anime image-to-video"
        if tcfg and "adult" not in duty.lower():
            tail += f", {tcfg['anchor']}"
        prompt_out = re.sub(r"\n{3,}", "\n\n", "\n\n".join(lines + ["", tail + "."]))
        prompt_out, applied_deltas = apply_pixai_model_deltas(prompt_out, vcfg, duration)
        locks_hit = [l.get("id") for l in locks
                     if l.get("surface_en") and l["surface_en"].lower() in prompt_out.lower()]
        return {"shot_id": shot.get("id", ""), "mode": "PixAI-I2V", "engine": "pixai",
                "video_model": vkey, "video_model_label": vcfg["label"], "video_note": vcfg["note"],
                "ref_mode": (eff_mode if (first or tagged) else "t2v"), "preformatted": True,
                "applied": applied_deltas,
                "refs": ref_entries, "ref_note": ref_note,
                "tier": tier, "tier_label": (tcfg or {}).get("label", ""),
                "missing_image": not bool(first),
                "first_image": first.get("name") if first else "",
                "first_image_url": img_url(first.get("name")) if first else "",
                "duration_s": duration, "prompt": prompt_out[:2000], "locks_hit": locks_hit}
    if first:
        if eff_mode == "reference":
            lines.append(f"@image1 is the character reference throughout this video, keeping {anchors} "
                         f"exactly as in the reference.")
        else:
            lines.append(f"@image1 is the first frame and the identity anchor — keep {anchors} "
                         f"and the composition of @image1 unchanged at the start.")
    else:
        lines.append(f"{anchors} as the subject of the clip.")
    if multi_ok:
        for tag, x in tagged:
            if x is first:
                continue
            role = (x.get("role") or "").strip()
            if not role and x.get("kind") == "last":
                role = "ending"
            desc = (x.get("desc") or "").strip()
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
    carry_bits = []
    if multi_ok:
        for tag, x in tagged:
            if x is first:
                continue
            role = (x.get("role") or "").strip() or ("ending" if x.get("kind") == "last" else "")
            carry_bits.append(f"the {REF_ROLE_PHRASE.get(role, 'reference')} from {tag}")
    if carry_bits:
        beat = beat.rstrip(".") + ". Carry " + " and ".join(carry_bits) + " into this shot."
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
        tail += f", {tcfg['anchor']}"
    lines.append(tail + ".")

    prompt = "\n".join(lines).strip()
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)[:2000]
    locks_hit = [l.get("id") for l in locks if l.get("surface_en") and l["surface_en"].lower() in prompt.lower()]
    applied_deltas = []
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
            "ref_mode": (eff_mode if (first or tagged) else "t2v"),
            "tier": tier, "tier_label": (tcfg or {}).get("label", ""),
            "missing_image": not bool(first),
            "first_image": first.get("name") if first else "",
            "first_image_url": img_url(first.get("name")) if first else "",
            "duration_s": duration, "prompt": prompt, "locks_hit": locks_hit}


# 兼容旧名
_apply_pixai_model_deltas = apply_pixai_model_deltas
