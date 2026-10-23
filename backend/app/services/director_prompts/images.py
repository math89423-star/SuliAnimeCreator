"""director 配图归一：新 images 数组优先，老单图 image 回退。"""

REF_ROLE_PHRASE = {
    "character": "character identity",
    "outfit": "outfit",
    "style": "art style",
    "face": "face",
    "pose": "pose",
    "scene": "scene",
    "prop": "prop",
    "ending": "ending state",
}
MAX_REFS = 6  # PixAI 多图参考上限（含首帧）


def shot_images(shot):
    imgs = list(shot.get("images") or [])
    legacy = shot.get("image") or ""
    if legacy and not any(x.get("name") == legacy for x in imgs):
        imgs.append({"name": legacy, "kind": "ref"})
    return [x for x in imgs if x.get("name")]


def first_image(shot):
    imgs = shot_images(shot)
    for kind in ("first", "ref"):
        hit = next((x for x in imgs if x.get("kind", "ref") == kind), None)
        if hit:
            return hit
    return imgs[0] if imgs else None


def img_url(name):
    return f"/api/images/{name}" if name else ""


def collect_refs(shot, fallback=None):
    """排出本镜参考图：首帧打头，last 次之，ref 随后；超上限截断。返回 (ordered, truncated)。

    fallback：镜级一张图都没有时的兜底参考（角色立绘 / 本集参考图）。
    只在空镜生效——有镜级图就不掺兜底，避免把 Keyframe 顶成 Multi-Reference。
    """
    imgs = shot_images(shot)
    if not imgs and fallback:
        imgs = [dict(x) for x in fallback if isinstance(x, dict) and x.get("name")]
    first = next((x for x in imgs if x.get("kind") == "first"), None)
    lasts = [x for x in imgs if x.get("kind") == "last" and x is not first]
    others = [x for x in imgs if x is not first and x not in lasts]
    ordered = ([first] if first else []) + lasts + others
    return ordered[:MAX_REFS], len(ordered) > MAX_REFS


def collect_refs_fell_back(shot, fallback=None):
    """本镜是否用了兜底参考（纯函数，给组装层写备注）。"""
    return (not shot_images(shot)) and bool(fallback)


# 兼容旧名：director.py 曾用下划线版本
_shot_images = shot_images
_first_image = first_image
_img_url = img_url
_collect_refs = collect_refs
