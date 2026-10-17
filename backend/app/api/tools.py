"""tools 蓝图：给项目 Agent 补联网能力（免 key，无第三方依赖）。
GET /api/v1/tools/websearch?q=关键词&n=8  → SearXNG(本地8888) 主路 + Wikipedia/DDG 兜底。
GET /api/v1/tools/webfetch?url=...        → 抓页面正文（去标签，截断），供搜索后精读。
headless Agent 经 backend/AGENTS.md 发现这两个接口（curl 直调）。
"""
import html as _html
import os
import re
import shutil as _shutil
import subprocess as _subprocess
import urllib.parse
import urllib.request
import uuid as _uuid

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


_FFMPEG_BIN = ""
_MAX_VIDEO_BYTES = int(os.getenv("VIDEO_MAX_BYTES", str(300 * 1024 * 1024)))


def _ffmpeg_bin():
    """找 ffmpeg：系统优先，宿主无则用 imageio-ffmpeg 自带静态二进制，镜像里一定有系统版。"""
    global _FFMPEG_BIN
    if _FFMPEG_BIN:
        return _FFMPEG_BIN
    p = _shutil.which("ffmpeg")
    if p:
        _FFMPEG_BIN = p
        return p
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        q = get_ffmpeg_exe()
        import pathlib as _pl
        if q and _pl.Path(q).is_file():
            _FFMPEG_BIN = q
            return q
    except Exception:
        pass
    return ""


def _ff_duration(exe, src):
    try:
        r = _subprocess.run([exe, "-hide_banner", "-i", src],
                            capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr or "")
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 0.0


def _pick_evenly(times, n):
    """切点多于帧数上限时均匀挑选 n 个（含首尾），保证长片全片覆盖、不堆在开头。"""
    if len(times) <= n:
        return times
    if n <= 1:
        return [times[0]]
    step = (len(times) - 1) / (n - 1)
    idx = sorted({round(i * step) for i in range(n)})
    return [times[i] for i in idx]


@bp.post("/video-frames")
def video_frames():
    """视频参考抽帧：下载视频（或用已上传文件）→ ffmpeg 按场景切关键帧 → 返回 uploads 图。
    body: {url?, path?(@data/uploads/xxx 或 basename 二选一), max_frames=12(4-24), scene=0.35(0.1-0.9),
           start_s?, end_s?(秒, 可选: 只抽区间内的帧，前端时间轴圈选)}
    返回 {source, mode, duration_s, start_s, end_s, count, frames:[{name,url}]}，帧图走 /api/images/<name> 直接看。"""
    from pathlib import Path as _P
    b = request.get_json(force=True, silent=True) or {}
    url = (b.get("url") or "").strip()
    path = (b.get("path") or "").strip()
    try:
        max_frames = max(4, min(24, int(b.get("max_frames") or 12)))
    except (ValueError, TypeError):
        max_frames = 12
    try:
        scene = float(b.get("scene") or 0.35)
        scene = max(0.1, min(0.9, scene))
    except (ValueError, TypeError):
        scene = 0.35
    exe = _ffmpeg_bin()
    if not exe:
        return jsonify({"code": 5001, "msg": "无 ffmpeg：容器镜像自带，宿主 pip 装 imageio-ffmpeg 也有"}), 500
    root = _P(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    tag = _uuid.uuid4().hex[:12]
    if path:
        name = _P(path.replace("@data/uploads/", "")).name
        src = root / name
        if not name or not src.is_file():
            return jsonify({"code": 4004, "msg": "uploads 里没有这个视频文件"}), 404
        source = name
    elif url:
        if not (url.startswith("http://") or url.startswith("https://")):
            return jsonify({"code": 4001, "msg": "url 须 http(s) 开头"}), 400
        suf = _P(urllib.parse.urlsplit(url).path).suffix[:5] or ".mp4"
        if len(suf) > 5 or "." not in suf:
            suf = ".mp4"
        source = f"vsrc_{tag}{suf}"
        try:
            req = urllib.request.Request(url, headers=_UA)
            with urllib.request.urlopen(req, timeout=120) as r, open(root / source, "wb") as f:
                left = _MAX_VIDEO_BYTES
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    left -= len(chunk)
                    if left < 0:
                        raise ValueError("视频超过 %dMB 上限" % (_MAX_VIDEO_BYTES // 1024 // 1024))
                    f.write(chunk)
        except Exception as e:
            try:
                (root / source).unlink()
            except Exception:
                pass
            return jsonify({"code": 5001, "msg": "视频下载失败: %s" % str(e)[:200]}), 502
        src = root / source
    else:
        return jsonify({"code": 4001, "msg": "url/path 二选一"}), 400
    # 区间圈选（前端时间轴）：缺省整片；clamp 到有效范围，start/end 非法即退回全片
    total_d = _ff_duration(exe, str(src))
    try:
        start_s = max(0.0, float(b.get("start_s") or 0))
    except (ValueError, TypeError):
        start_s = 0.0
    try:
        end_s = max(0.0, float(b.get("end_s") or 0))
    except (ValueError, TypeError):
        end_s = 0.0
    if total_d > 0:
        start_s = min(start_s, max(0.0, total_d - 0.5))
        end_s = min(end_s, total_d) if end_s > start_s + 0.2 else total_d
    seg = end_s - start_s if end_s > start_s + 0.2 else 0.0
    seg_args = (["-ss", f"{start_s:.3f}"] if start_s > 0 else []) + (["-t", f"{seg:.3f}"] if seg > 0 else [])
    out_pat = str(root / f"vf_{tag}_%03d.jpg")
    last_err = ""
    fmap = {}
    mode = "scene"
    # pass1：先全片扫一遍切点（不写图、不看结尾）：长片切点多于帧数上限时均匀挑选，避免只抽开头
    scene_txt = root / f"vf_{tag}_scenes.txt"
    scene_list = []
    try:
        p1 = _subprocess.run(
            [exe, "-hide_banner", "-y", *seg_args, "-i", str(src), "-an", "-sn",
             "-vf", f"select='gt(scene,{scene})',metadata=print:file={scene_txt}",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=300)
        last_err = (p1.stderr or "")[-400:]
        if scene_txt.is_file():
            scene_list = sorted({round(float(m), 3) for m in re.findall(r"pts_time:([0-9.]+)", scene_txt.read_text())})
    except Exception as e:
        last_err = "scene 扫描失败: %s" % str(e)[:160]
    finally:
        try:
            scene_txt.unlink()
        except Exception:
            pass
    # pass2：挑选后的切点逐点精确抽帧（数量 = min(切点数, 上限)；帧文件按时间顺序编号）
    for i, t in enumerate(_pick_evenly(scene_list, max_frames), 1):
        out_f = root / f"vf_{tag}_{i:03d}.jpg"
        try:
            _subprocess.run(
                [exe, "-hide_banner", "-y", "-ss", f"{start_s + t:.3f}", "-i", str(src),
                 "-frames:v", "1", "-vf", "scale=960:-1,format=yuvj420p", "-q:v", "3", str(out_f)],
                capture_output=True, text=True, timeout=60)
        except Exception:
            pass
        if out_f.is_file():
            fmap[out_f.name] = round(start_s + t, 1)
    frames = sorted(root.glob(f"vf_{tag}_*.jpg"))
    if not frames:
        # 无切点（或切点检测不可用）：按 帧数上限÷时长 均匀采样——最密 0.5s/帧，长片自动变稀且覆盖全片
        dur = seg if seg > 0 else total_d
        fps = min(2.0, max_frames / dur) if dur > 0 else 1.0
        fps = max(1e-6, fps)
        try:
            p2 = _subprocess.run(
                [exe, "-hide_banner", "-y", *seg_args, "-i", str(src),
                 "-vf", f"fps={fps:.6f},scale=960:-1,format=yuvj420p",
                 "-frames:v", str(max_frames), "-q:v", "3", out_pat],
                capture_output=True, text=True, timeout=180)
            last_err = (p2.stderr or "")[-400:]
        except Exception as e:
            return jsonify({"code": 5001, "msg": "抽帧超时/失败: %s" % str(e)[:200]}), 500
        frames = sorted(root.glob(f"vf_{tag}_*.jpg"))
        fmap = {p.name: round(start_s + idx / fps, 1) for idx, p in enumerate(frames)}
        mode = "uniform"
    if not frames:
        return jsonify({"code": 5001, "msg": "没抽出关键帧（片子太平？调小 scene 重试）: %s" % last_err[-200:]}), 500
    return ok({"source": source, "mode": mode, "duration_s": round(total_d, 1),
               "start_s": round(start_s, 2), "end_s": round(end_s if end_s > start_s else total_d, 2),
               "count": len(frames),
               "frames": [{"name": p.name, "url": f"/api/images/{p.name}", "time_s": fmap.get(p.name)} for p in frames]})
