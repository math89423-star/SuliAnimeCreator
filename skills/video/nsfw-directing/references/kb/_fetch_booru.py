#!/usr/bin/env python3
"""booru KB 抓取器 v2（宿主侧跑，走宿主代理——容器直连 danbooru 不可达）。

两段式（可断点续跑，缓存落 _cache/）：
  python3 _fetch_booru.py expand            # 共现展开 → _candidates.json（快，1 请求/seed）
  python3 _fetch_booru.py fetch [--limit N] # 取 wiki（定义+别名）→ _raw.json / _raw.md（带缓存，可续跑）

数据源（公开 wiki，只取定义与别名）：
  related_tag.json?query=<tag>   → 共现 tag +（自带）热度与分类
  wiki_pages/<tag>.json          → body(定义) + other_names(含中文/日文别名)
  tags.json?search[name_matches]=<tag> → seed 自身的 canonical 热度
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
BASE = "https://danbooru.donmai.us"
PROXY = os.getenv("BOORU_PROXY") or "http://172.31.160.1:7897"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
UA = {"User-Agent": "SuliKB/0.2 (+local craft knowledge base)", "Accept": "application/json"}   # 实测：浏览器伪装 UA 被 danbooru WAF 403，诚实 UA 200
REL_MIN = float(os.getenv("KB_REL_MIN") or 0.18)   # 共现阈值
POSTS_MIN = int(os.getenv("KB_POSTS_MIN") or 5000)  # 热度下限（过滤冷门/生僻）


def get_json(url, tries=3, timeout=25):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with OPENER.open(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(5.0 * (i + 1) if e.code == 429 else 2.0 * (i + 1))
        except Exception:
            time.sleep(2.0 * (i + 1))
    return None


def cached(key, fn):
    """带缓存；**失败（None/空）不落缓存**，下次重试。"""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (key.replace("/", "_") + ".json")
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    v = fn()
    empty = v is None or (isinstance(v, (dict, list)) and len(v) == 0)
    if not empty:
        p.write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8")
    return v


def load_seeds():
    seeds, cur = [], "未分类"
    f = HERE / "seeds.txt"
    for line in f.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            cur = s.lstrip("# ").strip()
        else:
            seeds.append({"tag": s, "section": cur})
    return seeds


def cmd_expand():
    seeds = load_seeds()
    cand = {}
    for i, sd in enumerate(seeds, 1):
        tag = sd["tag"]
        cand.setdefault(tag, {"sections": set(), "co": 1.0, "posts": None, "cat": 0})
        cand[tag]["sections"].add(sd["section"])
        rel = cached("rel_" + tag, lambda t=tag: get_json(
            "%s/related_tag.json?query=%s&limit=50" % (BASE, urllib.parse.quote(t))) or {})
        time.sleep(1.2)   # 节流：无节制连发会被 danbooru 限流
        for t in (rel or {}).get("related_tags") or []:
            tg = t.get("tag") or {}
            n, co, cat, posts = tg.get("name"), t.get("frequency"), tg.get("category"), tg.get("post_count")
            if not n or cat != 0 or (co or 0) < REL_MIN or (posts or 0) < POSTS_MIN:
                continue
            e = cand.setdefault(n, {"sections": set(), "co": 0.0, "posts": posts, "cat": cat})
            e["co"] = max(e["co"], co or 0)
            e["posts"] = max(e["posts"] or 0, posts or 0)
            e["sections"].add(sd["section"])
        if i % 10 == 0:
            print("  expand %d/%d → 候选 %d" % (i, len(seeds), len(cand)), flush=True)
    out = [{"tag": k, "sections": sorted(v["sections"]), "co": round(v["co"], 3),
            "posts": v["posts"], "cat": v["cat"]} for k, v in cand.items()]
    out.sort(key=lambda x: -(x["posts"] or 0))
    (HERE / "_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("候选 %d 条 → _candidates.json" % len(out), flush=True)


def cmd_fetch():
    limit = 999
    args = sys.argv
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    cands = json.loads((HERE / "_candidates.json").read_text(encoding="utf-8"))[:limit]
    # seed 自身补热度（共现表通常也含 seed）
    out = []
    for i, c in enumerate(cands, 1):
        tag = c["tag"]
        w = cached("wiki_" + tag, lambda t=tag: get_json(
            "%s/wiki_pages/%s.json" % (BASE, urllib.parse.quote(t))))
        time.sleep(1.0)
        out.append({**c,
                    "other_names": (w or {}).get("other_names") or [],
                    "body": ((w or {}).get("body") or "").strip()})
        if i % 25 == 0:
            print("  fetch %d/%d" % (i, len(cands)), flush=True)
            (HERE / "_raw.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "_raw.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # 速览表
    lines = ["# booru 原始抓取速览（%d 条，按热度降序）\n" % len(out),
             "| tag | posts | 共现 | 归类 | 中文/日文别名 | 定义（英文原文前 200 字） |", "|---|---|---|---|---|---|"]
    for x in sorted(out, key=lambda y: -(y.get("posts") or 0)):
        d = " ".join((x.get("body") or "").split())[:200].replace("|", "/")
        cn = "/".join([n for n in (x.get("other_names") or [])
                       if any("\u4e00" <= ch <= "\u9fff" for ch in n)]) or ""
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (
            x["tag"], x.get("posts"), x.get("co"), ",".join(x.get("sections") or []), cn, d))
    (HERE / "_raw.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("写出 _raw.json / _raw.md（%d 条）" % len(out), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "expand"
    if cmd == "expand":
        cmd_expand()
    elif cmd == "fetch":
        cmd_fetch()
    else:
        print(__doc__)
