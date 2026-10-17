"""SuliAnimeCreator 全量功能测试（HTTP 集成 + 静态审计，纯标准库，无第三方依赖）。

运行：  python -m pytest test/ -x -q        （需后端在 127.0.0.1:5001 就绪）
        Suli_BASE=http://127.0.0.1:5001 python -m pytest test/ -q

约定：只读 EP-81695F 等现成数据做断言；写操作只建新包/传小文件，不碰现成集。
"""
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import zipfile

BASE = os.getenv("Suli_BASE", "http://127.0.0.1:5001").rstrip("/")
EP = "EP-81695F"  # 演示集：大纲+草案3镜现成


class ApiError(AssertionError):
    pass


def req(method, path, body=None, query=None, timeout=60, raw=False):
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = headers = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            payload = resp.read()
            if raw:
                return resp.status, payload
            return resp.status, json.loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as e:
        payload = e.read()
        try:
            return e.code, json.loads(payload.decode("utf-8"))
        except Exception:
            return e.code, {"_raw": payload[:200]}


def ok(path, **kw):
    st, d = req("GET", path, **kw)
    assert st == 200, f"{path} http={st} {str(d)[:200]}"
    assert d.get("code") == 0, f"{path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]
