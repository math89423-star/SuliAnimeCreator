"""8-block 静帧组装（T2I 纯文本）。"""
import re

VAGUE_BAN = ["cinematic", "epic", "stunning", "spectacular", "perfect", "premium", "8k", "high quality", "texture-rich"]


def clean(text):
    for w in VAGUE_BAN:
        text = re.sub(r"\b" + re.escape(w) + r"\b", "", text, flags=re.I)
    return " ".join(text.split())


def build_prompt(shot, character=None, locks=None, style_bible=""):
    character = character or {}
    locks = locks or []
    style = style_bible or "high-quality 2D anime illustration, anime key visual, cel-shaded"
    subject = f"1girl, solo, {character.get('identity', 'young woman')}"
    appearance = f"{character.get('hairstyle', '')} {character.get('face', '')}".strip() or "black long straight hair, dark eyes"
    outfit = (character.get("outfits_text") or "school uniform with red bow")[:120]
    pose = shot.get("duty", "standing").replace("[规则拆]", "").replace("[AI拆]", "")[:60] or "standing"
    scene = shot.get("scene_text") or "classroom interior, desks and windows"
    cam = shot.get("camera") or {}
    camera = f"{cam.get('crop', 'medium')} shot, {cam.get('height', 'eye')}-level, straight-on zero tilt"
    light = "soft key light from upper left, warm 3200K, muted indigo and amber palette"
    lock_txt = ", ".join([l.get("surface_en", "") for l in locks if l.get("surface_en")])[:200]
    parts = [style, subject, appearance, outfit, pose, scene, camera, light]
    if lock_txt:
        parts.insert(3, lock_txt)
    parts.append("score_9, masterpiece, best quality, sharp lineart")
    en = clean(", ".join([p for p in parts if p]))[:900]
    locks_hit = [l.get("id") for l in locks if l.get("surface_en") and l["surface_en"].lower() in en.lower()]
    return {"assembled_en": en, "locks_hit": locks_hit}


# 兼容旧名
_clean = clean
