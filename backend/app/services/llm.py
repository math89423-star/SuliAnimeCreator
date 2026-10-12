"""LLM门面：保持旧 import 路径可用，逻辑已拆到 llm_heuristic / llm_opencode。

- heuristic_cuts/DIALOG 来自 llm_heuristic（不联网回退）
- llm_cuts/vlm_chat/llm_cfg/vlm_cfg 来自 llm_opencode（网关客户端）
"""
from .llm_heuristic import DIALOG, heuristic_cuts
from .llm_opencode import (
    OPENCODE_BASE, LLAMACPP_DEFAULT,
    llm_cfg, vlm_cfg, llm_cuts, vlm_chat,
    _endpoint_for, _post, _post_openai, _resolve_key,
)

__all__ = [
    "DIALOG", "heuristic_cuts",
    "OPENCODE_BASE", "LLAMACPP_DEFAULT",
    "llm_cfg", "vlm_cfg", "llm_cuts", "vlm_chat",
]
