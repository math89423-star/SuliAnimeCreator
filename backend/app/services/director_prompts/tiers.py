"""director 档位真源：成人向四档 + 前端下拉共用。"""

TIERS = {
    "tease": {
        "label": "氛围暗示",
        "anchor": "adult, mature",
        "clause": ("Intimacy stays suggestive: clothing remains in place, and contact is limited to "
                   "proximity, breath, and gaze."),
    },
    "undress": {
        "label": "半露",
        "anchor": "adult, mature",
        "clause": ("The subject is partially undressed, the garment slipped off one shoulder with the collar "
                   "open, while the coverage of <Picture 1> is preserved where the reference keeps it."),
    },
    "explicit": {
        "label": "直白",
        "anchor": "adult, mature, fully adult and mutually responsive",
        "clause": ("Both subjects are fully adult and mutually responsive; their bodies stay pressed flush "
                   "in frame and the visible motion stays within a single slow rhythm."),
    },
    "closeup": {
        "label": "特写",
        "anchor": "adult, mature, fully adult and mutually responsive",
        "clause": ("The shot holds as an extreme close-up on the contact surface with both faces cropped "
                   "out of frame, and the motion never leaves the crop."),
    },
}


def tier_list():
    return [{"key": k, "label": v["label"]} for k, v in TIERS.items()]
