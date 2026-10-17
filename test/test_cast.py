"""角色库化回归（2026-10-16）：出镜人名必须来自取角链，不许再出现写死的演示名。

跑法：`python -m pytest test/test_cast.py -q`（纯标准库，不需要后端在跑）。
把 backend/app 拷到 tmp 后再 import，任何 backend/ 目录权限/包结构都不影响本测试。
"""
import os
import shutil
import sys
import tempfile
import time

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_SRC = os.path.join(REPO, "backend", "app")

# 仓库里不再允许出现的写死人名（生产代码里一个都不许留）
BANNED = ("星璃", "陆见川", "沈禾", "蒋姨")
# 允许的占位说话人
PLACEHOLDERS = ("主角", "对手")
# 检查范围：真的会进生成链的代码（legacySeeds.ts 只做一次性清理，不算）
SCAN_DIRS = (os.path.join("backend", "app"), os.path.join("frontend", "src"))
SCAN_EXT = (".py", ".vue", ".ts", ".js")
SKIP_FILES = (os.path.join("frontend", "src", "utils", "legacySeeds.ts"),)

_TMP = None
_MODS = None


def _svc():
    """把 backend/app 拷到临时目录后 import，返回 (draft, cast, llm_opencode)。"""
    global _TMP, _MODS
    if _MODS is None:
        # 目录名带源码指纹：改了 backend/app 不会读到上一次的旧副本
        stamp = str(os.path.getmtime(APP_SRC))
        for root, _dirs, files in os.walk(APP_SRC):
            for fn in files:
                if fn.endswith(".py"):
                    stamp = "%s_%d" % (stamp, int(os.path.getmtime(os.path.join(root, fn)) * 1000))
        _TMP = tempfile.mkdtemp(prefix="suli_cast_ut_%d_" % (abs(hash(stamp)) % 100000))
        shutil.copytree(APP_SRC, os.path.join(_TMP, "app"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        sys.path.insert(0, _TMP)
        from app.services import cast as cast_mod  # noqa: E402
        from app.services import draft as draft_mod  # noqa: E402
        from app.services import llm_opencode  # noqa: E402
        _MODS = (draft_mod, cast_mod, llm_opencode)
    return _MODS


def _names(md):
    """正文里的说话人（`角色：台词`），供断言用。"""
    return _svc()[1].speaker_names(md, 12)


def _stub_llm(monkeypatch, reply=""):
    """把 LLM 网关换成假实现：既能保证走模板回退，又能截获 prompt 本体。"""
    _, _, llm = _svc()
    seen = {"prompt": ""}

    def fake_cfg():
        return {"provider": "opencode", "base": "http://stub", "key": "stub", "model": "stub-model"}

    def fake_post(base, key, model_id, prompt, timeout=60, effort=""):
        seen["prompt"] = prompt
        return reply

    monkeypatch.setattr(llm, "llm_cfg", fake_cfg)
    monkeypatch.setattr(llm, "_post", fake_post)
    return seen


def test_no_hardcoded_names_in_sources():
    """静态检查：生产代码里不再写死演示人名（前端默认值也要干净）。"""
    hits = []
    for sub in SCAN_DIRS:
        root_dir = os.path.join(REPO, sub)
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", "dist")]
            for fn in files:
                if not fn.endswith(SCAN_EXT):
                    continue
                path = os.path.join(root, fn)
                rel = os.path.relpath(path, REPO)
                if rel in SKIP_FILES:
                    continue
                try:
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                except Exception:
                    continue
                for name in BANNED:
                    if name in text:
                        hits.append("%s: %s" % (rel, name))
    assert not hits, "仍写死的演示人名：%s" % "; ".join(hits)


def test_frontend_defaults_are_empty():
    """前端两处默认值必须空着：角色名输入框、剧本底稿。"""
    for rel, needle in ((os.path.join("frontend", "src", "views", "CharacterView.vue"), "const cname = ref('')"),
                        (os.path.join("frontend", "src", "views", "ScriptboardView.vue"), "const script = ref('')")):
        with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
            assert needle in fh.read(), "%s 里没找到空默认值：%s" % (rel, needle)
    with open(os.path.join(REPO, "frontend", "src", "views", "StoryView.vue"), encoding="utf-8") as fh:
        assert "localStorage.getItem(DRAFT_KEY) || ''" in fh.read(), "StoryView 提示词默认值没清空"


def test_resolve_cast_priority():
    """取角顺序：显式点名 → 本集正文说话人 → 角色库 → 占位。"""
    _, cast_mod, _ = _svc()
    C = cast_mod.resolve_cast(["甲", "乙"], "丙：你好。")
    assert C["names"] == ["甲", "乙"] and C["anchored"] and C["source"] == "explicit"
    assert [c["source"] for c in C["cast"]] == ["explicit", "explicit"]

    C = cast_mod.resolve_cast(None, "丙：你好。\n丁：在。")
    assert C["names"] == ["丙", "丁"] and C["source"] == "script"

    C = cast_mod.resolve_cast(None, "")
    allowed = set(PLACEHOLDERS) | set(cast_mod.db_names())
    assert set(C["names"]) <= allowed and not any(n in BANNED for n in C["names"])

    C = cast_mod.resolve_cast(["独"])        # 只有一个人时补占位，避免无对白
    assert len(C["names"]) == 2 and C["names"][0] == "独"


def test_speaker_names_skips_titles_and_tags():
    """标题行与 [SFX]/[VO] 这类标签行不算说话人。"""
    _, cast_mod, _ = _svc()
    md = "# EP-X 标题\n## EP-X-SC001 内·主场景·夜\n[SFX] 铁门低鸣\n[VO] 少年：这句是旁白。\n女主：取衣牌呢？\n"
    names = cast_mod.speaker_names(md)
    assert names == ["女主"], names


def test_speaker_names_canonicalizes_notes():
    """说话人带状态注解 / 括号没关全时，只认本名，别把半句台词当人名。"""
    _, cast_mod, _ = _svc()
    md = ("女主（按住他的手腕）：别松。\n"
          "女主：看着我的手。\n"
          "字幕：她走近柜台，摊开掌心（字幕不是说话人）\n"
          "配角（把平板翻过来，屏幕是一张扫描件）：承接书。\n"
          "[OS] 配角（在门外）：还有六个小时。\n"
          "<!-- 本集契约：点题登场 -->\n")
    assert cast_mod.speaker_names(md) == ["女主", "配角"], cast_mod.speaker_names(md)


def test_screenplay_template_uses_cast_only(monkeypatch):
    """模板链：给了 cast 就用 cast，没给就占位，绝不吐演示名。"""
    draft, cast_mod, _ = _svc()
    _stub_llm(monkeypatch)
    md, engine = draft.build_screenplay_md("测试想法", "测试方向", ["起", "转", "落"], 20,
                                           "EP-CAST-T1", cast=["甲", "乙"])
    assert engine == "template"
    assert _names(md) == ["甲", "乙"], _names(md)
    assert not any(n in md for n in BANNED)

    md2, _ = draft.build_screenplay_md("测试想法", "测试方向", ["起", "转", "落"], 20, "EP-CAST-T2")
    who = _names(md2)
    assert who and set(who) <= set(PLACEHOLDERS) | set(cast_mod.db_names()), who
    assert not any(n in md2 for n in BANNED)

    md3 = draft.pick_to_screenplay_md({"logline": "方向X", "beats": ["起", "转"]}, "EP-CAST-T3")
    assert _names(md3) == ["主角", "对手"], _names(md3)
    assert "cast:主角/对手" in md3


def test_llm_prompt_names_the_cast(monkeypatch):
    """LLM 路径：prompt 里点名的是本次 cast，不再写死两人。"""
    draft, _, _ = _svc()
    seen = _stub_llm(monkeypatch, reply="")          # 空回复 -> 走模板，但 prompt 已截获
    draft.build_screenplay_md("想法", "方向", ["起"], 20, "EP-CAST-T5", cast=["甲", "乙"])
    assert "甲" in seen["prompt"] and "乙" in seen["prompt"]
    assert not any(n in seen["prompt"] for n in BANNED)

    draft.build_screenplay_md("想法", "方向", ["起"], 20, "EP-CAST-T6")
    assert "别自造人名" in seen["prompt"]
    assert not any(n in seen["prompt"] for n in BANNED)


def test_outline_template_carries_cast(monkeypatch):
    draft, _, _ = _svc()
    _stub_llm(monkeypatch)
    md, engine = draft.build_outline_md("EP-CAST-T4", 15, "pixai", "", "背景一句", "",
                                        cast=["甲", "乙"])
    assert engine == "template"
    assert "出镜：甲、乙" in md
    assert not any(n in md for n in BANNED)

    seen = _stub_llm(monkeypatch)
    draft.build_outline_md("EP-CAST-T4", 15, "pixai", "", "背景一句", "", cast=["甲", "乙"])
    assert "甲" in seen["prompt"] and "别换成别的人名" in seen["prompt"]
    assert not any(n in seen["prompt"] for n in BANNED)


@pytest.mark.skipif(not os.getenv("Suli_BASE", ""), reason="需要后端：Suli_BASE=... 才跑 HTTP 用例")
def test_cast_api_roundtrip():
    """HTTP：点名 → 生成大纲 → 取角能读到，并且换点名能覆盖。"""
    import json
    import urllib.request

    base = os.getenv("Suli_BASE", "http://127.0.0.1:5001").rstrip("/")
    eid = "EP-CAST-UT%d" % (int(time.time()) % 100000)

    def req(method, path, body=None):
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        r = urllib.request.Request(base + path, data=data, method=method,
                                   headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(r, timeout=90) as resp:
            return json.loads(resp.read().decode())

    assert req("PUT", "/api/v1/scriptboard/cast/%s" % eid, {"names": ["甲", "乙"]})["data"]["names"] == ["甲", "乙"]
    got = req("POST", "/api/v1/scriptboard/outline/generate/%s" % eid,
              {"total_s": 15, "engine": "pixai", "hint": "一句背景"})["data"]
    assert "乙" in got["outline_md"]
    assert not any(n in got["outline_md"] for n in BANNED)
    assert req("PUT", "/api/v1/scriptboard/cast/%s" % eid, {"names": ["丙"]})["data"]["names"][0] == "丙"
