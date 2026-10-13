"""draft 轻链：草案发散不走 dsh，直接调 LLM 网关 + 规则回退。

定位（2026-10-13）：dsh 只留 skill 加载 + 单会话（episode 一集一会话）做导演判断；
草案发散（发散/大纲/转草案）走本模块，失败永远有 heuristic 保底，不抛 500。
"""
import re


MOVEMENTS = ["固定", "推", "拉", "摇", "移", "跟", "环绕", "升降", "手持", "航拍"]
CROPS = ["extreme_close", "closeup", "close", "medium_close", "medium",
         "medium_full", "full", "wide", "extreme_wide"]


def expand_idea(idea, n=3):
    """发散 n 个方向：LLM 优先，失败回模板（兼容旧 story/suggest 三档）。"""
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


def _outline_template(episode_id, total_s, shots_n, engine, tier, hint=""):
    total_s = total_s or 15
    tier_name = {"nsfw": "成人向", "sfw": "普通"}.get(tier or "", "常规")
    lines = [
        "# 方案大纲 %s" % (episode_id or ""),
        "",
        "## 方向一句话",
        "%s（%s，%s，合计约 %ss）" % ((hint or "单图氛围延续").strip(), tier_name, engine or "pixai", total_s),
        "",
        "## 基调与档位",
        "- 档位：%s / 引擎：%s" % (tier_name, engine or "pixai"),
        "- 约束：单镜 3-8 秒，一镜一事件",
        "",
        "## 分镜大纲表",
        "",
        "| 镜号 | 内容一句话 | 预计时长 | 运镜方向 | 备注 |",
        "| --- | --- | --- | --- | --- |",
    ]
    per = max(3, min(8, round(total_s / max(1, shots_n))))
    for i in range(1, shots_n + 1):
        mov = MOVEMENTS[i % len(MOVEMENTS)]
        lines.append("| %d | 氛围延续第%d镜 | %d秒 | %s | 草案待定稿 |" % (i, i, per, mov))
    lines += ["", "## 合计时长", "", "约 %s 秒，共 %d 镜。" % (per * shots_n, shots_n), ""]
    return "\n".join(lines)


def build_outline_md(episode_id, total_s=15, engine="pixai", tier="", hint="", ref_image=""):
    """轻大纲：LLM 优先写 markdown，失败回模板。永远返回 (md, engine_tag)。"""
    total_s = int(total_s or 15)
    shots_n = 3 if total_s <= 15 else (4 if total_s <= 24 else 5)
    try:
        from .llm_opencode import llm_cfg, _post
        cfg = llm_cfg()
        if cfg.get("provider") == "opencode" and cfg.get("key") and cfg.get("model"):
            model_id = re.sub(r"^opencode-go/", "", cfg["model"])
            prompt = ("只做方案大纲 markdown，含：方向一句话/基调与档位/分镜大纲表"
                      "(镜号|内容一句话|预计时长|运镜方向|备注)/合计时长。"
                      "%d-%d镜，单镜3-8秒，总计约%d秒，引擎%s档位%s。背景：%s"
                      % (shots_n, shots_n, total_s, engine or "pixai",
                         tier or "常规", (hint or "")[:800]))
            txt = _post(cfg["base"], cfg["key"], model_id, prompt,
                        effort=cfg.get("effort", ""))
            txt = (txt or "").strip()
            if len(txt) >= 40 and "镜" in txt:
                return txt, "llm"
    except Exception:
        pass
    return _outline_template(episode_id, total_s, shots_n, engine, tier, hint), "template"


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
    try:
        d = float(v)
        return max(1, min(8, int(round(d))))
    except (ValueError, TypeError):
        return fallback


def split_outline_to_shots(outline_md, episode_id, total_s=15, tier=""):
    """大纲转草案参数：优先 llm_cuts 逐段拆，失败按表行数均分。返回 (list, tag)。"""
    text = (outline_md or "").strip()
    total_s = int(total_s or 15)
    rows = [l for l in text.splitlines() if l.strip().startswith("|")]
    data_rows = [l for l in rows if not re.match(r'^\|\s*-', l.strip())][1:]
    n = min(5, max(2, len(data_rows) or 3))
    duties = []
    for l in data_rows:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1]:
            duties.append(cells[1][:60])
    try:
        from .llm import llm_cuts
        cuts = llm_cuts(text[:2000])[:n]
        if cuts:
            per = max(3, min(8, round(total_s / len(cuts))))
            out = []
            for i, c in enumerate(cuts):
                out.append({
                    "duty": c.get("duty", "")[:80] or ("大纲第%d镜" % (i + 1)),
                    "duty_en": c.get("key_text_en", "")[:200] or "",
                    "duration_s": _norm_dur(c.get("duration_s"), per),
                    "sound": c.get("sound", "") or "",
                    "tier": (tier or "").strip(),
                    "camera": {"crop": _norm_crop(c.get("crop")),
                               "movement": MOVEMENTS[(i + 1) % len(MOVEMENTS)]},
                })
            return out, "llm"
    except Exception:
        pass
    per = max(3, min(8, round(total_s / n)))
    out = []
    for i in range(n):
        duty = duties[i] if i < len(duties) else ("大纲第%d镜" % (i + 1))
        out.append({
            "duty": duty,
            "duty_en": "",
            "duration_s": per,
            "sound": "",
            "tier": (tier or "").strip(),
            "camera": {"crop": "medium",
                       "movement": MOVEMENTS[(i + 1) % len(MOVEMENTS)]},
        })
    return out, "template"
