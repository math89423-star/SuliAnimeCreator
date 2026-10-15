"""art 蓝图：美术工具页数据化。7个工具已原生化为前端组件（frontend/src/components/tools/），此处只给索引。
另含出图引擎画像（image-models）：三家生产引擎的提示词形态/质量标签/纪律，craft 归
skills/image/production-image-models（本文件只给机器可读真源，不重写规范）。
"""
from flask import Blueprint, jsonify

bp = Blueprint("art", __name__, url_prefix="/api/v1/art")

TOOLS = [
    {"id": "composition-camera", "name": "构图机位", "desc": "220卡30页：景别/机位/透视/构图，高级镜头+拆解"},
    {"id": "costume", "name": "服装穿搭", "desc": "18流派198单品+搭配台，S1-3b选型用"},
    {"id": "palette", "name": "配色", "desc": "15系764色+和色465，主辅点三层取色"},
    {"id": "flowers", "name": "花语", "desc": "101花三层花语+booru tag"},
    {"id": "naming", "name": "取名", "desc": "75招+91撞名自检"},
    {"id": "shot-grammar", "name": "镜头语法", "desc": "运镜31/机位21/景别7，拼prompt"},
    {"id": "nsfw-guide", "name": "分级", "desc": "九槽+模型分流+成年锚"},
]

# 出图引擎画像（真源）：form=提示词形态；quality_tags=模型自带质量标签（写了就重复，别手写）
IMAGE_MODELS = [
    {
        "key": "novelai", "label": "NovelAI Diffusion（V5 / V4.5 / V4 / Anime V3）",
        "form": "tags",
        "quality_tags": ", very aesthetic, masterpiece, no text",
        "weight_syntax": "{ } 强化 / [ ] 弱化（各 ×1.05）；数值 1.5::x :: 仅 V4+",
        "hint": "逗号 tag 为主，可夹短句；质量标签走开关不手写；一次只加 1-2 个关键权重",
        "negative_hint": "每镜现配、短、只点名真实风险：extra digits, cropped head, child, minor, underage, loli, shota, aged_down",
        "notes": "多角色用 Character Prompts（V4≤6 / V5≤22）；Precise Reference 分角色/风格且多张会融合；V4+ 约 512 T5 token",
        "ref": "skills/image/production-image-models/references/novelai.md",
    },
    {
        "key": "tsubaki3", "label": "PixAI Tsubaki.3",
        "form": "natural",
        "quality_tags": "",
        "weight_syntax": "无（用词的顺序与具体度控制权重）",
        "hint": "五槽顺序：主体 → 细节 → 构图机位 → 光 → 风格；介词动词比形容词值钱；禁 tag 堆",
        "negative_hint": "自然语言模型无负向栏；要排除的东西用正面写法或换参考图",
        "notes": "可中文/日文/韩文直写，专有名词与技术词留英文；参考图分 base image 与 reference slot 两通道；图上文字写内容+位置+职责",
        "ref": "skills/image/production-image-models/references/tsubaki3.md",
    },
    {
        "key": "seedream", "label": "Seedream（火山方舟 doubao-seedream 4.0/4.5/5.0）",
        "form": "natural",
        "quality_tags": "",
        "weight_syntax": "无",
        "hint": "一句用途开头 + 主体/行为/环境连贯短句 + 风格/色彩/光影/构图；避免碎片堆叠",
        "negative_hint": "无负向栏；用正向描述与参考图约束",
        "notes": "编辑用增加/删除/替换/修改 + 箭头线框涂鸦定位；参考图写“参考对象 + 生成画面”两部分；组图用“一系列/一套/组图”或给张数；限流约 500 IPM",
        "ref": "skills/image/production-image-models/references/seedream.md",
    },
]


def ok(data):
    return jsonify({"code": 0, "data": data})


@bp.get("/tools")
def tools():
    return ok(TOOLS)


@bp.get("/image-models")
def image_models():
    return ok(IMAGE_MODELS)

