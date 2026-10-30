"""8-block 静帧组装（T2I 纯文本）。只出英文：含 CJK 的字段整段丢掉，缺啥空啥，不套默认。

frame="first"|"last" 时 pose/scene 优先读同侧 boundary（start_boundary/end_boundary）
的英文（duty_en/key_text_en/scene_en），再回落到镜级英文；boundary 为空时首尾同文，
等起止状态链路补齐自然分流，本层不编造英文。
"""
import re

from .text import strip_prefix

VAGUE_BAN = ["cinematic", "epic", "stunning", "spectacular", "perfect", "premium", "8k", "high quality", "texture-rich"]

CJK = re.compile(r"[\u3400-\u9fff]")


def _en_only(text):
    """英文正文不吃中文：含 CJK 整段丢掉（与 pixai 同口径），身份交给参考图。"""
    text = (text or "").strip()
    return "" if CJK.search(text) else text


def _boundary(shot, frame):
    if frame in ("first", "last"):
        b = shot.get("start_boundary" if frame == "first" else "end_boundary") or {}
        if isinstance(b, dict):
            return b
    return {}


def clean(text):
    for w in VAGUE_BAN:
        text = re.sub(r"\b" + re.escape(w) + r"\b", "", text, flags=re.I)
    return " ".join(text.split())


def build_prompt(shot, character=None, locks=None, style_bible="", frame=None):
    character = character or {}
    locks = locks or []
    style = style_bible or "high-quality 2D anime illustration, anime key visual, cel-shaded"
    bnd = _boundary(shot, frame)
    identity_en = (_en_only(character.get("anchor_en") or "")
                   or _en_only(character.get("identity") or "")
                   or "the character")
    subject = f"1girl, solo, {identity_en}"
    appearance = _en_only(f"{character.get('hairstyle', '')} {character.get('face', '')}".strip())
    outfit = _en_only((character.get("outfits_text") or "").strip()[:120])
    pose = (_en_only(strip_prefix(bnd.get("duty_en") or bnd.get("key_text_en") or ""))
            or _en_only(strip_prefix(shot.get("duty_en") or shot.get("key_text_en") or ""))
            or "standing")[:60].strip() or "standing"
    scene = (_en_only((bnd.get("scene_en") or "").strip())
             or _en_only((shot.get("scene_en") or "").strip()))
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
    return {"assembled_en": en, "locks_hit": locks_hit, "frame": frame or ""}
