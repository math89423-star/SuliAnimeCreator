"""headless profile 的 provider 分组解析：模型 id → dsh provider 组。

dsh-llm-pi-ai 的 api 是 provider 级字段，网关按模型路由线协议
（chat/completions / responses / messages），所以 profile 把 provider 拆成三组，
每组各自列自己的模型。**模型不在它那一组里就等于 dsh 跑不了它**——
设置页只能让人选这里列出来的，否则「保存成功、实际没换模型」。

真源：$DSH_HOME/profiles/headless/cordis.patch.yml 的 llm-pi-ai 段。
"""
import os
import re
from pathlib import Path

DSH_HOME = os.getenv("DSH_HOME", str(Path.home() / ".dsh"))
FALLBACK_AGENT_MODEL = "deepseek-v4.1-flash"

# 组名 → 线协议（与 profile 的 llm-pi-ai 段一一对应）
GROUP_PROTOCOL = {
    "opencode-go": "/chat/completions",
    "opencode-go-responses": "/responses",
    "opencode-go-anthropic": "/messages",
}


def _patch_text():
    p = Path(DSH_HOME) / "profiles" / "headless" / "cordis.patch.yml"
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _llm_pi_ai_block():
    """profile patch 里 llm-pi-ai 那一段的原文（到下一个顶层条目为止）。"""
    text = _patch_text()
    i = text.find("- id: llm-pi-ai")
    if i < 0:
        return ""
    seg = text[i:]
    m = re.search(r"(?m)^- id: ", seg[10:])
    return seg[: 10 + m.start()] if m else seg


def model_groups():
    """{模型 id: provider 组}——profile 里列出来的就是 dsh 能真跑的。"""
    block = _llm_pi_ai_block()
    out = {}
    if not block:
        return out
    parts = re.split(r"(?m)^      ([a-z0-9-]+):\s*$", block)
    for i in range(1, len(parts), 2):
        group, body = parts[i], parts[i + 1]
        if group not in GROUP_PROTOCOL:
            continue
        for mid in re.findall(r"(?m)^\s+- id:\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$", body):
            out[mid] = group
    return out


def servable_models():
    """能跑的模型 id 列表（按 profile 里的声明顺序）。"""
    return list(model_groups().keys())


def default_model():
    """profile 的 agent-default-model（没写则回退）。"""
    m = re.search(r"(?ms)^- id: agent-default-model.*?^\s*model:\s*(\S+)\s*$", _patch_text())
    return m.group(1).strip("\"'") if m else FALLBACK_AGENT_MODEL


def group_of(model_id):
    """模型该落哪组；不在 profile 里返回 None。"""
    return model_groups().get((model_id or "").strip())
