"""opencode-go 网关 + 本地 llama.cpp 客户端。只做分镜文本，不碰生图/视频。
配置来源：data/model_settings.json（设置页）→ 环境变量 → 默认值。
依据：https://opencode.ai/docs/go（Go计划 base https://opencode.ai/zen/go/v1）。
"""
import os
import re
import json
import urllib.request
import urllib.error
from pathlib import Path

from . import dsh_profile

OPENCODE_BASE = "https://opencode.ai/zen/go/v1"
LLAMACPP_DEFAULT = "http://127.0.0.1:8080"


def _resolve_key():
    """key 链：OPENCODE_API_KEY 环境变量 → dsh 凭据 OPENCODE_GO_API_KEY 引用（开发机）。
    日志只打掩码，绝不打印明文。"""
    key = os.getenv("OPENCODE_API_KEY", "").strip()
    if key:
        return key, "env:OPENCODE_API_KEY"
    try:
        text = Path.home().joinpath(".dsh/.credentials.yaml").read_text()
        m = re.search(r"OPENCODE_GO_API_KEY:\s*(\S+)", text)
        if m:
            return m.group(1).strip(), "dsh-credentials:OPENCODE_GO_API_KEY"
    except Exception:
        pass
    return "", "none"


def _stored_section(name):
    """读设置页落盘的模型配置，缺文件时回空 dict（调用方再套 env/默认）。"""
    try:
        from .disk_store import load as _load
        doc = _load("model_settings.json", {}) or {}
        sec = doc.get(name)
        return sec if isinstance(sec, dict) else {}
    except Exception:
        return {}


def llm_cfg():
    """合并后的 LLM 生效配置：设置文件优先，空项回落环境变量/默认值。"""
    s = _stored_section("llm")
    provider = (s.get("provider") or "opencode").strip() or "opencode"
    if provider == "llamacpp":
        return {
            "provider": "llamacpp",
            "base": (s.get("local_url") or "").strip() or LLAMACPP_DEFAULT,
            "model": (s.get("local_model") or s.get("model") or "").strip(),
            "key": (s.get("api_key") or "").strip(),
        }
    key, key_src = _resolve_key()
    return {
        "provider": "opencode",
        "base": (s.get("base") or "").strip() or os.getenv("OPENCODE_BASE", "").strip() or OPENCODE_BASE,
        "model": (s.get("model") or "").strip() or os.getenv("OPENCODE_MODEL", "opencode-go/deepseek-v4.1-flash").strip(),
        "key": (s.get("api_key") or "").strip() or key,
        "key_src": "settings" if (s.get("api_key") or "").strip() else key_src,
        "effort": (s.get("effort") or "").strip(),
    }


def vlm_cfg():
    """合并后的 VLM 生效配置（结构同 llm）。"""
    s = _stored_section("vlm")
    provider = (s.get("provider") or "opencode").strip() or "opencode"
    if provider == "llamacpp":
        return {
            "provider": "llamacpp",
            "base": (s.get("local_url") or "").strip() or LLAMACPP_DEFAULT,
            "model": (s.get("local_model") or s.get("model") or "").strip(),
            "key": (s.get("api_key") or "").strip(),
        }
    key, key_src = _resolve_key()
    return {
        "provider": "opencode",
        "base": (s.get("base") or "").strip() or os.getenv("OPENCODE_BASE", "").strip() or OPENCODE_BASE,
        "model": (s.get("model") or "").strip(),
        "key": (s.get("api_key") or "").strip() or key,
        "key_src": "settings" if (s.get("api_key") or "").strip() else key_src,
        "effort": (s.get("effort") or "").strip(),
    }


def _endpoint_for(model_id):
    """模型走哪条线协议（/chat/completions | /responses | /messages）。

    真源 = headless profile 的 provider 分组（那边是按网关实际路由分好的，
    实测出来的）；profile 里没有的才走前缀启发式兜底。
    前缀启发式会错：minimax-m3.1-flash-free 实际走 openai/chat，
    按前缀猜成 /messages 会被网关判 ModelProtocolUnsupported。
    """
    mid = re.sub(r"^opencode-go/", "", (model_id or "").strip())
    group = dsh_profile.group_of(mid)
    if group:
        return dsh_profile.GROUP_PROTOCOL[group]
    m = mid.lower()
    if m.startswith(("muse-spark", "grok-", "gpt-")):
        return "/responses"
    if m.startswith(("minimax-", "qwen")):
        return "/messages"
    return "/chat/completions"


def _parse_chat(data):
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "")


def _gateway_error(e, where):
    """把网关的拒绝理由翻成人话：HTTPError 的 body 里才有真话（Invalid credential /
    api_key_expired / MissingSessionID），默认的 "HTTP Error 401" 什么也看不出来。"""
    body = ""
    try:
        body = e.read().decode("utf-8", "replace")
    except Exception:
        pass
    msg = ""
    if body:
        try:
            d = json.loads(body)
            err_obj = d.get("error") if isinstance(d, dict) else None
            if isinstance(err_obj, dict):
                msg = str(err_obj.get("message") or err_obj.get("code") or "")
            elif isinstance(err_obj, str):
                msg = err_obj
            if not msg and isinstance(d, dict):
                msg = str(d.get("msg") or d.get("message") or "")
        except Exception:
            msg = body[:200]
    code = getattr(e, "code", "") or ""
    hint = ""
    low = (msg or "").lower()
    if "api_key_expired" in low or "expired" in low:
        hint = "（key 已过期：去 OpenCode Console 新建一把推理 key，替换设置页的 api_key）"
    elif "invalid credential" in low or "requires a credential" in low:
        hint = "（网关不认这把 key：key 无效、已被吊销，或不是这把账号的推理 key）"
    elif "missingsessionid" in low:
        hint = "（请求缺 x-opencode-session 头）"
    return ValueError("%s HTTP %s：%s%s" % (where, code, (msg or "无返回内容")[:300], hint))


def _post_openai(base, key, model, messages, timeout=60):
    """OpenAI 兼容 chat 接口（本地 llama.cpp --chat-completion 即此协议）。"""
    body = {"model": model, "messages": messages}
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 SuliAnimeCreator/0.1"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise _gateway_error(e, "网关拒绝")
    return _parse_chat(data)


def _post(base, key, model_id, prompt, timeout=60, effort=""):
    import uuid as _uuid
    path = _endpoint_for(model_id)
    effort = (effort or "").strip()
    if effort not in ("none", "minimal", "low", "medium", "high", "xhigh"):
        effort = ""
    if path == "/responses":
        body = {"model": model_id, "input": prompt}
        if effort:
            body["reasoning"] = {"effort": effort}
    elif path == "/messages":
        body = {"model": model_id, "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]}
    else:
        body = {"model": model_id,
                "messages": [{"role": "user", "content": prompt}]}
        if effort:
            body["reasoning_effort"] = effort
    req = urllib.request.Request(base.rstrip("/") + path, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 SuliAnimeCreator/0.1",
                 "x-opencode-session": "sulianimecreator-" + _uuid.uuid4().hex[:12]})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise _gateway_error(e, "网关拒绝")
    if path == "/responses":
        parts = []
        for item in data.get("output") or []:
            for c in item.get("content") or []:
                if isinstance(c, dict) and c.get("text"):
                    parts.append(c["text"])
        return "\n".join(parts)
    if path == "/messages":
        return "\n".join(c.get("text", "") for c in data.get("content") or [] if isinstance(c, dict))
    return _parse_chat(data)


def llm_cuts(seg_text, assets=None):
    cfg = llm_cfg()
    prompt = ("只做分镜文本，输出JSON数组，每镜含duty/duration_s/crop/sound/key_text_en，1-4镜。场次文本：\n" + seg_text[:2000])
    if cfg["provider"] == "llamacpp":
        if not cfg["model"]:
            raise ValueError("LLM未启用：llama.cpp 模型名为空，请到设置页填写")
        txt = _post_openai(cfg["base"], cfg["key"], cfg["model"],
                            [{"role": "user", "content": prompt}])
    else:
        model_id = re.sub(r"^opencode-go/", "", cfg["model"])
        if not cfg["key"]:
            raise ValueError("LLM未启用：缺OPENCODE_API_KEY（或dsh凭据OPENCODE_GO_API_KEY），也可到设置页填写")
        txt = _post(cfg["base"], cfg["key"], model_id, prompt, effort=cfg.get("effort", ""))
    m = re.search(r'\[.*\]', txt, re.S)
    if not m:
        raise ValueError("LLM解析失败")
    return json.loads(m.group(0))


def vlm_chat(prompt, images=None):
    """最小可用 VLM：一句话配图理解。images 为 base64 data-url 或 http(s) 图床数组。"""
    cfg = vlm_cfg()
    parts = [{"type": "text", "text": prompt}]
    for img in images or []:
        parts.append({"type": "image_url", "image_url": {"url": img}})
    messages = [{"role": "user", "content": parts}]
    if cfg["provider"] == "llamacpp":
        if not cfg["model"]:
            raise ValueError("VLM未启用：llama.cpp 模型名为空，请到设置页填写")
        return _post_openai(cfg["base"], cfg["key"], cfg["model"], messages)
    model_id = re.sub(r"^opencode-go/", "", cfg["model"])
    if not model_id:
        raise ValueError("VLM未启用：opencode 模型 id 为空，请到设置页填写")
    if not cfg["key"]:
        raise ValueError("VLM未启用：缺 API Key")
    if _endpoint_for(model_id) != "/chat/completions":
        raise ValueError(f"VLM模型 {model_id} 不走 chat 协议，请换 chat 兼容模型")
    return _post(cfg["base"], cfg["key"], model_id, parts, effort=cfg.get("effort", ""))
