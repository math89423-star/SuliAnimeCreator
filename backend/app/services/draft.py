"""draft 轻链：草案发散不走 dsh，直接调 LLM 网关 + 规则回退。

dsh 只留 skill 加载 + 单会话（episode 一集一会话）做导演判断；
草案发散（发散/大纲/转草案）走本模块，失败永远有 heuristic 保底，不抛 500。
"""
import re

from . import cast as cast_svc


MOVEMENTS = ["固定", "推", "拉", "摇", "移", "跟", "环绕", "升降", "手持", "航拍"]
CROPS = ["extreme_close", "closeup", "close", "medium_close", "medium",
         "medium_full", "full", "wide", "extreme_wide"]


def expand_idea(idea, n=3):
    """发散 n 个方向：LLM 优先，失败回模板（story/suggest 三档）。"""
    idea = (idea or "").strip()
    try:
        from .llm_opencode import llm_cfg, _post
        cfg = llm_cfg()
        if cfg.get("provider") == "opencode" and cfg.get("key") and cfg.get("model"):
            model_id = re.sub(r"^opencode-go/", "", cfg["model"])
            prompt = ("你是短剧发散助手。对下面一句话做 %d 个异质发散方向，"
                      "只输出 JSON 数组，每项含 dir/logline/beats(3个动词)。idea：\n%s" % (n, idea[:500]))
            import json as _json
            txt = _post(cfg["base"], cfg["key"], model_id, prompt,
                        effort=cfg.get("effort", ""))
            m = re.search(r'\[.*\]', txt, re.S)
            if m:
                rows = _json.loads(m.group(0))
                if isinstance(rows, list) and rows:
                    return rows[:n], "llm"
    except Exception:
        pass
    base = idea or "无题"
    rows = [
        {"dir": "A", "logline": "%s：隐喻替换版" % base, "beats": ["起", "转", "落"]},
        {"dir": "B", "logline": "%s：时空平移版" % base, "beats": ["起", "转", "落"]},
        {"dir": "C", "logline": "%s：视角反转版" % base, "beats": ["起", "转", "落"]},
    ]
    return rows[:n], "template"


def _cast_names(cast=None, hint="", episode_id=""):
    """本次生成用谁：显式点名 → 集内正文说话人 → 角色库 → 主角/对手占位。"""
    return cast_svc.resolve_cast(cast, hint or "", episode_id or "")


def _lead_pair(names=None):
    """模板对白用的一对说话人：没有角色就回占位，不编人名。"""
    names = [n for n in (names or []) if str(n).strip()]
    if not names:
        names = list(cast_svc.FALLBACK_NAMES)
    lead = names[0]
    foil = names[1] if len(names) > 1 else cast_svc.FALLBACK_NAMES[1]
    return lead, foil


def _outline_template(episode_id, total_s, shots_n, engine, tier, hint="", cast=None, ref_image=""):
    total_s = total_s or 15
    tier_name = {"nsfw": "成人向", "sfw": "普通"}.get(tier or "", "常规")
    C = _cast_names(cast, hint, episode_id)
    lines = [
        "# 方案大纲 %s" % (episode_id or ""),
        "",
        "## 方向一句话",
        "%s（%s，%s，合计约 %ss）" % ((hint or "单图氛围延续").strip(), tier_name, engine or "pixai", total_s),
        "",
        "## 基调与档位",
        "- 档位：%s / 引擎：%s" % (tier_name, engine or "pixai"),
        "- 约束：单镜 3-8 秒，一镜一事件",
    ]
    if C["anchored"]:
        lines.append("- 出镜：%s（角色名照写，勿改用其他名字）" % "、".join(C["names"]))
    lines += [
        "",
        "## 分镜大纲表",
        "",
        "| 镜号 | 内容一句话 | 预计时长 | 运镜方向 | 生成方式 | 备注 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    per = max(3, min(8, round(total_s / max(1, shots_n))))
    for i in range(1, shots_n + 1):
        mov = MOVEMENTS[i % len(MOVEMENTS)]
        # 有大纲配图时第一镜挂首帧，生成方式照实写；其余镜没有素材，按纯文本
        gen = "i2v-first" if (ref_image and i == 1) else "t2v"
        lines.append("| %d | 氛围延续第%d镜 | %d秒 | %s | %s | 草案待定稿 |"
                     % (i, i, per, mov, gen))
    lines += ["", "## 合计时长", "", "约 %s 秒，共 %d 镜。" % (per * shots_n, shots_n), ""]
    return "\n".join(lines)


def build_outline_md(episode_id, total_s=15, engine="pixai", tier="", hint="", ref_image="", cast=None):
    """轻大纲：LLM 优先写 markdown，失败回模板。永远返回 (md, engine_tag)。"""
    total_s = int(total_s or 15)
    shots_n = 3 if total_s <= 15 else (4 if total_s <= 24 else 5)
    C = _cast_names(cast, hint, episode_id)
    cast_hint = ""
    if C["anchored"]:
        cast_hint = "出镜角色（点名照写，别换成别的人名）：%s。" % "、".join(
            c["name"] for c in C["cast"][:4])
    try:
        from .llm_opencode import llm_cfg, _post
        cfg = llm_cfg()
        if cfg.get("provider") == "opencode" and cfg.get("key") and cfg.get("model"):
            model_id = re.sub(r"^opencode-go/", "", cfg["model"])
            prompt = ("只做方案大纲 markdown，含：方向一句话/基调与档位/分镜大纲表"
                      "(镜号|内容一句话|预计时长|运镜方向|生成方式|备注)/合计时长。"
                      "生成方式只能填 t2v / i2v-first / i2v-first-last / multi-ref 之一："
                      "t2v=纯文本不锚图，i2v-first=首帧锁构图，i2v-first-last=首尾帧，"
                      "multi-ref=多图只锚身份。按这镜实际能不能拿到图来填，拿不到就写 t2v。"
                      "%d-%d镜，单镜3-8秒，总计约%d秒，引擎%s档位%s。%s背景：%s"
                      % (shots_n, shots_n, total_s, engine or "pixai",
                         tier or "常规", cast_hint, (hint or "")[:800]))
            txt = _post(cfg["base"], cfg["key"], model_id, prompt,
                        effort=cfg.get("effort", ""))
            txt = (txt or "").strip()
            if len(txt) >= 40 and "镜" in txt:
                return txt, "llm"
    except Exception:
        pass
    return _outline_template(episode_id, total_s, shots_n, engine, tier, hint, C["cast"], ref_image), "template"


def _norm_crop(v):
    v = (v or "").strip().lower()
    for c in CROPS:
        if c in v:
            return c
    alias = {"特写": "closeup", "近景": "close", "中景": "medium",
             "全景": "full", "远景": "wide", "大特写": "extreme_close",
             "大远景": "extreme_wide"}
    for k, std in alias.items():
        if k in (v or ""):
            return std
    return "medium"


def _norm_dur(v, fallback):
    """时长归一：认 5 / 5s / 5秒 / 约5秒；认不出回 fallback。"""
    m = re.search(r"\d+(?:\.\d+)?", str(v or ""))
    if not m:
        return fallback
    try:
        return max(1, min(8, int(round(float(m.group(0))))))
    except (ValueError, TypeError):
        return fallback


def _norm_move(v):
    """运镜归一：取正文里最先出现的那个词（"手持轻晃跟拍"→手持，不是按词表顺序抢），
    认不出回空串（由调用方按位置兜底）。"""
    t = (v or "").strip()
    hits = [(t.find(m), m) for m in MOVEMENTS if m and m in t]
    return min(hits)[1] if hits else ""


def _table_columns(header):
    """大纲表头 → 列下标。认得出就按名字取，认不出按位置（0..4）兜底。"""
    cells = [c.strip() for c in (header or "").strip().strip("|").split("|")]
    cols = {}
    for i, c in enumerate(cells):
        if "镜号" in c:
            cols["mid"] = i
        elif "内容" in c:
            cols["content"] = i
        elif "时长" in c or "秒" in c:
            cols["dur"] = i
        elif "运镜" in c:
            cols["move"] = i
        elif "生成" in c:
            cols["gen"] = i
        elif "备注" in c:
            cols["note"] = i
    if "content" not in cols:
        cols = {"mid": 0, "content": 1, "dur": 2, "move": 3, "gen": 4, "note": 5}
    return cols


def _parse_outline_rows(text):
    """大纲表 → 行参数：内容 / 时长 / 运镜 / 生成方式 / 备注。

    表头认名字取列（五列表没有生成方式列就按位置兜底），列值不再丢：
    只取 cells[1] 当内容，时长/运镜/备注全扔，运镜靠轮转补——大纲写了等于没写。
    """
    from .director_prompts.genmode import normalize_gen_mode
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    clean = [l for l in rows if not re.match(r'^\|\s*:?-', l.strip())]
    if not clean:
        return []
    cols = _table_columns(clean[0])
    out = []
    for l in clean[1:]:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]

        def cell(key, pos, default=""):
            i = cols.get(key, pos)
            return cells[i] if 0 <= i < len(cells) else default

        duty = cell("content", 1)
        if not duty:
            continue
        out.append({
            "duty": duty[:60],
            "duration_s": cell("dur", 2),
            "movement": _norm_move(cell("move", 3)),
            "gen_mode": normalize_gen_mode(cell("gen", 4)),
            "note": cell("note", 5)[:80],
        })
    return out


def split_outline_to_shots(outline_md, episode_id, total_s=15, tier=""):
    """大纲转草案参数。返回 (list, tag)。

    大纲表是方案的唯一真相（镜数、内容、时长、运镜、生成方式都照表）；
    llm_cuts 只用来补英文正文与音效，不重写镜数/内容——否则表里定的东西白写。
    没有表行时才退回 llm_cuts，再退回均分模板。
    """
    text = (outline_md or "").strip()
    total_s = int(total_s or 15)
    parsed = _parse_outline_rows(text)
    n = min(5, max(2, len(parsed) or 3))
    cuts = []
    try:
        from .llm import llm_cuts
        cuts = llm_cuts(text[:2000])[:n] or []
    except Exception:
        cuts = []

    if parsed:
        per = max(3, min(8, round(total_s / len(parsed))))
        out = []
        for i, row in enumerate(parsed[:5]):
            c = cuts[i] if i < len(cuts) else {}
            out.append({
                "duty": row["duty"],
                "duty_en": str(c.get("key_text_en") or "")[:200],
                "duration_s": _norm_dur(row.get("duration_s"), per),
                "sound": str(c.get("sound") or ""),
                "gen_mode": row.get("gen_mode") or "",
                "tier": (tier or "").strip(),
                "camera": {"crop": _norm_crop(c.get("crop")),
                           "movement": row.get("movement") or MOVEMENTS[(i + 1) % len(MOVEMENTS)]},
            })
        return out, "outline"

    if cuts:
        from .director_prompts.genmode import normalize_gen_mode
        per = max(3, min(8, round(total_s / len(cuts))))
        out = []
        for i, c in enumerate(cuts):
            out.append({
                "duty": c.get("duty", "")[:80] or ("大纲第%d镜" % (i + 1)),
                "duty_en": c.get("key_text_en", "")[:200] or "",
                "duration_s": _norm_dur(c.get("duration_s"), per),
                "sound": c.get("sound", "") or "",
                "gen_mode": normalize_gen_mode(c.get("gen_mode")),
                "tier": (tier or "").strip(),
                "camera": {"crop": _norm_crop(c.get("crop")),
                           "movement": _norm_move(c.get("movement")) or MOVEMENTS[(i + 1) % len(MOVEMENTS)]},
            })
        return out, "llm"
    per = max(3, min(8, round(total_s / n)))
    out = []
    for i in range(n):
        p = parsed[i] if i < len(parsed) else {}
        out.append({
            "duty": p.get("duty") or ("大纲第%d镜" % (i + 1)),
            "duty_en": "",
            "duration_s": _norm_dur(p.get("duration_s"), per),
            "sound": "",
            "gen_mode": p.get("gen_mode") or "",
            "tier": (tier or "").strip(),
            "camera": {"crop": "medium",
                       "movement": p.get("movement") or MOVEMENTS[(i + 1) % len(MOVEMENTS)]},
        })
    return out, "template"


# ---- 精品剧本链：screenplay 正文 / 校验 / 估时 / beats / 审查 ----

def pick_to_screenplay_md(pick, episode_id=""):
    """confirm 落底稿：pick{dir,logline,beats} -> 规范剧本 md。纯规则，可直接落盘。
    说话人按角色库取（显式 cast → 本集正文说话人 → 角色库 → 主角/对手占位），不编人名。"""
    import datetime as _dt
    pick = pick or {}
    logline = str(pick.get("logline") or "未命名方向").strip()[:200]
    beats = pick.get("beats") or ["起", "转", "落"]
    beats = [str(b)[:60] for b in beats][:6] or ["起", "转", "落"]
    eid = (episode_id or "EP-DEMO01").strip() or "EP-DEMO01"
    lead, foil = _lead_pair(_cast_names(pick.get("cast"), logline, eid)["names"])
    L = ["# %s %s" % (eid, logline), "",
         "## %s-SC001 内·主场景·夜" % eid, ""]
    sfx = ["[SFX] 铁门低鸣", "[SFX] 环境底声停一拍", "[SFX] 脚步逼近", "[SFX] 关键道具落桌", "[SFX] 静默一拍", "[SFX] 低频鼓点起"]
    replies = ["%s：收到，这条接住了。", "%s：别松，钩子还在推进。", "%s：顶上去，一句定生死。",
               "%s：稳住，节拍按计划走。", "%s：好，收束留白。", "%s：成了，转场。"]
    for i, b in enumerate(beats, 1):
        L.append("%s：%s第%d拍推进——%s。" % (lead, logline[:12], i, b))
        L.append(sfx[(i - 1) % len(sfx)])
        L.append(replies[(i - 1) % len(replies)] % foil)
        L.append("")
    L.append("[连续性] 关键道具状态已交代；人物关系推进。")
    L.append("[转场] 硬切下场。")
    L.append("")
    L.append("<!-- beats:%s -->" % " / ".join(beats))
    L.append("<!-- generated:%s template:p pick_to_screenplay cast:%s -->" % (
        _dt.datetime.now().isoformat(timespec="seconds"),
        "/".join(_cast_names(pick.get("cast"), logline, eid)["names"])))
    return "\n".join(L).strip() + "\n"


def _screenplay_template(idea, logline, beats, target_s, episode_id, cast=None):
    eid = (episode_id or "EP-DEMO01").strip() or "EP-DEMO01"
    base = (logline or idea or "单集矛盾").strip()[:120] or "单集矛盾"
    beats = beats or ["起", "转", "落"]
    lead, foil = _lead_pair(_cast_names(cast, idea or base, eid)["names"])
    n_sc = 3 if target_s <= 20 else 4
    L = ["# %s %s" % (eid, base), ""]
    for i in range(n_sc):
        b = str(beats[i % len(beats)])[:40]
        L += ["## %s-SC%03d 内·主场景·夜" % (eid, i + 1), "",
              "动作：%s推进，镜头随人物走位给冲突。" % b,
              "%s：%s，第%d场顶上去。" % (lead, base[:16], i + 1),
              "[SFX] 脚步+环境底声",
              "%s：接第%d场，谁先变招谁定调。" % (foil, i + 1),
              ""]
    L += ["[连续性] 关键道具状态已交代；人物关系推进。", "[转场] 硬切收束。", ""]
    return "\n".join(L).strip() + "\n"


def build_screenplay_md(idea="", logline="", beats=None, target_s=30, episode_id="", cast=None):
    """剧本正文生成：LLM 优先，失败回模板。永远返回 (md, engine_tag)。
    出镜人名一律来自角色库/本集正文/显式点名，prompt 里不再写死人名。"""
    idea = (idea or "").strip()[:500]
    logline = (logline or "").strip()[:200]
    beats = beats or []
    try:
        target_s = max(10, min(90, int(target_s or 30)))
    except (ValueError, TypeError):
        target_s = 30
    C = _cast_names(cast, idea or logline, episode_id or "")
    try:
        from .llm_opencode import llm_cfg, _post
        cfg = llm_cfg()
        if cfg.get("provider") == "opencode" and cfg.get("key") and cfg.get("model"):
            model_id = re.sub(r"^opencode-go/", "", cfg["model"])
            cast_hint = ("对白说话人只能用这些名字：%s。"
                         "写法就是「名字：台词」，别在名字后加角色标签、别自造人名。"
                         % "、".join(c["name"] for c in C["cast"][:4])) if C["anchored"] else \
                        "角色名留空用「主角/对手」占位，别自造人名。"
            prompt = ("写一集中文短剧剧本 Markdown，必须含：首行‘# EP集名 标题’；"
                      "2-4 个‘## EP-SCxxx 内·地点·时间’场景；每场有动作行+‘角色：台词’对白"
                      "（%s）+ [SFX]/[连续性]/[转场]标签；"
                      "总时长约%d秒。只输出剧本正文。背景：%s / %s / 节拍%s"
                      % (cast_hint, target_s, idea[:400], logline[:200], "/".join(beats[:4])[:120]))
            import json as _json  # noqa: F401 (keep import parity)
            txt = _post(cfg["base"], cfg["key"], model_id, prompt,
                        effort=cfg.get("effort", ""))
            txt = (txt or "").strip()
            if txt.count("##") >= 1 and ("：" in txt or ":" in txt) and len(txt) >= 120:
                return txt.strip() + "\n", "llm"
    except Exception:
        pass
    return _screenplay_template(idea, logline or idea, beats or ["起", "转", "落"],
                                target_s, episode_id, C["cast"]), "template"


def validate_screenplay(md):
    """剧本结构校验：返回 findings[{level,rule,fix,pos}]。纯规则，演示稳定。"""
    text = (md or "")
    lines = text.splitlines()
    findings = []
    if not text.strip():
        return [{"level": "blocker", "rule": "SCR-00", "fix": "剧本为空，先生成或粘贴正文", "pos": "全文"}]
    if not re.search(r"^#\s+\S+", text, re.M):
        findings.append({"level": "blocker", "rule": "SCR-01", "fix": "缺首行‘# EP集名 标题’", "pos": "首行"})
    sc = re.findall(r"^##\s+\S+", text, re.M)
    if not sc:
        findings.append({"level": "blocker", "rule": "SCR-02", "fix": "缺‘## EP-SCxxx 内·地点·时间’场景标题，至少1场", "pos": "场景"})
    elif len(sc) > 6:
        findings.append({"level": "major", "rule": "SCR-02b", "fix": "场景%d场偏多，精品集建议2-4场" % len(sc), "pos": "场景数"})
    dlg = [l for l in lines if re.match(r"^\s*[^#\[>\s][^：:]{1,12}[：:].+", l.strip())]
    if len(dlg) < 2:
        findings.append({"level": "blocker", "rule": "SCR-03", "fix": "对白不足2句，用‘角色：台词’写", "pos": "对白"})
    tags = ("[SFX]", "[VO]", "[OS]", "[连续性]", "[转场]", "[画面文字]")
    if not any(t in text for t in tags):
        findings.append({"level": "major", "rule": "SCR-04", "fix": "缺生产标签，至少加1个 [SFX]/[连续性]/[转场]", "pos": "标签"})
    # 模板感：连续重复句
    seen = {}
    for l in lines:
        s = l.strip()
        if len(s) >= 6 and not s.startswith("#"):
            seen[s] = seen.get(s, 0) + 1
    dups = [k for k, v in seen.items() if v >= 3]
    if dups:
        findings.append({"level": "major", "rule": "SCR-05", "fix": "模板感：同句出现≥3次‘%s’，改写其中2处" % dups[0][:16], "pos": "去重"})
    if len(text) < 200:
        findings.append({"level": "major", "rule": "SCR-06", "fix": "正文偏短（%d字），精品集建议400字+" % len(text), "pos": "篇幅"})
    return findings


def normalize_screenplay(md, episode_id=""):
    """规范化：补 H1/SC 编号/去多余空行，不改作者台词。返回 (md, changes[])。"""
    text = (md or "").strip().replace("\r\n", "\n")
    changes = []
    eid = (episode_id or "EP-DEMO01").strip() or "EP-DEMO01"
    if not re.search(r"^#\s+\S+", text, re.M):
        first = next((l.strip() for l in text.splitlines() if l.strip()), "未命名单集")
        text = "# %s %s\n\n" % (eid, first[:40]) + text
        changes.append("补首行H1")
    lines = []
    sc_n = 0
    for ln in text.splitlines():
        s = ln.rstrip()
        if re.match(r"^##\s*(SC)?\d*", s.strip()) and "·" not in s:
            sc_n += 1
            s = "## %s-SC%03d 内·主场景·夜" % (eid, sc_n)
            changes.append("补场景标题%d" % sc_n)
        elif re.match(r"^##\s+\S+", s.strip()):
            sc_n += 1
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    if "SC" not in text:
        changes.append("未检出场景（保留原文待人工补）")
    return text, changes


def estimate_screenplay(md):
    """时长估算：字数/对白/场景 -> 秒数。纯规则，供演示‘可拍性’证据。"""
    import re as _re
    text = (md or "")
    chars = len(text)
    # 手写标点剔除（无 regex 库依赖）
    punct = set(" \\t\\n\\r，。！？、；：:\"“”‘’（）()[\\]【】…—·—-…「」『』.·/、|")
    speak_chars = sum(1 for c in text if c not in punct)
    scenes = len(_re.findall(r"^##\s+\S+", text, _re.M))
    dialogues = sum(1 for l in text.splitlines()
                    if _re.match(r"^\s*[^#\[>\s][^：:]{1,12}[：:].+", l.strip()))
    # 口播 4.2字/s + 动作场均6s + 标签切换2s
    est = round(dialogues * 8 / 4.2 + max(scenes, 1) * 4 + 2, 1) if (dialogues or scenes) else 0.0
    est = max(5.0, min(90.0, est))
    return {"chars": chars, "speak_chars": speak_chars, "scenes": scenes,
            "dialogues": dialogues, "est_s": est,
            "in_range_10_30": 10 <= est <= 30}


def parse_beats_from_screenplay(md, episode_id=""):
    """从剧本 md 解析 beats：优先场景标题，其次对白句。供 export-bundle 用。"""
    text = (md or "").strip()
    beats = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("##") and len(beats) < 8:
            title = s.lstrip("#").strip()[:40]
            if title and "方案大纲" not in title:
                beats.append({"beat_id": "B%02d" % (len(beats) + 1),
                              "function": title, "text_cn": ""})
    if len(beats) < 2:
        for ln in text.splitlines():
            s = ln.strip()
            if re.match(r"^\s*[^#\[>\s][^：:]{1,12}[：:].+", s) and len(beats) < 8:
                beats.append({"beat_id": "B%02d" % (len(beats) + 1),
                              "function": s[:40], "text_cn": ""})
    return beats


def build_review(screenplay_md, shots, total_s=0):
    """真审查门：剧本结构 + 分镜覆盖 + 时长 + 模板感。返回 (verdict, findings)。"""
    findings = []
    for f in validate_screenplay(screenplay_md or ""):
        findings.append({"level": f["level"], "rule": f["rule"], "fix": f["fix"], "pos": f.get("pos", "")})
    if not shots:
        findings.append({"level": "blocker", "rule": "SHT-01", "fix": "无SHOT覆盖，先转草案", "pos": "分镜"})
    else:
        for s in shots:
            if not (s.get("duty") or "").strip():
                findings.append({"level": "major", "rule": "SHT-02", "fix": "%s缺duty一句话" % s.get("id", "?"), "pos": s.get("id", "")})
                break
        nodur = [s.get("id") for s in shots if not float(s.get("duration_s") or 0)]
        if nodur:
            findings.append({"level": "major", "rule": "SHT-03", "fix": "%s缺时长" % nodur[0], "pos": nodur[0]})
        nofirst = not any(((s.get("images") or []) and any(x.get("kind") == "first" for x in (s.get("images") or []))) for s in shots)
        if nofirst:
            findings.append({"level": "major", "rule": "SHT-04", "fix": "全集无首帧，至少给首镜挂1张", "pos": "首帧"})
    try:
        tot = float(total_s or sum(float(s.get("duration_s") or 0) for s in (shots or [])))
    except Exception:
        tot = 0
    if shots and not (10 <= tot <= 30):
        findings.append({"level": "major", "rule": "DUR-01", "fix": "合计%.1fs越界，精品段要求10-30s" % tot, "pos": "时长"})
    blockers = [f for f in findings if f["level"] == "blocker"]
    majors = [f for f in findings if f["level"] == "major"]
    if blockers:
        verdict = "BLOCK"
    elif majors:
        verdict = "REVISE"
    else:
        verdict = "PASS"
    return verdict, findings
