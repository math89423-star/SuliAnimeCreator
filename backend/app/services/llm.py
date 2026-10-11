"""LLM拆镜：全站 key 只走 opencode-go provider（与 dsh headless 同路）。
端点映射照 MirrorStage ai_config（muse-spark/grok/gpt 走 /responses，
minimax/qwen 走 /messages，其余 /chat/completions）；model 写作兼容
opencode-go/<id> 前缀，调用网关时剥掉。只做分镜文本，不碰生图/视频。
依据：https://opencode.ai/docs/go（Go计划 base https://opencode.ai/zen/go/v1）。
"""
import os, re, json, urllib.request
from pathlib import Path

OPENCODE_BASE = "https://opencode.ai/zen/go/v1"

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


def _endpoint_for(model_id):
    m = model_id.lower()
    if m.startswith(("muse-spark", "grok-", "gpt-")):
        return "/responses"
    if m.startswith(("minimax-", "qwen")):
        return "/messages"
    return "/chat/completions"


def _post(base, key, model_id, prompt, timeout=60):
    import uuid as _uuid
    path = _endpoint_for(model_id)
    if path == "/responses":
        body = {"model": model_id, "input": prompt}
    elif path == "/messages":
        body = {"model": model_id, "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]}
    else:
        body = {"model": model_id,
                "messages": [{"role": "user", "content": prompt}]}
    # 网关硬性要求：浏览器 UA（防 1010）+ x-opencode-session 会话头（防 MissingSessionID）
    req = urllib.request.Request(base.rstrip("/") + path, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 SuliAnimeCreator/0.1",
                 "x-opencode-session": "sulianimecreator-" + _uuid.uuid4().hex[:12]})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode())
    if path == "/responses":
        parts = []
        for item in data.get("output") or []:
            for c in item.get("content") or []:
                if isinstance(c, dict) and c.get("text"):
                    parts.append(c["text"])
        return "\n".join(parts)
    if path == "/messages":
        return "\n".join(c.get("text", "") for c in data.get("content") or [] if isinstance(c, dict))
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "")


def llm_cuts(seg_text, assets=None):
    base = os.getenv("OPENCODE_BASE", "").strip() or OPENCODE_BASE
    key, key_src = _resolve_key()
    raw_model = os.getenv("OPENCODE_MODEL", "opencode-go/muse-spark-1.3-contributor").strip()
    model_id = re.sub(r"^opencode-go/", "", raw_model)  # 网关要裸 id
    if not key:
        raise ValueError("LLM未启用：缺OPENCODE_API_KEY（或dsh凭据OPENCODE_GO_API_KEY）")
    prompt = ("只做分镜文本，输出JSON数组，每镜含duty/duration_s/crop/sound/key_text_en，1-4镜。场次文本：\n" + seg_text[:2000])
    txt = _post(base, key, model_id, prompt)
    m = re.search(r'\[.*\]', txt, re.S)
    if not m:
        raise ValueError("LLM解析失败")
    return json.loads(m.group(0))
