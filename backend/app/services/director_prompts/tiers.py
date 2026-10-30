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

# 水位四档：门档仍是 nsfw，这一层只管"演到哪一步"（镜条目 water_level 字段，可缺省）。
# 与 art 域 tier、L-Port comic_page_diverge、skills/video/nsfw-directing 同一套。
WATER_CLAUSES = {
    "tease": ("The shot stays at the edge of contact: clothing intact, motion limited to breathing, "
              "a held gaze and the shift of a fingertip."),
    "undress": ("Clothing is half-removed and held in place by one hand or the sheet; exposure stays controlled, "
                "skin showing one band at a time."),
    "explicit": ("The sexual act is in progress and the point where their bodies meet stays visible in frame, "
                 "motion limited to one slow rhythm."),
    "closeup": ("The frame holds tight on a single contact point with the rest of the body cropped out, "
                "one small movement carrying the shot."),
}
WATER_LABELS = {"tease": "暗示", "undress": "半露", "explicit": "直白", "closeup": "特写"}


def normalize_water(v):
    """四档水位归一；门档值与空串一律返回空串。"""
    v = (v or "").strip()
    return v if v in WATER_CLAUSES else ""


def water_clause(v):
    return WATER_CLAUSES.get(normalize_water(v), "")


# 水位四档 -> 门档归一（库里已存数据照读不炸）
TIER_ALIAS = {"tease": "nsfw", "undress": "nsfw", "explicit": "nsfw", "closeup": "nsfw"}

def normalize_tier(v):
    v = (v or "").strip()
    if v in TIERS:
        return v
    return TIER_ALIAS.get(v, "")


def tier_list():
    return [{"key": k, "label": v["label"]} for k, v in TIERS.items()]

__all__ = ["TIERS", "TIER_ALIAS", "normalize_tier", "tier_list",
           "WATER_CLAUSES", "WATER_LABELS", "normalize_water", "water_clause"]
