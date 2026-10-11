"""art 蓝图：美术工具页数据化。7个工具已原生化为前端组件（frontend/src/components/tools/），此处只给索引。"""
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

def ok(data):
    return jsonify({"code": 0, "data": data})

@bp.get("/tools")
def tools():
    return ok(TOOLS)
