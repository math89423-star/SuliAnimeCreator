"""director 档位真源：只两档 sfw/nsfw + 前端下拉共用。"""

TIERS = {
    "sfw": {
        "label": "普通",
        "anchor": "",
        "clause": ("Keep the content non-explicit and suitable for all audiences: "
                   "clothing remains in place, no sexual content."),
    },
    "nsfw": {
        "label": "成人向",
        "anchor": "adult, mature, fully adult and mutually responsive",
        "clause": ("Both subjects are fully adult and mutually responsive; their bodies stay pressed flush "
                   "in frame and the visible motion stays within a single slow rhythm."),
    },
}

# 旧四档 -> 两档归一（库里老数据照读不炸）
LEGACY_TIERS = {"tease": "nsfw", "undress": "nsfw", "explicit": "nsfw", "closeup": "nsfw"}


def normalize_tier(v):
    v = (v or "").strip()
    if v in TIERS:
        return v
    return LEGACY_TIERS.get(v, "")


def tier_list():
    return [{"key": k, "label": v["label"]} for k, v in TIERS.items()]

__all__ = ["TIERS", "LEGACY_TIERS", "normalize_tier", "tier_list"]
