"""设置存储：模型配置的默认值 + 合并 + 去密钥视图。纯函数 + 落盘只走 disk_store。"""
from .disk_store import load

FILE = "model_settings.json"

LLM_PROVIDERS = ("opencode", "llamacpp")
IMAGE_PROVIDERS = ("sd-webui", "comfyui", "custom")

DEFAULTS = {
    "llm": {
        "provider": "opencode",
        "model": "opencode-go/deepseek-v4.1-flash",
        "base": "https://opencode.ai/zen/go/v1",
        "api_key": "",
        "local_url": "http://127.0.0.1:8080",
        "local_model": "",
        "effort": "",
    },
    "vlm": {
        "provider": "opencode",
        "model": "",
        "base": "https://opencode.ai/zen/go/v1",
        "api_key": "",
        "local_url": "http://127.0.0.1:8080",
        "local_model": "",
    },
    "image": {
        "provider": "sd-webui",
        "endpoint": "http://127.0.0.1:7860",
        "model": "",
        "api_key": "",
    },
}


def merged():
    stored = load(FILE, {}) or {}
    doc = {}
    for section, defaults in DEFAULTS.items():
        row = dict(defaults)
        if isinstance(stored.get(section), dict):
            for k in defaults:
                v = stored[section].get(k)
                if isinstance(v, str):
                    row[k] = v
        doc[section] = row
    return doc


def public(doc):
    """去密钥视图：密钥只暴露是否设置过。"""
    out = {}
    for section, row in doc.items():
        pub = dict(row)
        for k in ("api_key",):
            if k in pub:
                pub[k + "_set"] = bool(pub.pop(k))
        out[section] = pub
    return out


def str_limited(v, limit=500):
    v = v if isinstance(v, str) else ""
    return v.strip()[:limit]
