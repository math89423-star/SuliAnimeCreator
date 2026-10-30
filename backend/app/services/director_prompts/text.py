"""director 文本小件：对话正则 / CJK 检测 / PixAI 脚手架剥离 / 完整句判定。"""
import re

DIALOG = re.compile(r'^\s*([^：:\s\[\]]{1,12})\s*[:：]\s*(.+)\s*$')
CJK = re.compile(r'[\u3400-\u9fff]')

# duty 两种形态：短动作短语 vs 完整句（Agent 按 nsfw-directing 写的 duty_en）。
# 中文说话人 → 英文主体词：中文人称代词不能直译进英文句
PRONOUN_EN = {"她": "the woman", "女方": "the woman", "女": "the woman", "他": "the man",
              "男方": "the man", "男": "the man", "两人": "both of them", "旁白": "an off-screen voice"}
FULL_START = re.compile(r'^(the|his|her|their|she|he|they|both|adult|two|a man|a woman)\b', re.I)


def strip_prefix(duty):
    return (duty or "").replace("[规则拆]", "").replace("[AI拆]", "").strip()


def pixai_preformatted(text):
    """Agent 有时把 PixAI 格式预写进 duty_en。检测到就按已成稿处理，不二次套格式。"""
    t = text or ""
    return ("@image" in t.lower()) or bool(re.search(r"\[\s*(?:Scene\s*\d+:)?\s*\d", t)) or ("SFX:" in t)


def strip_pixai_scaffold(text):
    """把预写的 PixAI 脚手架剥掉，只留动作正文（给 H3 轨道用）。"""
    d = text or ""
    d = re.sub(r"@image\d+[^.]*\.\s*", "", d, flags=re.I)
    d = re.sub(r"\[\s*(?:Scene\s*\d+:)?\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*s?\s*\]", "", d)
    d = re.sub(r"\bVoice\s*[—\-][^:：]*[:：]\s*「[^」]*」", "", d)
    d = re.sub(r"\bSFX\s*:[^.]*", "", d, flags=re.I)
    return " ".join(d.split()).strip()


def looks_full(duty):
    d = (duty or "").strip()
    if not d:
        return False
    if ";" in d or len(d) > 90:
        return True
    return bool(FULL_START.match(d))
