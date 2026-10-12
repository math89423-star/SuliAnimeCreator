"""LLM 规则回退：无 key / 解析失败时的本地拆镜。不联网。"""
import re

DIALOG = re.compile(r'^\s*([^：:\s\[\]]{1,12})\s*[:：]\s*(.+)\s*$')


def heuristic_cuts(text, max_cuts=3):
    cuts = []
    for ln in (text or "无剧本占位").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = DIALOG.match(ln)
        if m:
            who, line = m.group(1), m.group(2)
            cuts.append({"duty": f"{who}台词：{line[:24]}", "duration_s": 5,
                         "crop": "close-up" if len(cuts) % 2 else "medium",
                         "sound": f"{who}：{line}", "key_text_en": f"{who} speaking, dialogue beat"})
            continue
        for sent in re.split(r'(?<=[。！？!?.])', ln):
            sent = sent.strip()
            if sent:
                cuts.append({"duty": f"动作：{sent[:24]}", "duration_s": 4,
                             "crop": "medium", "sound": "", "key_text_en": "action beat"})
            if len(cuts) >= max_cuts:
                break
        if len(cuts) >= max_cuts:
            break
    return cuts or [{"duty": "建立：" + (text or "")[:24], "duration_s": 4, "crop": "wide", "sound": "", "key_text_en": "establishing beat"}]
