"""settings 蓝图：模型配置（LLM / VLM / 绘图）存取与连通测试。

落盘 backend/data/model_settings.json，进程重启不丢。
读接口永不返回密钥明文（只给 *_set 标记）；写接口空字符串表示保持原值。
"""
import json
import time
import urllib.request
import urllib.error
from flask import Blueprint, jsonify, request

from ..services.disk_store import load, save
from ..services import llm as llm_svc

bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")

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


def ok(data):
    return jsonify({"code": 0, "data": data})


def err(msg, code=1, status=400):
    return jsonify({"code": code, "data": None, "msg": msg}), status


def _merged():
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


def _public(doc):
    """去密钥视图：密钥只暴露是否设置过。"""
    out = {}
    for section, row in doc.items():
        pub = dict(row)
        for k in ("api_key",):
            if k in pub:
                pub[k + "_set"] = bool(pub.pop(k))
        out[section] = pub
    return out


def _str(v, limit=500):
    v = v if isinstance(v, str) else ""
    return v.strip()[:limit]


@bp.get("/models")
def get_models():
    return ok(_public(_merged()))


@bp.put("/models")
def put_models():
    body = request.get_json(silent=True) or {}
    doc = _merged()
    for section, defaults in DEFAULTS.items():
        incoming = body.get(section)
        if not isinstance(incoming, dict):
            continue
        row = doc[section]
        if section in ("llm", "vlm"):
            p = _str(incoming.get("provider"), 20)
            if p and p not in LLM_PROVIDERS:
                return err(f"{section}.provider 非法，仅支持 opencode / llamacpp")
            if p:
                row["provider"] = p
            for k in ("model", "base", "local_url", "local_model"):
                v = _str(incoming.get(k))
                if v:
                    row[k] = v
            # effort 仅 llm：允许设值，显式传空字符串时清掉（默认不发送）
            if section == "llm":
                ev = _str(incoming.get("effort"), 20)
                if ev:
                    if ev not in ("none", "minimal", "low", "medium", "high", "xhigh"):
                        return err("llm.effort 非法，仅支持 none / minimal / low / medium / high / xhigh")
                    row["effort"] = ev
                elif "effort" in incoming and isinstance(incoming.get("effort"), str):
                    row["effort"] = ""
            key = incoming.get("api_key")
            if isinstance(key, str) and key.strip():
                row["api_key"] = key.strip()[:500]
        else:
            p = _str(incoming.get("provider"), 20)
            if p and p not in IMAGE_PROVIDERS:
                return err("image.provider 非法，仅支持 sd-webui / comfyui / custom")
            if p:
                row["provider"] = p
            for k in ("endpoint", "model"):
                v = _str(incoming.get(k))
                if v:
                    row[k] = v
            key = incoming.get("api_key")
            if isinstance(key, str) and key.strip():
                row["api_key"] = key.strip()[:500]
    save(FILE, doc)
    return ok(_public(doc))


def _http_json(url, method="GET", body=None, headers=None, timeout=20):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"User-Agent": "Mozilla/5.0 SuliAnimeCreator/0.1",
                                          "Content-Type": "application/json",
                                          **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode(errors="replace")
    try:
        return r.status, json.loads(raw)
    except Exception:
        return r.status, {"raw": raw[:300]}


def _need_http(url):
    u = (url or "").strip()
    if not u.lower().startswith(("http://", "https://")):
        raise ValueError("地址须以 http:// 或 https:// 开头")
    return u.rstrip("/")


# 网关 key 未就绪时给下拉用的兜底（均为仓库已验证过路由规则的模型 id）
CURATED_OPENCODE = [
    "opencode-go/deepseek-v4.1-flash",
    "opencode-go/longcat-2.5-preview-free",
]

# 网关目录缓存：TTL 内直接复用（刷新按钮不再每次打网关）；
# 拉取失败时退回上次成功结果（source=cache），只有从未成功过才用 CURATED 兜底。
CATALOG_TTL = 120
CATALOG_FILE = "model_catalog_cache.json"
_memo = {}


def _memo_get(mkey):
    row = _memo.get(mkey)
    if row is None:
        disk = load(CATALOG_FILE, {}) or {}
        row = disk.get(mkey)
        if isinstance(row, dict):
            _memo[mkey] = row
    return row if isinstance(row, dict) else None


def _memo_put(mkey, payload):
    row = {"ts": time.time(), "payload": payload}
    _memo[mkey] = row
    try:
        disk = load(CATALOG_FILE, {}) or {}
        disk[mkey] = row
        save(CATALOG_FILE, disk)
    except Exception:
        pass


def _live_model_ids(base, key=""):
    """按 OpenAI 兼容格式从网关/本地服务拉模型 id 列表，失败抛异常。"""
    headers = {}
    if key:
        headers["Authorization"] = "Bearer " + key
    last = None
    for path in ("/models", "/v1/models"):
        try:
            _, data = _http_json(base + path, headers=headers, timeout=8)
            items = data.get("data") if isinstance(data, dict) else None
            if isinstance(items, list):
                ids = [m.get("id", "") for m in items if isinstance(m, dict) and m.get("id")]
                if ids:
                    return ids
        except Exception as e:
            last = e
    raise ValueError(f"拉取模型列表失败：{last or '网关无 /models 接口'}")


@bp.get("/models/catalog")
def models_catalog_get():
    """GET 仅查公开目录（不接受 key，key 走 POST body，避免进访问日志）。"""
    provider = (request.args.get("provider") or "").strip()
    return _catalog(provider, (request.args.get("base") or "").strip(), "")


@bp.post("/models/catalog")
def models_catalog_post():
    """POST 查目录，body: {provider, base?, key?}。"""
    body = request.get_json(silent=True) or {}
    provider = (body.get("provider") or "").strip()
    base = (body.get("base") or "").strip()
    key = (body.get("key") or "").strip()
    return _catalog(provider, base, key)


def _catalog(provider, base_q, key_q):
    """provider=opencode 走网关（有 key 则 live，无 key 试公开接口，失败给兜底）；
    provider=llamacpp 走本地服务 /v1/models。返回 {models:[{id, endpoint}], source}。"""
    if provider not in ("opencode", "llamacpp"):
        return err("provider 非法")
    if provider == "llamacpp":
        try:
            base = _need_http(base_q or llm_svc.LLAMACPP_DEFAULT)
        except ValueError as e:
            return err(str(e))
        try:
            ids = _live_model_ids(base, key_q)
        except Exception as e:
            return err(str(e))
        return ok({"models": [{"id": i, "endpoint": "chat"} for i in ids], "source": "live"})
    # opencode
    doc = _merged()
    base = base_q or (doc["llm"].get("base") or "").strip() or llm_svc.OPENCODE_BASE
    try:
        base = _need_http(base)
    except ValueError as e:
        return err(str(e))
    mkey = "opencode|" + base
    if not key_q:
        row = _memo_get(mkey)
        if row and time.time() - float(row.get("ts") or 0) < CATALOG_TTL:
            return ok(dict(row.get("payload") or {}))
    key = key_q.strip()
    if not key:
        key = (doc["llm"].get("api_key") or "").strip() or (doc["vlm"].get("api_key") or "").strip()
    if not key:
        key, _ = llm_svc._resolve_key()
    ids, source = [], "live"
    for k in ([key, ""] if key else [""]):
        try:
            ids = _live_model_ids(base, k)
            break
        except Exception:
            continue
    if not ids:
        row = _memo_get(mkey)
        if row and isinstance(row.get("payload"), dict):
            data = dict(row["payload"])
            data["source"] = "cache"
            return ok(data)
        ids, source = list(CURATED_OPENCODE), "curated"
    import re as _re
    out = []
    for raw in ids:
        mid = _re.sub(r"^opencode-go/", "", raw)
        out.append({"id": raw, "endpoint": llm_svc._endpoint_for(mid).lstrip("/")})
    data = {"models": out, "source": source, "base": base}
    if source == "live" and not key_q:
        _memo_put(mkey, data)
    return ok(data)


@bp.post("/models/test")
def test_models():
    """测连通。body: {section: llm|vlm|image, config?: {...}}，不带 config 则测已保存值。"""
    body = request.get_json(silent=True) or {}
    section = _str(body.get("section"), 10)
    if section not in DEFAULTS:
        return err("section 非法")
    cfg = dict(_merged()[section])
    incoming = body.get("config")
    if isinstance(incoming, dict):
        for k, v in incoming.items():
            if isinstance(v, str) and v.strip() and k in cfg:
                cfg[k] = v.strip()
    try:
        if section in ("llm", "vlm"):
            detail = _test_text_model(cfg)
        else:
            detail = _test_image_model(cfg)
    except ValueError as e:
        return err(str(e))
    except Exception as e:
        return err(f"连接失败：{type(e).__name__}: {e}")
    return ok({"ok": True, "detail": detail})


def _test_text_model(cfg):
    provider = cfg.get("provider") or "opencode"
    if provider == "llamacpp":
        base = _need_http(cfg.get("local_url") or "http://127.0.0.1:8080")
        try:
            _, data = _http_json(base + "/health", timeout=10)
            if isinstance(data, dict) and data.get("status") in ("ok", "loading"):
                return f"llama.cpp 健康检查通过：{data}"
        except Exception:
            pass
        status, data = _http_json(base + "/v1/models", timeout=10)
        names = []
        try:
            names = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
        except Exception:
            pass
        want = (cfg.get("local_model") or cfg.get("model") or "").strip()
        hint = f"，目标模型 {want} " + ("在列表中" if want in names else "不在列表中") if want else ""
        return f"llama.cpp /v1/models HTTP {status}，在线模型 {len(names)} 个{hint}"
    # opencode 网关：发一条最小请求
    base = _need_http(cfg.get("base") or llm_svc.OPENCODE_BASE)
    key = (cfg.get("api_key") or "").strip()
    if not key:
        key, _ = llm_svc._resolve_key()
    if not key:
        raise ValueError("缺 API Key：请在配置里填写，或设置 OPENCODE_API_KEY 环境变量")
    import re as _re
    model_id = _re.sub(r"^opencode-go/", "", (cfg.get("model") or "").strip())
    if not model_id:
        raise ValueError("模型 id 为空")
    txt = llm_svc._post(base, key, model_id, "只回 ok 两个字母", timeout=30,
                         effort=cfg.get("effort", ""))
    return f"opencode 网关 {model_id} 应答：{(txt or '').strip()[:120]}"


def _test_image_model(cfg):
    provider = cfg.get("provider") or "custom"
    ep = _need_http(cfg.get("endpoint") or "")
    if not ep:
        raise ValueError("endpoint 为空")
    if provider == "sd-webui":
        status, data = _http_json(ep + "/sdapi/v1/samplers", timeout=15)
        n = len(data) if isinstance(data, list) else 0
        return f"SD WebUI 连通 HTTP {status}，采样器 {n} 个"
    if provider == "comfyui":
        status, _ = _http_json(ep + "/system_stats", timeout=15)
        return f"ComfyUI 连通 HTTP {status}"
    status, _ = _http_json(ep, timeout=15)
    return f"自定义接口 HTTP {status}"
