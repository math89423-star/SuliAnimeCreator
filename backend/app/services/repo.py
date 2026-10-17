"""repo：跨蓝图统一读口，避免 `from ..api.xxx import _PRIVATE`。

之前 director.py 直接导 scriptboard/character/story 的私有全局
（_SHOTS/_EPS/_CHARS/_SLOT_PROMPTS/_DOCS/_STORE），改一处存储结构
就炸一片。本模块是唯一的跨域读取出口：

- 函数内懒导入，天然断循环依赖；
- 只读不写，写回仍归各蓝图自己的 _persist()；
- 返回引用（dict 本体），调用方不要长期持有，读完即用。
"""
from __future__ import annotations


def shots_map():
    from ..api.scriptboard import _SHOTS
    return _SHOTS


def episodes_map():
    from ..api.scriptboard import _EPS
    return _EPS


def chars_map():
    from ..api.character import _CHARS
    return _CHARS


def slot_prompts_map():
    from ..api.character import _SLOT_PROMPTS
    return _SLOT_PROMPTS


def character_docs_map():
    from ..api.character import _DOCS
    return _DOCS


def character_assets(cid=""):
    """角色设定图资产（18 槽位：kind|slot 去重取最新）：只读。"""
    from ..api.character import _ASSETS
    rows = [a for a in _ASSETS.values() if not cid or a.get("character_id") == cid]
    latest = {}
    for a in sorted(rows, key=lambda x: x.get("id", 0)):
        latest[(a.get("kind", ""), a.get("slot", ""))] = a
    return [latest[k] for k in sorted(latest)]


def character_dims():
    from ..api.character import DIMS
    return DIMS


def story_store():
    from ..api.story import _STORE
    return _STORE


def list_shots_by_episode(eid: str):
    shots = shots_map()
    rows = [s for s in shots.values() if not eid or s.get("episode_id") == eid]
    rows.sort(key=lambda x: (x.get("ord", 0), x.get("id", "")))
    return rows


def get_episode(eid: str):
    return episodes_map().get(eid, {})


def first_character():
    chars = chars_map()
    vals = list(chars.values())
    return vals[0] if vals else {}


def get_character(cid: str):
    return chars_map().get(cid, {}) if cid else first_character()


def resolve_shot(s):
    """shots 项兼容：dict 直接用；id 字符串回查实镜；查不到给占位。"""
    if isinstance(s, dict):
        return s
    try:
        hit = shots_map().get(s)
        if hit:
            return hit
    except Exception:
        pass
    return {"id": s, "duty": s, "camera": {}}
