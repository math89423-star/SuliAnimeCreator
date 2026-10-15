"""H3 单图动画（I2VA / T2VA-fallback）：对齐行 + 三字段。纯函数，无 Flask、无跨蓝图导入。"""
from .images import first_image, img_url
from .text import DIALOG, CJK, PRONOUN_EN, looks_full, strip_prefix, strip_pixai_scaffold, pixai_preformatted
from .tiers import TIERS, normalize_tier
import re

I2VA_ALIGN = ("For the target video, at 0.00 seconds into the target video, "
              "<Picture 1> (from [Shot 1]) is fully referenced.")

# 分镜运镜中文 → H3 相机运动英文子句（machine-readable canonical，见 base-en.txt §4.3）
MOVEMENT_EN = {
    "固定": "holds a static shot",
    "推": "pushes in with small amplitude at slow speed",
    "拉": "pulls out with small amplitude at slow speed",
    "摇": "pans right with small amplitude at slow speed",
    "移": "trucks right with small amplitude at slow speed",
    "跟": "follows the subject with a tracking shot",
    "环绕": "arcs around the subject with small amplitude at slow speed",
    "升降": "pedestals up with small amplitude at slow speed",
    "手持": "holds with a slight handheld shake",
    "航拍": "pulls out from an aerial view with large amplitude at slow speed",
}

CROP_EN = {
    "extreme_close": "an extreme close-up", "closeup": "a close-up",
    "close": "a close shot", "medium_close": "a medium close-up",
    "medium": "a medium shot", "medium_full": "a medium-full shot",
    "full": "a full shot", "wide": "a wide shot",
    "extreme_wide": "an extreme wide shot",
}


def build_i2va(shot, character=None, locks=None, style_bible="", music="", tier=""):
    """单镜 I2VA：有首帧出 H3 全文（对齐行+三字段），无首帧回退 T2VA（无对齐行）。
    每段视频独立单镜，不跨镜拼切，时长即 shot.duration_s（H3 建议 4-15s）。
    tier 只两档 sfw/nsfw，留空即原行为（无档位子句）。"""
    character = character or {}
    locks = locks or []
    style = (style_bible or "").strip() or "2D-animated"
    tier = normalize_tier(tier or shot.get("tier") or "")
    tcfg = TIERS.get(tier)
    raw = strip_prefix(shot.get("duty_en") or shot.get("duty"))
    pre_dlg = ""
    pre_fmt = pixai_preformatted(raw)
    if pre_fmt:
        m0 = re.search(r"Voice\s*[—\-][^:：]*[:：]\s*「([^」]*)」", raw)
        pre_dlg = m0.group(1).strip() if m0 else ""
        raw = strip_pixai_scaffold(raw)
    duty = raw or "holds position"
    cam = shot.get("camera") or {}
    crop_en = CROP_EN.get(cam.get("crop", "medium"), "a medium shot")
    move_en = MOVEMENT_EN.get((cam.get("movement") or "固定").strip(), "holds a static shot")
    try:
        duration = float(shot.get("duration_s") or 5)
    except (TypeError, ValueError):
        duration = 5.0
    duration = min(max(duration, 0.5), 30.0)

    identity = character.get("identity", "young woman") or "young woman"
    appearance = f"{character.get('hairstyle', '')} {character.get('face', '')}".strip()
    outfit = (character.get("outfits_text") or "").strip()[:120]
    lock_txt = ", ".join([l.get("surface_en", "") for l in locks if l.get("surface_en")])[:200]

    anchor_bits = [identity, appearance, outfit, lock_txt]
    anchor = ", ".join([b for b in anchor_bits if b]) or identity

    first = first_image(shot)
    has_pic = bool(first)
    full = looks_full(duty)
    if has_pic:
        if full:
            framing = ("the shot keeps the composition, framing, and spatial layout established by <Picture 1>, "
                       "along with every identity, outfit, and prop anchor visible in the reference")
        else:
            framing = (f"{crop_en} frames the subject shown in <Picture 1>, preserving "
                       f"{anchor}, and the composition and spatial layout established by <Picture 1>")
    else:
        if full:
            framing = ("the shot continues the same scene, characters, outfit state, and prop state "
                       "established by the previous shot")
        else:
            framing = f"{crop_en} frames {anchor} in its establishing composition"

    carry = f" while keeping {outfit}" if outfit else ""

    sound = (shot.get("sound") or "").strip()
    dlg_clause = ""
    snd_hint = ""
    if not sound and pre_dlg:
        who = "the speaker"
        sound = f"{who}：{pre_dlg}"
    if sound:
        m = DIALOG.match(sound)
        if m:
            who, line = m.group(1).strip(), m.group(2).strip()
            lang = "Chinese" if CJK.search(line) else "English"
            if who in PRONOUN_EN:
                speaker = PRONOUN_EN[who][0].upper() + PRONOUN_EN[who][1:]
            elif CJK.search(who):
                speaker = f"the speaker {who}"
            else:
                speaker = f"The {who}"
            dlg_clause = (f" {speaker} with a clear voice (S1) says: "
                          f"<d>[{lang}] {line}</d>")
            snd_hint = ""
        else:
            snd_hint = f"{sound} is heard over soft ambient tone with faint fabric movement."
    key_en = (shot.get("key_text_en") or "").strip()
    key_clause = f" {key_en}." if key_en and key_en not in duty else ""

    duty_l = duty.lower()
    tier_clause = f" {tcfg['clause']}" if (tcfg and not full) else ""
    anchor_dup = bool(tcfg and tcfg.get("anchor")) and tcfg["anchor"].split(",")[0].strip().lower() in duty_l
    head = f"{style}, {tcfg['anchor']}" if (tcfg and tcfg.get("anchor") and not anchor_dup) else style
    cam_clause = "" if pre_fmt else f"The camera {move_en}. "
    if full:
        body = duty if duty.endswith((".", "!", "?")) else duty + "."
        body = body[0].upper() + body[1:]
        imm = (f"[Shot 1] {head}, {framing}.{tier_clause} "
               f"{cam_clause}{body}{key_clause}{dlg_clause}")
    else:
        imm = (f"[Shot 1] {head}, {framing}.{tier_clause} "
               f"The camera {move_en} as the subject {duty}{carry}.{key_clause}{dlg_clause}")
    imm = " ".join(imm.split())[:1200]

    if snd_hint:
        soundscape = snd_hint
    elif tier == "nsfw":
        soundscape = ("Close breathing overlaps in a slow rhythm, joined by fabric drag against the sheet "
                      "and a faint creak from the bed frame.")
    elif tier == "sfw":
        soundscape = ("Quiet room tone continues under a slow breath, with the soft drag of fabric "
                      "against skin and a faint rustle of the sheet.")
    elif dlg_clause:
        soundscape = "Dialogue is heard over soft room tone with faint fabric movement."
    else:
        soundscape = ("Soft ambient tone continues with faint fabric movement and "
                      "subtle action sounds matching the visible motion.")
    if dlg_clause and not snd_hint and tier == "nsfw":
        soundscape += " The spoken line stays close and breathy just above it."
    music_txt = (music or "").strip() or "N/A"

    if has_pic:
        prompt = (f"{I2VA_ALIGN}\n\n"
                  f"integrated_multimodal_description: {imm}\n\n"
                  f"overall_soundscape: {soundscape}\n\n"
                  f"non_diegetic_music: {music_txt}")
        mode = "I2VA"
    else:
        prompt = (f"integrated_multimodal_description: {imm}\n\n"
                  f"overall_soundscape: {soundscape}\n\n"
                  f"non_diegetic_music: {music_txt}")
        mode = "T2VA-fallback"
    locks_hit = [l.get("id") for l in locks if l.get("surface_en") and l["surface_en"].lower() in imm.lower()]
    return {"shot_id": shot.get("id", ""), "mode": mode,
            "tier": tier, "tier_label": (tcfg or {}).get("label", ""),
            "missing_image": not has_pic,
            "first_image": first.get("name") if first else "",
            "first_image_url": img_url(first.get("name")) if first else "",
            "duration_s": duration, "prompt": prompt, "locks_hit": locks_hit}
