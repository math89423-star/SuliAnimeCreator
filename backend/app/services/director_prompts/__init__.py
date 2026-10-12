"""director_prompts：纯组装函数包。路由层只调这里，不碰别家蓝图私有变量。"""
from .tiers import TIERS, tier_list
from .still import VAGUE_BAN, clean, build_prompt
from .h3 import I2VA_ALIGN, MOVEMENT_EN, CROP_EN, build_i2va
from .pixai import (
    PIXAI_CAM, PIXAI_SFX, PIXAI_SFX_DEFAULT, PIXAI_TONE, PIXAI_MODELS,
    apply_pixai_model_deltas, build_pixai,
)
from .images import (
    REF_ROLE_PHRASE, MAX_REFS, shot_images, first_image, img_url, collect_refs,
)
from .text import (
    DIALOG, CJK, PRONOUN_EN, FULL_START,
    strip_prefix, pixai_preformatted, strip_pixai_scaffold, looks_full,
)

__all__ = [
    "TIERS", "tier_list",
    "VAGUE_BAN", "clean", "build_prompt",
    "I2VA_ALIGN", "MOVEMENT_EN", "CROP_EN", "build_i2va",
    "PIXAI_CAM", "PIXAI_SFX", "PIXAI_SFX_DEFAULT", "PIXAI_TONE", "PIXAI_MODELS",
    "apply_pixai_model_deltas", "build_pixai",
    "REF_ROLE_PHRASE", "MAX_REFS", "shot_images", "first_image", "img_url", "collect_refs",
    "DIALOG", "CJK", "PRONOUN_EN", "FULL_START",
    "strip_prefix", "pixai_preformatted", "strip_pixai_scaffold", "looks_full",
]
