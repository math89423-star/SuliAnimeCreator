"""tools 蓝图：给项目 Agent 补联网能力（免 key，无第三方依赖）。
GET /api/v1/tools/websearch?q=关键词&n=8  → SearXNG(本地) 主路 + Bing 中文站 + Wikipedia/DDG 兜底。
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
from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor

from flask import Blueprint, request, jsonify

bp = Blueprint("tools", __name__, url_prefix="/api/v1/tools")

_UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
_TIMEOUT = 8
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
        with urllib.request.urlopen(req, timeout=4) as r:
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


def _bing(q, limit=8):
    """Bing 中文站 HTML 兜底：免 key；中文长尾词/游戏角色名比 Wikipedia 稳。"""
    url = "https://cn.bing.com/search?q=%s&setlang=zh-CN" % urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers={**_UA, "Accept-Language": "zh-CN,zh;q=0.9"})
        with urllib.request.urlopen(req, timeout=10) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception:
        return []
    out = []
    for block in re.findall(r'<li class="b_algo".*?</li>', page, re.S):
        m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        link = _html.unescape(m.group(1)).strip()
        if not link.startswith("http"):
            continue
        title = _html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        snip = ""
        p = re.search(r"<p[^>]*>(.*?)</p>", block, re.S)
        if p:
            snip = _html.unescape(re.sub(r"<[^>]+>", "", p.group(1))).strip()
        out.append({"title": title or link, "url": link, "snippet": snip[:300], "source": "bing-cn"})
        if len(out) >= limit:
            break
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


@bp.route("/websearch", methods=["GET", "POST"])
def websearch():
    body = request.get_json(silent=True) or {}
    q = (request.args.get("q") or request.form.get("q") or body.get("q") or "").strip()
    if not q:
        return jsonify({"code": 4001, "msg": "q 为空"}), 400
    try:
        n = max(1, min(int(request.args.get("n") or request.form.get("n") or body.get("n") or 8), 20))
    except ValueError:
        n = 8
    # SearXNG 与 Bing 并发：中文长尾词 Bing 常 0.5s 回；SearXNG 慢也不拖住整体
    with _ThreadPoolExecutor(max_workers=2) as ex:
        f_searx = ex.submit(_searxng, q, n)
        f_bing = ex.submit(_bing, q, n)
        rows = f_searx.result() + f_bing.result()
    if not rows:
        rows = (_wiki_search(q, "zh") + _wiki_search(q, "en") + _ddg_instant(q)
                + _wiki_fulltext(q, "zh") + _wiki_fulltext(q, "en"))
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


def _norm_range(b, total_d):
    """start_s/end_s（秒）→ (start_s, end_s, seg, seg_args)；缺省整片，非法退回全片（video-frames 同款口径）。"""
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
    return start_s, end_s, seg, seg_args


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
    start_s, end_s, seg, seg_args = _norm_range(b, total_d)
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


# ---- 深度拉片（复刻级拆解）：S0 切点清单 + S1/S2 逐镜帧墙 ----
# 设计口径见 skills/video/deep-teardown/SKILL.md：agent 先用 video-scenes 拿镜头表，
# 再用 shots-frames 把「每镜 2-4 帧」拼成带时间标签的接触表（一图看多镜，省读图次数）。
_FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _resolve_src(b, root, tag):
    """url/path 二选一 → (src 路径, source 名)；异常抛 ValueError（中文提示）。"""
    from pathlib import Path as _P
    url = (b.get("url") or "").strip()
    path = (b.get("path") or "").strip()
    if path:
        name = _P(path.replace("@data/uploads/", "")).name
        src = root / name
        if not name or not src.is_file():
            raise ValueError("uploads 里没有这个视频文件")
        return src, name
    if not url:
        raise ValueError("url/path 二选一")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("url 须 http(s) 开头")
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
        raise ValueError("视频下载失败: %s" % str(e)[:200])
    return root / source, source


def _scan_cuts(exe, src, seg_args, scene, scene_txt, timeout=300):
    """ffmpeg select+metadata 扫切点（video-frames pass1 同款），返回相对区间起点的切点秒表。"""
    try:
        _subprocess.run(
            [exe, "-hide_banner", "-y", *seg_args, "-i", str(src), "-an", "-sn",
             "-vf", f"select='gt(scene,{scene})',metadata=print:file={scene_txt}",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=timeout)
        if scene_txt.is_file():
            return sorted({round(float(m), 3) for m in re.findall(r"pts_time:([0-9.]+)", scene_txt.read_text())})
    except Exception:
        pass
    finally:
        try:
            scene_txt.unlink()
        except Exception:
            pass
    return []


def _shots_of(cuts_abs, t0, t1, min_shot_s):
    """切点 → 镜头表：首尾补齐后剖段；短于 min_shot_s 的镜并入前一镜（首镜并入后一镜）。"""
    bounds = [t0] + [c for c in cuts_abs if t0 + 0.05 < c < t1 - 0.05] + [t1]
    segs = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    if min_shot_s > 0:
        merged = []
        for s, e in segs:
            if merged and (e - s) < min_shot_s:
                merged[-1] = (merged[-1][0], e)
            else:
                merged.append((s, e))
        if len(merged) > 1 and (merged[0][1] - merged[0][0]) < min_shot_s:
            merged[1] = (merged[0][0], merged[1][1])
            merged.pop(0)
        segs = merged
    return [{"i": i + 1, "start_s": round(s, 2), "end_s": round(e, 2), "dur_s": round(e - s, 2)}
            for i, (s, e) in enumerate(segs)]


def _fnum(b, key, lo, hi, dflt):
    """body 取浮点参数（clamp 到 [lo,hi]，缺/非法用 dflt）。"""
    try:
        v = float(b.get(key))
    except (ValueError, TypeError):
        return dflt
    return max(lo, min(hi, v))


def _auto_shots(exe, src, cuts_rel, t0, t1, min_shot_s, tmp_root, tag, scene, long_shot_s, scene2):
    """切点 → 镜头表；≥long_shot_s 的长镜在镜内用更低阈值 scene2 二级扫描拆细（拆出的镜带 sub:true）。
    返回 (shots, sub_cuts)；sub_cuts 是二级扫描实际用上的内部切点（绝对秒）。
    背景：实测该片 0.35 主阈值对蒙太奇式快切段整段漏检（80.9s「长镜」内实有 18 个切点），
    而 0.15 在长镜内验证为真切点为主——主阈值保持严格、长镜内再敏感扫一遍是折中解。"""
    shots = _shots_of([round(t0 + t, 3) for t in cuts_rel], t0, t1, min_shot_s)
    sub_cuts = []
    if long_shot_s > 0 and 0 < scene2 < scene:
        out = []
        for sh in shots:
            if sh["dur_s"] >= long_shot_s:
                rel2 = _scan_cuts(exe, src,
                                  ["-ss", f"{sh['start_s']:.3f}", "-t", f"{sh['dur_s']:.3f}"],
                                  scene2, tmp_root / f"vs2_{tag}_{sh['i']:03d}.txt")
                inner = [round(sh["start_s"] + t, 3) for t in rel2]
                subs = _shots_of(inner, sh["start_s"], sh["end_s"], min_shot_s)
                if len(subs) > 1:
                    for s2 in subs:
                        s2["sub"] = True
                    sub_cuts.extend(s2["start_s"] for s2 in subs[1:])
                    out.extend(subs)
                    continue
            out.append(sh)
        shots = out
        for i, s in enumerate(shots, 1):
            s["i"] = i
    return shots, sub_cuts


@bp.post("/video-scenes")
def video_scenes():
    """深度拉片 S0：整片（或区间）切点扫描 → 镜头清单（复刻拆解第一步，纯数据不用图）。
    body: {url?|path?, scene=0.35(0.1-0.9), start_s?, end_s?, min_shot_s=0.5(0~5, 合并再短镜头),
           long_shot_s=12(0~120, ≥此秒数的长镜做二级扫描; 0=关), scene2=0.15(0.05-0.9, 二级阈值)}
    长镜二级扫描：0.35 主阈值对快切蒙太奇段会整段漏检（实测 80.9s「长镜」内有 18 个真切点），
    ≥long_shot_s 的镜在镜内用更低阈值再扫一遍，拆出的镜带 "sub":true（供看图时复核，误拆可并在报告里说明）。
    返回 {source, duration_s, start_s, end_s, threshold, cut_count, cuts, sub_count, sub_cuts, shots, stats}"""
    from pathlib import Path as _P
    b = request.get_json(force=True, silent=True) or {}
    scene = _fnum(b, "scene", 0.1, 0.9, 0.35)
    min_shot_s = _fnum(b, "min_shot_s", 0.0, 5.0, 0.5)
    long_shot_s = _fnum(b, "long_shot_s", 0.0, 120.0, 12.0)
    scene2 = _fnum(b, "scene2", 0.05, 0.9, 0.15)
    exe = _ffmpeg_bin()
    if not exe:
        return jsonify({"code": 5001, "msg": "无 ffmpeg：容器镜像自带，宿主 pip 装 imageio-ffmpeg 也有"}), 500
    root = _P(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    tag = _uuid.uuid4().hex[:12]
    try:
        src, source = _resolve_src(b, root, tag)
    except ValueError as e:
        return jsonify({"code": 4001, "msg": str(e)}), 400
    total_d = _ff_duration(exe, str(src))
    start_s, end_s, seg, seg_args = _norm_range(b, total_d)
    cuts_rel = _scan_cuts(exe, src, seg_args, scene, root / f"vs_{tag}_scenes.txt")
    if seg > 0:
        t0, t1 = start_s, start_s + seg
    else:
        t0, t1 = 0.0, (total_d or (max(cuts_rel) + 0.1 if cuts_rel else 1.0))
    cuts_abs = [round(min(max(t0 + t, t0), t1), 3) for t in cuts_rel]
    shots, sub_cuts = _auto_shots(exe, src, cuts_rel, t0, t1, min_shot_s, root, tag, scene, long_shot_s, scene2)
    durs = [s["dur_s"] for s in shots]
    stats = {"count": len(shots),
             "mean_s": round(sum(durs) / len(durs), 2) if durs else 0,
             "min_s": min(durs) if durs else 0, "max_s": max(durs) if durs else 0}
    return ok({"source": source, "duration_s": round(total_d, 1),
               "start_s": round(t0, 2), "end_s": round(t1, 2),
               "threshold": scene, "min_shot_s": min_shot_s,
               "long_shot_s": long_shot_s, "scene2": scene2,
               "cut_count": len(cuts_abs), "cuts": cuts_abs,
               "sub_count": sum(1 for s in shots if s.get("sub")),
               "sub_cuts": [round(c, 3) for c in sub_cuts],
               "shots": shots, "stats": stats})


def _tile_ff(exe, src, t_abs, out_f, tile_w, label, font):
    """抽单帧 → 缩到 tile_w 宽 → 左上角烙上 `#镜号 绝对秒` 标签；失败回退无标签重试。"""
    vf = f"scale={tile_w}:-2"
    if font:
        vf += (f",drawtext=fontfile={font}:text='{label}':fontsize={max(13, tile_w // 18)}"
               f":fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=4:x=6:y=6")
    r = _subprocess.run([exe, "-hide_banner", "-y", "-ss", f"{t_abs:.3f}", "-i", str(src),
                         "-frames:v", "1", "-vf", vf, "-q:v", "4", str(out_f)],
                        capture_output=True, text=True, timeout=60)
    if r.returncode != 0 and font:
        _subprocess.run([exe, "-hide_banner", "-y", "-ss", f"{t_abs:.3f}", "-i", str(src),
                         "-frames:v", "1", "-vf", f"scale={tile_w}:-2", "-q:v", "4", str(out_f)],
                        capture_output=True, text=True, timeout=60)
    return out_f.is_file()


@bp.post("/shots-frames")
def shots_frames():
    """深度拉片 S1/S2：逐镜抽「帧墙」（接触表，格上带 #镜号+时间 标签）——一图看多镜，省读图次数。
    body: {url?|path?, shots?:[{start_s,end_s}]（缺省现场扫切点）, per_shot=3(1-4), tile_w=320(240-640),
           cols=8(4-8), rows=3(1-4), scene=0.35, start_s?, end_s?, min_shot_s=0.5,
           long_shot_s=12, scene2=0.15（长镜二级扫描，同 video-scenes）,
           keep=true（帧文件保留：带 #镜号+时间 标签的缩略图，供报告配图；false=用完即删）}
    返回 {source, duration_s, shot_count, per_shot, keep, shots, sheets, frames:[{shot,time_s,name,url}]}
    帧墙在 uploads（sh_*.jpg），单镜缩略在 frames[]（st_*.jpg）；Agent 用读图工具看 data/uploads/<name>。"""
    from pathlib import Path as _P
    b = request.get_json(force=True, silent=True) or {}

    def _clampf(key, lo, hi, dflt):
        try:
            v = float(b.get(key))
        except (ValueError, TypeError):
            return dflt
        return max(lo, min(hi, v))

    per_shot = int(_clampf("per_shot", 1, 4, 3))
    tile_w = int(_clampf("tile_w", 240, 640, 320))
    cols = int(_clampf("cols", 4, 8, 8))
    rows = int(_clampf("rows", 1, 4, 3))
    scene = _clampf("scene", 0.1, 0.9, 0.35)
    min_shot_s = _clampf("min_shot_s", 0.0, 5.0, 0.5)
    long_shot_s = _fnum(b, "long_shot_s", 0.0, 120.0, 12.0)
    scene2 = _fnum(b, "scene2", 0.05, 0.9, 0.15)
    keep = True if b.get("keep") is None else bool(b.get("keep"))
    exe = _ffmpeg_bin()
    if not exe:
        return jsonify({"code": 5001, "msg": "无 ffmpeg"}), 500
    root = _P(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    tag = _uuid.uuid4().hex[:12]
    try:
        src, source = _resolve_src(b, root, tag)
    except ValueError as e:
        return jsonify({"code": 4001, "msg": str(e)}), 400
    total_d = _ff_duration(exe, str(src))
    start_s, end_s, seg, seg_args = _norm_range(b, total_d)
    # 镜头表：优先用消息给的 shots（关键镜精拆），否则现场扫切点
    raw_shots = b.get("shots")
    if isinstance(raw_shots, list) and raw_shots:
        pairs = []
        for it in raw_shots[:140]:
            try:
                s = max(0.0, float(it.get("start_s")))
                e = float(it.get("end_s"))
            except (AttributeError, ValueError, TypeError):
                continue
            if total_d > 0:
                e = min(e, total_d)
            if e > s + 0.05:
                pairs.append((s, e))
        pairs.sort()
        shots = [{"i": i + 1, "start_s": round(s, 3), "end_s": round(e, 3), "dur_s": round(e - s, 3)}
                 for i, (s, e) in enumerate(pairs)]
    else:
        cuts_rel = _scan_cuts(exe, src, seg_args, scene, root / f"sf_{tag}_scenes.txt")
        if seg > 0:
            t0, t1 = start_s, start_s + seg
        else:
            t0, t1 = 0.0, (total_d or 1.0)
        shots, _sub = _auto_shots(exe, src, cuts_rel, t0, t1, min_shot_s, root, tag, scene, long_shot_s, scene2)
    if not shots:
        return jsonify({"code": 4001, "msg": "没解析出镜头（区间太小或参数不对）"}), 400
    tiles_total = len(shots) * per_shot
    if tiles_total > 336:
        return jsonify({"code": 4001,
                        "msg": "本次要生成 %d 帧（>336 上限）：per_shot 调小、拆两段或先缩素材区间" % tiles_total}), 400
    # 逐镜抽格（带标签）
    font = _FONT_FILE if _P(_FONT_FILE).is_file() else ""
    idx = 0
    tile_files = []
    fail = 0
    for sh in shots:
        s, e, d = sh["start_s"], sh["end_s"], sh["dur_s"]
        if per_shot <= 1:
            ts = [s + d / 2]
        else:
            pad = min(0.08, max(0.0, d * 0.05))
            span = max(0.0, d - 2 * pad)
            ts = [s + pad + span * k / (per_shot - 1) for k in range(per_shot)]
        for t_abs in ts:
            idx += 1
            out_f = root / f"st_{tag}_{idx:04d}.jpg"
            if not _tile_ff(exe, src, t_abs, out_f, tile_w, f"#{sh['i']} {t_abs:.1f}s", font):
                fail += 1
            tile_files.append((out_f, sh["i"], round(t_abs, 2)))
    if fail == len(tile_files) and tile_files:
        return jsonify({"code": 5001, "msg": "抽帧全失败（ffmpeg 异常）"}), 500
    # 拼帧墙：每张 cols×rows 格；尾墙不够就复制最后一格补齐
    sheets = []
    pad_list = []
    per_sheet = cols * rows
    for ci in range(0, len(tile_files), per_sheet):
        chunk = list(tile_files[ci:ci + per_sheet])
        n = len(chunk)
        rows_r = max(1, min(rows, -(-n // cols)))
        need = cols * rows_r
        last = chunk[-1][0]
        for _k in range(n, need):
            p = root / f"st_{tag}_{idx + 1:04d}.jpg"
            try:
                _shutil.copyfile(last, p)
            except Exception:
                break
            idx += 1
            extra = (p, chunk[-1][1], chunk[-1][2])
            chunk.append(extra)
            pad_list.append(extra)
        full = chunk
        sheet_name = f"sh_{tag}_{len(sheets) + 1:02d}.jpg"
        sheet_p = root / sheet_name
        first_no = int(full[0][0].stem.rsplit("_", 1)[1])
        r = _subprocess.run(
            [exe, "-hide_banner", "-y", "-f", "image2", "-start_number", str(first_no),
             "-i", str(root / f"st_{tag}_%04d.jpg"),
             "-vf", f"tile={cols}x{rows_r}:padding=6:color=0x141414",
             "-frames:v", "1", "-q:v", "3", str(sheet_p)],
            capture_output=True, text=True, timeout=120)
        if not sheet_p.is_file():
            return jsonify({"code": 5001, "msg": "帧墙拼接失败: %s" % (r.stderr or "")[-200:]}), 500
        sheets.append({"name": sheet_name, "url": f"/api/images/{sheet_name}", "cols": cols, "rows": rows_r,
                       "tiles": [{"shot": t[1], "time_s": t[2]} for t in full]})
    # 补齐用的重复格一律清掉；真帧默认保留（keep=true）——报告配图直接用这些带标签的缩略图
    for p, _, _ in pad_list:
        try:
            p.unlink()
        except Exception:
            pass
    frames = []
    if keep:
        frames = [{"shot": s, "time_s": t, "name": p.name, "url": f"/api/images/{p.name}"}
                  for p, s, t in tile_files]
    else:
        for p, _, _ in tile_files:
            try:
                p.unlink()
            except Exception:
                pass
    return ok({"source": source, "duration_s": round(total_d, 1),
               "shot_count": len(shots), "per_shot": per_shot, "keep": keep,
               "cols": cols, "rows": rows, "shots": shots, "sheets": sheets,
               "frames": frames})


# ---- H站（hanime1.me）下载入库 ----
# 观片页 <video><source> 直出 1080/720/480 三档 mp4（vdownload.hembed.com + secure token）。
# 部分网络环境该站被墙（宿主裸连 403 / 容器 DNS 污染直连 ENETUNREACH）：
# 容器里配 HANIME_PROXY 走代理（docker-compose 已带默认），留空则直连。
_HANIME_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"}
_HANIME_ID_RE = re.compile(r"^(\d{4,12})$")
_HANIME_URL_RE = re.compile(r"hanime1\.me/watch\?v=(\d{4,12})", re.I)
_HANIME_ALLOW_HOSTS = ("hembed.com", "hanime1.me")


def _hanime_opener():
    pxy = (os.getenv("HANIME_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or "").strip()
    if pxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({"http": pxy, "https": pxy}))
    return urllib.request.build_opener()


def _slugify(s, n=40):
    s = re.sub(r"[^0-9A-Za-z]+", "-", s or "").strip("-")
    return s[:n].strip("-")


@bp.post("/hanime1-fetch")
def hanime1_fetch():
    """H站观片页 → 解析直出 mp4（1080/720/480）→ 下载进 data/uploads；同名已存在直接复用。
    body: {url: "https://hanime1.me/watch?v=408633" 或 "408633", quality?: best|1080p|720p|480p}
    返回（与上传接口同形）：{name, path, url, bytes, duration_s, quality, cached}
    """
    from pathlib import Path as _P
    b = request.get_json(force=True, silent=True) or {}
    raw = (b.get("url") or "").strip()
    want = (b.get("quality") or "best").strip().lower()
    m = _HANIME_URL_RE.search(raw)
    if m:
        vid = m.group(1)
    elif _HANIME_ID_RE.match(raw):
        vid = raw
    else:
        return jsonify({"code": 4001, "msg": "给 hanime1.me 观片页链接，或纯数字视频 id"}), 400
    page_url = "https://hanime1.me/watch?v=%s" % vid
    op = _hanime_opener()
    hdr = dict(_HANIME_UA)
    hdr["Referer"] = "https://hanime1.me/"
    try:
        with op.open(urllib.request.Request(page_url, headers=hdr), timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception as e:
        return jsonify({"code": 5001, "msg": "打不开观片页（视频不存在、被墙或代理未配）：%s" % str(e)[:160]}), 502
    title = ""
    mt = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    if mt:
        title = _html.unescape(mt.group(1))
    else:
        mt = re.search(r"<title>([^<]*)</title>", html)
        if mt:
            title = _html.unescape(mt.group(1))
    title = re.sub(r"\s*[-–—]\s*Hanime1\.me\s*$", "", title, flags=re.I).strip(" -\u00a0")
    opts = []  # [(画质数字, url)]
    for tag in re.findall(r"<source\b[^>]*>", html):
        mu = re.search(r'src="([^"]+\.mp4[^"]*)"', tag)
        mq = re.search(r'size="(\d+)"', tag)
        if mu and mq:
            opts.append((int(mq.group(1)), _html.unescape(mu.group(1))))
    if not opts:  # 兜底：页面任意带 secure 的 mp4 直链（如 <link rel="preload">）
        for u in re.findall(r'https://[^"<>\s]+?\.mp4\?secure=[^"<>\s]+', html):
            u = _html.unescape(u)
            mq = re.search(r"-(\d{3,4})p\.mp4", u)
            opts.append((int(mq.group(1)) if mq else 720, u))
    if not opts:
        return jsonify({"code": 4004, "msg": "页面里没解析到 mp4 直链（视频不存在或页面结构变了）"}), 404
    if want in ("1080p", "720p", "480p"):
        q = int(want[:-1])
        cand = [o for o in opts if o[0] == q] or opts
    else:
        cand = opts
    qual, mp4 = max(cand, key=lambda o: o[0])
    host = (urllib.parse.urlsplit(mp4).hostname or "").lower()
    if not any(host == h or host.endswith("." + h) for h in _HANIME_ALLOW_HOSTS):
        return jsonify({"code": 4003, "msg": "直链域名不在白名单：%s" % host}), 400
    root = _P(__file__).resolve().parents[2] / "data" / "uploads"
    root.mkdir(parents=True, exist_ok=True)
    slug = _slugify(title)
    fname = "hanime1-%s%s-%dp.mp4" % (vid, ("-" + slug) if slug else "", qual)
    dest = root / fname
    cached = dest.is_file() and dest.stat().st_size > 0
    if not cached:
        try:
            with op.open(urllib.request.Request(mp4, headers=hdr), timeout=60) as r, open(dest, "wb") as f:
                limit = _MAX_VIDEO_BYTES
                total = int(r.headers.get("Content-Length") or 0)
                if total and total > limit:
                    raise ValueError("视频超过 %dMB 上限" % (limit // 1024 // 1024))
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    limit -= len(chunk)
                    if limit < 0:
                        raise ValueError("视频超过 %dMB 上限" % (_MAX_VIDEO_BYTES // 1024 // 1024))
                    f.write(chunk)
                if f.tell() == 0:
                    raise ValueError("下载到 0 字节")
        except Exception as e:
            try:
                dest.unlink()
            except Exception:
                pass
            return jsonify({"code": 5001, "msg": "视频下载失败：%s" % str(e)[:160]}), 502
    size = dest.stat().st_size
    dur = 0.0
    exe = _ffmpeg_bin()
    if exe:
        dur = _ff_duration(exe, str(dest))
    return ok({"name": fname, "path": fname, "url": "/api/images/%s" % urllib.parse.quote(fname),
               "bytes": size, "duration_s": round(dur, 2), "quality": "%dp" % qual, "cached": cached})
