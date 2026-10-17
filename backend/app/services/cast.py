"""cast：剧本/大纲/正文的「角色库化」取角。

取角顺序（谁说话就被谁的名字写进去，模板与 LLM prompt 共用同一份）：

1. 显式点名（调用方 cast 入参，或 ep["cast"] 落盘批次）——名字与角色库 id 都能给；
2. 集内正文已定稿的说话人（从 `#/##` 标题行除外的 `角色：台词` 前缀抽名）——
   重新生成时沿用本集已经定下来的角色，不会换人；
3. 角色库（character_db.json，最新的优先）；
4. 占位 `主角/对手`——永远不编造人名。

只读，不落盘；返回的 ids 供调用方记溯源。
"""
from __future__ import annotations

import re

FALLBACK_NAMES = ("主角", "对手")
MAX_CAST = 6

# 与 draft.validate_screenplay / estimate_screenplay 同一套说话人正则，口径别改歪
_DIALOG_RE = re.compile(r"^\s*([^#\[>\s]{1,12}?)\s*[:：]\s*\S")
# 说话人带状态注解（`蒋婉（把平板翻过来，屏幕是一张扫描件）：…`）：先抓到冒号前那截再清洗
_ANNOT_RE = re.compile(r"^\s*(?![#\[>\s])([^:：]{1,80}?)\s*[:：]\s*(\S.*)$")
# 台词行不会太长，也不会没有句末标点——长句+无句末标点判为叙述
_TAIL_MAX = 40
_TAIL_END_PUNCT = "。！？…~"
# 非说话人的行间标签 / 场次记号 / 模板叙述前缀，别当角色名
# （"动作" 是 draft 模板的叙述行前缀 `动作：…推进，镜头随人物走位…`，不是人名）
_NOT_SPEAKER = ("SFX", "VO", "OS", "旁白", "转场", "连续性", "画面文字", "字幕",
                "动作", "镜头", "景别", "时间", "地点", "方案大纲", "合计")
_OPEN_BRACKETS = "（(【[「『"
_CLOSE_BRACKETS = "）)】]」』"   # 注释用：判断注解是否收尾时参考，逻辑上不必逐一匹配
# 注解里出现句末标点（或逗号长句），说明这截八成是台词/叙述不是人名，宁可不认
_NOTE_END_PUNCT = "。！？；…—~!?;"
_NOTE_ANY_PUNCT = "，。！？；、…—~!?,;:："


def _strip_speaker_note(name):
    """说话人前缀去掉状态注解：`蒋婉（把平板翻过来…）` → `蒋婉`。
    括号开了没收的整段都算注解，只看括号前那截；判成叙述就返回 ""。"""
    name = re.sub(r"\s+", "", name or "")
    cut = -1
    for ch in _OPEN_BRACKETS:
        i = name.find(ch)
        if i > 0 and (cut < 0 or i < cut):
            cut = i
    if cut <= 0:
        return name
    head, note = name[:cut], name[cut:]
    # 注解里带句末标点 = 台词片段，弃
    if any(c in note for c in _NOTE_END_PUNCT):
        return ""
    # 注解里带逗号：只有短名（≤6字）才认，防把叙述句当人名
    if any(c in note for c in _NOTE_ANY_PUNCT) and len(head) > 6:
        return ""
    return head


def _speaker_of(line):
    """一行是不是 `角色：台词`；是就返回清洗后的说话人，否则 ""。"""
    s = (line or "").strip()
    if not s or s.startswith("#") or s.startswith("<!--") or s.startswith(">"):
        return ""
    def _dialogue_like(tail):
        """台词行的形状：不太长，且带句末标点（叙述句/画面句常没有）。"""
        tail = (tail or "").strip()
        return bool(tail) and len(tail) <= _TAIL_MAX and (
            any(c in tail for c in _TAIL_END_PUNCT) or tail.endswith('"'))

    m = _DIALOG_RE.match(s)
    if m:
        tail = s[m.end():]
        if not _dialogue_like(tail):
            return ""
        n = _strip_speaker_note(m.group(1).strip().strip("「」『』【】[]（）()"))
    else:
        # 第二梯队：允许长前缀，靠括号清洗 + 噪声判定兜住误认
        m = _ANNOT_RE.match(s)
        if not m or not _dialogue_like(m.group(2)):
            return ""
        n = _strip_speaker_note(m.group(1).strip().strip("「」『』【】[]（）()"))
        if any(c in n for c in _NOTE_END_PUNCT + "，"):
            return ""
    if not n or n.upper() in _NOT_SPEAKER or any(t in n for t in _NOT_SPEAKER):
        return ""
    if "<!--" in n or "-->" in n or len(n) > 12:
        return ""
    return n


def _norm_names(values):
    """名字列表去空白、去重、保序。"""
    out = []
    for v in values or []:
        n = str(v or "").strip()
        if n and n not in out:
            out.append(n[:24])
    return out


def _load_chars():
    """角色库角色表。优先走运行中蓝图的镜像，退回磁盘直读（单测/离线都可用）。"""
    try:
        from .repo import chars_map
        chars = chars_map()
        if chars:
            return list(chars.values())
    except Exception:
        pass
    try:
        from .disk_store import load
        doc = load("character_db.json", {}) or {}
        chars = doc.get("chars") or {}
        return list(chars.values())
    except Exception:
        return []


def db_names(limit=MAX_CAST):
    """角色库站得住脚的名字，新加的排前面。空库返回 []。"""
    rows = [c for c in _load_chars() if str((c or {}).get("name") or "").strip()]
    rows.sort(key=lambda c: int(c.get("created_at") or 0), reverse=True)
    return _norm_names([c.get("name") for c in rows])[:limit]


def name_by_id(cid=""):
    cid = str(cid or "").strip()
    if not cid:
        return ""
    for c in _load_chars():
        if c.get("id") == cid:
            return str(c.get("name") or "").strip()
    return ""


def speaker_names(text, limit=MAX_CAST):
    """从剧本正文抽说话人：只看 `角色：台词`，跳过标题/标签/注释行。"""
    out = []
    for ln in (text or "").splitlines():
        n = _speaker_of(ln)
        if not n or n in out:
            continue
        out.append(n)
        if len(out) >= limit:
            break
    return out


def resolve_cast(cast=None, script_text="", episode_id=""):
    """定这次生成用谁。

    cast 项可为 {'name'|'id'|'character_id'} 或纯字符串；也接受 ep 内存里的 cast。
    返回 {'names': [...], 'ids': [...], 'cast': [{id,name,source}], 'source': 说明}
    """
    ep = None
    if episode_id:
        try:
            from .repo import get_episode
            ep = get_episode(episode_id)
        except Exception:
            ep = None

    entries = []
    explicit = cast if cast else ((ep or {}).get("cast") or [])
    for item in explicit or []:
        if isinstance(item, dict):
            cid = str(item.get("id") or item.get("character_id") or "").strip()
            nm = str(item.get("name") or "").strip() or name_by_id(cid)
        else:
            cid, nm = "", str(item or "").strip()
        if nm:
            entries.append({"id": cid, "name": nm[:24], "source": "explicit"})

    if not entries:
        for n in speaker_names(script_text, MAX_CAST):
            entries.append({"id": "", "name": n, "source": "script"})

    if not entries:
        for n in db_names(MAX_CAST):
            entries.append({"id": "", "name": n, "source": "db"})

    anchored = bool(entries)
    if not entries:
        entries = [{"id": "", "name": n, "source": "fallback", "role": r}
                   for n, r in zip(FALLBACK_NAMES, ("protagonist", "antagonist"))]

    # 说话人至少两位，模板/LLM 都要有对话对象可写
    if len(entries) == 1:
        entries.append({"id": "", "name": FALLBACK_NAMES[1], "source": "role",
                        "role": "antagonist"})

    seen, cast_rows, names, ids = set(), [], [], []
    for e in entries:
        if e["name"] in seen:
            continue
        seen.add(e["name"])
        cast_rows.append(e)
        names.append(e["name"])
        if e["id"]:
            ids.append(e["id"])
    source = cast_rows[0]["source"] if cast_rows else "fallback"
    return {"names": names, "ids": ids, "cast": cast_rows,
            "source": source, "anchored": anchored}
