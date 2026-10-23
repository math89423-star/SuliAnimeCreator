"""镜级生成方式（gen_mode）：**方案由 Suli 定，能力校验由 L-Port 侧规则兜底**。

四值枚举，与具体引擎无关（引擎能力在 pixai.PIXAI_MODELS 里）：
- ``t2v``             纯文本，不锚任何图
- ``i2v-first``       首帧锁构图（Keyframe）
- ``i2v-first-last``  首尾帧（首帧起点、尾帧收束）
- ``multi-ref``       多图只锚身份，动作自由（Multi-Reference）

这里只做两件事：归一（``normalize_gen_mode`` / ``infer_gen_mode``）与结算
（``resolve_gen_mode``）。结算结果再映射回既有的 ``ref_mode``（t2v / startframe /
reference），前端与 L-Port 都只认那三个值，不新开一套。
"""

GEN_MODES = ("t2v", "i2v-first", "i2v-first-last", "multi-ref")

GEN_MODE_LABELS = {
    "t2v": "纯文本",
    "i2v-first": "首帧",
    "i2v-first-last": "首尾帧",
    "multi-ref": "多图参考",
}

# 意图 → ref_mode（组装层与 L-Port 的公共词汇）
GEN_MODE_REF = {
    "t2v": "t2v",
    "i2v-first": "startframe",
    "i2v-first-last": "startframe",
    "multi-ref": "reference",
}

# 中文别名（大纲表里人手写也能认）
_ALIASES = {
    "纯文本": "t2v", "文生视频": "t2v", "t2v": "t2v", "text": "t2v", "无图": "t2v",
    "首帧": "i2v-first", "图生视频": "i2v-first", "i2v": "i2v-first",
    "i2v-first": "i2v-first", "startframe": "i2v-first", "keyframe": "i2v-first",
    "首尾帧": "i2v-first-last", "首尾": "i2v-first-last",
    "i2v-first-last": "i2v-first-last", "first-last": "i2v-first-last",
    "多图参考": "multi-ref", "多图": "multi-ref", "参考图": "multi-ref",
    "multi-ref": "multi-ref", "multiref": "multi-ref", "reference": "multi-ref",
}


def normalize_gen_mode(v):
    """生成方式归一：认枚举值、中文别名、ref_mode 旧值；认不出回空串（＝按素材推断）。"""
    s = (v or "").strip().lower().replace("_", "-")
    if not s:
        return ""
    if s in GEN_MODES:
        return s
    return _ALIASES.get(s, "")


def shot_kinds(shot):
    """本镜素材事实：有没有首帧 / 尾帧 / 其它参考图（老单图 image 字段算 ref）。"""
    imgs = [x for x in (shot.get("images") or []) if x.get("name")]
    legacy = shot.get("image") or ""
    if legacy and not any(x.get("name") == legacy for x in imgs):
        imgs.append({"name": legacy, "kind": "ref"})
    first = any(x.get("kind") == "first" for x in imgs)
    last = any(x.get("kind") == "last" for x in imgs)
    others = [x for x in imgs if x.get("kind") not in ("first", "last")]
    return {"first": first, "last": last, "others": len(others), "total": len(imgs)}


def infer_gen_mode(shot):
    """没标生成方式时按素材推：首+尾 → 首尾帧；首+其它图 → 多图参考；只有首 → 首帧；
    只有参考图 → 多图参考；一张没有 → 纯文本。"""
    k = shot_kinds(shot)
    if k["first"] and k["last"]:
        return "i2v-first-last"
    if k["first"] and k["others"]:
        return "multi-ref"
    if k["first"]:
        return "i2v-first"
    if k["total"]:
        return "multi-ref"
    return "t2v"


def resolve_gen_mode(gen_mode, shot, multi_ok=True, last_ok=True, fallback_used=False):
    """意图 + 素材 + 型号能力 → (生效方式, ref_mode, 说明列表)。

    降级只降不改方案：意图 ``i2v-first-last`` 缺尾帧就退成 ``i2v-first``，
    型号不支持尾帧也退成 ``i2v-first``，并在说明里写清为什么。
    """
    want = normalize_gen_mode(gen_mode) or infer_gen_mode(shot)
    k = shot_kinds(shot)
    notes = []

    if want == "t2v":
        eff = "t2v"
    elif want == "i2v-first":
        if k["first"]:
            eff = "i2v-first"
        elif fallback_used and multi_ok:
            eff = "multi-ref"
            notes.append("本镜无首帧，用角色立绘/本集参考图作 Multi-Reference")
        else:
            eff = "t2v"
            notes.append("本镜无首帧，纯文本出")
    elif want == "i2v-first-last":
        if not k["first"]:
            eff = "t2v"
            notes.append("本镜无首帧，首尾帧退成纯文本")
        elif not k["last"]:
            eff = "i2v-first"
            notes.append("本镜缺尾帧，首尾帧退成首帧")
        elif not last_ok:
            eff = "i2v-first"
            notes.append("目标型号不支持尾帧，首尾帧退成首帧")
        else:
            eff = "i2v-first-last"
    else:  # multi-ref
        if not multi_ok:
            if k["first"]:
                eff = "i2v-first"
                notes.append("目标型号不支持多图参考，退成首帧")
            else:
                eff = "t2v"
                notes.append("目标型号不支持多图参考且无首帧，退成纯文本")
        elif k["total"] == 0 and not fallback_used:
            eff = "t2v"
            notes.append("本镜没有参考图，多图参考退成纯文本")
        else:
            eff = "multi-ref"

    return eff, GEN_MODE_REF[eff], notes


def gen_mode_list():
    """给前端下拉：按枚举顺序出 {key,label}。"""
    return [{"key": k, "label": GEN_MODE_LABELS[k]} for k in GEN_MODES]
