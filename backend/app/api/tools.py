"""tools 蓝图：给项目 Agent 补联网能力（免 key，无第三方依赖）。
GET /api/v1/tools/websearch?q=关键词&n=8  → SearXNG(本地8888) 主路 + Wikipedia/DDG 兜底。
GET /api/v1/tools/webfetch?url=...        → 抓页面正文（去标签，截断），供搜索后精读。
headless Agent 经 backend/AGENTS.md 发现这两个接口（curl 直调）。
"""
import html as _html
import os
import re
import urllib.parse
import urllib.request

from flask import Blueprint, request, jsonify

bp = Blueprint("tools", __name__, url_prefix="/api/v1/tools")

_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
_TIMEOUT = 12
_SEARXNG = os.getenv("SEARXNG_URL", "http://127.0.0.1:8888").rstrip("/")


def ok(data):
    return jsonify({"code": 0, "data": data})


def _get_json(url):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def _searxng(q, limit=10):
    """本地 SearXNG 主路：通用网页搜索，无需 key。"""
    import json as _json
    url = ("%s/search?q=%s&format=json&language=zh-CN" % (_SEARXNG, urllib.parse.quote(q)))
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            items = _json.loads(r.read().decode("utf-8", "replace")).get("results", [])
    except Exception:
        return []
    out = []
    for it in items[:limit]:
        if not it.get("url"):
            continue
        out.append({"title": it.get("title") or it["url"], "url": it["url"],
                    "snippet": (it.get("content") or "")[:300],
                    "source": "searxng-%s" % (it.get("engine") or "?")})
    return out


def _wiki_search(q, lang, limit=5):
    """Wikipedia opensearch：免 key，最稳的一路。"""
    import json as _json
    url = ("https://%s.wikipedia.org/w/api.php?action=opensearch&format=json&limit=%d&search=%s"
           % (lang, limit, urllib.parse.quote(q)))
    try:
        titles, descs, urls = _json.loads(_get_json(url))[1:4]
    except Exception:
        return []
    out = []
    for t, d, u in zip(titles, descs, urls):
        out.append({"title": t, "url": u, "snippet": d or t, "source": "wikipedia-" + lang})
    return out


def _wiki_fulltext(q, lang, limit=5):
    """Wikipedia 全文检索：opensearch（标题前缀）没命中时的兜底。"""
    import json as _json
    url = ("https://%s.wikipedia.org/w/api.php?action=query&format=json&list=search&srlimit=%d&srsearch=%s"
           % (lang, limit, urllib.parse.quote(q)))
    try:
        items = _json.loads(_get_json(url))["query"]["search"]
    except Exception:
        return []
    out = []
    for it in items:
        t = it.get("title", "")
        snip = re.sub(r"<[^>]+>", "", it.get("snippet", ""))[:300]
        out.append({"title": t, "url": "https://%s.wikipedia.org/wiki/%s" % (lang, urllib.parse.quote(t.replace(" ", "_"))),
                    "snippet": _html.unescape(snip), "source": "wikipedia-" + lang})
    return out


def _ddg_instant(q):
    """DDG 即时答案：免 key，有摘要时才有货，无则空。"""
    import json as _json
    url = ("https://api.duckduckgo.com/?format=json&no_html=1&skip_disambig=1&q=%s"
           % urllib.parse.quote(q))
    try:
        d = _json.loads(_get_json(url))
    except Exception:
        return []
    out = []
    if (d.get("AbstractText") or "").strip():
        out.append({"title": d.get("Heading") or q, "url": d.get("AbstractURL") or "",
                    "snippet": d["AbstractText"][:300], "source": "ddg-instant"})
    for t in (d.get("RelatedTopics") or [])[:6]:
        if isinstance(t, dict) and t.get("FirstURL"):
            out.append({"title": (t.get("Text") or "")[:80] or t["FirstURL"],
                        "url": t["FirstURL"], "snippet": (t.get("Text") or "")[:300],
                        "source": "ddg-instant"})
    return out


@bp.get("/websearch")
def websearch():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"code": 4001, "msg": "q 为空"}), 400
    try:
        n = max(1, min(int(request.args.get("n", "8")), 20))
    except ValueError:
        n = 8
    rows = _searxng(q, limit=n)
    if len(rows) < n:
        rows += _wiki_search(q, "zh") + _wiki_search(q, "en") + _ddg_instant(q)
    if not rows:
        rows = _wiki_fulltext(q, "zh") + _wiki_fulltext(q, "en")
    seen, uniq = set(), []
    for r in rows:
        if not r["url"] or r["url"] in seen:
            continue
        seen.add(r["url"])
        uniq.append(r)
        if len(uniq) >= n:
            break
    return ok({"q": q, "results": uniq})


_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_HTML_RE = re.compile(r"<[^>]+>")


@bp.get("/webfetch")
def webfetch():
    url = (request.args.get("url") or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"code": 4001, "msg": "url 须 http(s) 开头"}), 400
    try:
        p = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit((p.scheme, p.netloc.encode("idna").decode("ascii"),
                                       urllib.parse.quote(urllib.parse.unquote(p.path)),
                                       urllib.parse.quote(urllib.parse.unquote(p.query), safe="=&"),
                                       p.fragment))
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()[:600000].decode("utf-8", "replace")
    except Exception as e:
        return jsonify({"code": 5001, "msg": "抓取失败: %s" % str(e)[:200]}), 502
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if m:
        title = _html.unescape(re.sub(r"\s+", " ", m.group(1)).strip())[:200]
    text = _TAG_RE.sub(" ", raw)
    text = _HTML_RE.sub(" ", text)
    text = _html.unescape(re.sub(r"\s+", " ", text)).strip()[:12000]
    return ok({"url": url, "title": title, "text": text})
