"""角色槽位提示词：按目标出图引擎出稿。纯函数，方便单测。"""

SLOT_CN = {"front": "正面", "side": "侧面", "back": "背面", "look": "外观", "expression": "表情",
           "front_cn": "正面", "side_cn": "侧面", "back_cn": "背面"}


def build_slot_prompt(char, kind, slot, engine=""):
    engine = (engine or "").strip()
    hair = ((char.get("hairstyle") or "").strip())
    identity = ((char.get("identity") or "").strip())
    outfits = ((char.get("outfits_text") or "").strip())
    hair_cn = hair or "发型按设定"
    identity_cn = identity or "成年女性角色"
    outfits_cn = outfits or "设定服装"

    if engine == "novelai":
        parts = ["character design sheet", "1girl", "solo", "adult", "mature female",
                 identity, hair, outfits, f"{slot} view", "full body", "simple background",
                 "clean lineart", "flat color", "consistent front side back", "balanced limbs"]
        return ", ".join([x for x in parts if x])
    if engine == "tsubaki3":
        return (f"角色设定图（{SLOT_CN.get(slot, slot)}）：一位{identity_cn}，{hair_cn}，身穿{outfits_cn}；"
                f"站在纯色背景前，正面、侧面与背面姿态一致、比例协调；中景，镜头平视，浅景深；"
                f"柔和均匀的顶光与正面补光，阴影干净；动漫插画，干净线稿、平涂上色。")
    if engine == "seedream":
        return (f"角色设定图（三视图 + 服装细节）：以{identity_cn}为主体，{hair_cn}，身穿{outfits_cn}；"
                f"纯色背景，正面/侧面/背面姿态一致、比例准确，画面清晰不需要文字；"
                f"动漫插画风格，干净线条与柔和配色，均匀布光；输出为设定表版式，三视图并排。")
    return (f"high-quality 2D anime character design sheet, {kind} {slot} view, "
            f"{hair} {identity}, clean line, flat color, "
            f"front/side/back consistent, masterpiece")
