"""漫画页序列（art 域）：建页 → 页条 → 挂成图 → 前页续接 → 直投带页上下文。

约定（见 conftest）：写操作只造带随机后缀的临时集/临时方案，结束即清理，不碰现成集。
"""
import json
import pathlib
import shutil
import subprocess
import urllib.request
import uuid

from conftest import req

BASE = "http://127.0.0.1:5001"

INBOX = pathlib.Path("/home/administrator/L-Port-Comfy/app/backend/data/libraries/投流素材库/suli_packages")
UPLOADS = pathlib.Path("/home/administrator/SuliAnimeCreator/backend/data/uploads")


def _data(method, path, body=None, query=None, timeout=120):
    st, d = req(method, path, body=body, query=query, timeout=timeout)
    assert st == 200, f"{method} {path} http={st} {str(d)[:300]}"
    assert d.get("code") == 0, f"{method} {path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]


def _suffix():
    return uuid.uuid4().hex[:6].upper()


def _rm_push_dir(pkg):
    """收件箱是后端容器（root）写的，宿主直接删会权限不足：优先走容器内删。"""
    try:
        r = subprocess.run(["docker", "exec", "sulianimecreator-backend-1",
                            "rm", "-rf", f"/lport-lib/suli_packages/{pkg}"],
                           capture_output=True, timeout=30)
        if r.returncode == 0:
            return
    except Exception:
        pass
    shutil.rmtree(INBOX / pkg, ignore_errors=True)


def test_comic_pages_flow():
    suffix = _suffix()
    eid = f"EP-COMIC-{suffix}"
    outline = "# 方案大纲\n\n## 方向一句话\n雨夜便利店，白发少女推门进店。\n"
    pid = None
    plan_ids = []
    pushed_pkg = None
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"漫画自检-{suffix}"})
        pid = proj["id"]
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "漫画自检集"})
        _data("PUT", f"/api/v1/scriptboard/outline/{eid}", {"outline_md": outline})

        # ① 建第 1 页（带页上下文：大纲快照）
        p1 = _data("POST", "/api/v1/art/plans", {
            "title": f"{eid} 第1页 第1格", "intent_text": "少女推门进店", "engines": ["novelai"],
            "ref_images": [], "note": "", "source": "ui",
            "page": {"episode_id": eid, "index": 1, "panel_index": 1, "prev_plan_id": "",
                     "outline_text": outline, "image": None},
        })
        plan_ids.append(p1["id"])
        assert p1["page"]["episode_id"] == eid
        assert p1["page"]["index"] == 1
        assert p1["page"]["panel_index"] == 1
        assert p1["page"]["outline_text"] == outline

        # ② 格序列按页序+格序返回这一集的全部格
        rows = _data("GET", "/api/v1/art/comics", query={"episode_id": eid})
        assert [r["id"] for r in rows] == [p1["id"]], rows
        assert rows[0]["page"]["index"] == 1 and rows[0]["page"]["panel_index"] == 1

        # ③ 挂本页成图 → 写进 page.image（multipart，conftest 的 req 只发 JSON，这里直接打 urllib）
        img = UPLOADS / "c59dfe6a3b75426a9f0131d1e445b91a.png"
        assert img.is_file(), "缺基准图 %s" % img
        with open(img, "rb") as fh:
            body = (b"--BOUND\r\nContent-Disposition: form-data; name=\"file\"; filename=\"p1.png\"\r\n"
                    b"Content-Type: image/png\r\n\r\n" + fh.read() + b"\r\n--BOUND--\r\n")
            r = urllib.request.Request(
                f"{BASE}/api/v1/art/plans/{p1['id']}/image",
                data=body, headers={"Content-Type": "multipart/form-data; boundary=BOUND"}, method="POST")
            with urllib.request.urlopen(r, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        assert payload.get("code") == 0, payload
        got = _data("GET", f"/api/v1/art/plans/{p1['id']}")
        assert got["page"]["image"], "成图没挂上"
        assert got["page"]["image"]["name"].endswith(".png")

        # ④ 第 2 页第 1 格：prev 指上一页的末格，参考图带上一页末格成图
        p2 = _data("POST", "/api/v1/art/plans", {
            "title": f"{eid} 第2页 第1格", "intent_text": "她拿起汽水", "engines": ["novelai"],
            "ref_images": [got["page"]["image"]], "note": "", "source": "ui",
            "page": {"episode_id": eid, "index": 2, "panel_index": 1, "prev_plan_id": p1["id"],
                     "outline_text": outline, "image": None},
        })
        plan_ids.append(p2["id"])
        assert p2["page"]["prev_plan_id"] == p1["id"]
        assert p2["page"]["panel_index"] == 1
        assert p2["ref_images"] and p2["ref_images"][0]["name"] == got["page"]["image"]["name"]

        # ④b 页内第 2 格：prev 指同页第 1 格
        p3 = _data("POST", "/api/v1/art/plans", {
            "title": f"{eid} 第2页 第2格", "intent_text": "瓶身水珠特写", "engines": ["novelai"],
            "ref_images": [], "note": "", "source": "ui",
            "page": {"episode_id": eid, "index": 2, "panel_index": 2, "prev_plan_id": p2["id"],
                     "outline_text": outline, "image": None},
        })
        plan_ids.append(p3["id"])
        assert p3["page"]["panel_index"] == 2
        assert p3["page"]["prev_plan_id"] == p2["id"]

        rows = _data("GET", "/api/v1/art/comics", query={"episode_id": eid})
        assert [(r["page"]["index"], r["page"]["panel_index"]) for r in rows] == [(1, 1), (2, 1), (2, 2)], rows

        # ⑤ 直投：包里的 intent_text 必带页上下文（集号/页/格/大纲），参考图随包走
        pushed = _data("POST", "/api/v1/art/push-lport", {"plan_id": p2["id"]})
        pushed_pkg = pushed["package_id"]
        pkg_dir = INBOX / pushed_pkg
        assert pkg_dir.is_dir(), f"收件箱缺目录 {pkg_dir}"
        art_plan = json.loads((pkg_dir / "art_plan.json").read_text(encoding="utf-8"))
        assert eid in art_plan["intent_text"], art_plan["intent_text"]
        assert "第 2 页" in art_plan["intent_text"] and "第 1 格" in art_plan["intent_text"], art_plan["intent_text"]
        assert "雨夜便利店" in art_plan["intent_text"], art_plan["intent_text"]
        assert art_plan["reference_images"], art_plan
        assert art_plan["comic_context"]["episode_id"] == eid
        assert art_plan["comic_context"]["index"] == 2
        assert art_plan["comic_context"]["panel_index"] == 1

        # ⑤b 页内第 2 格的上下文：页序/格序/上一格
        got3 = _data("GET", f"/api/v1/art/plans/{p3['id']}")
        assert got3["page"]["index"] == 2 and got3["page"]["panel_index"] == 2
        assert got3["page"]["prev_plan_id"] == p2["id"]

        # ⑥ 撤成图
        _data("DELETE", f"/api/v1/art/plans/{p1['id']}/image")
        got2 = _data("GET", f"/api/v1/art/plans/{p1['id']}")
        assert not got2["page"]["image"]
    finally:
        if pushed_pkg:
            _rm_push_dir(pushed_pkg)
        for x in plan_ids:
            try:
                req("DELETE", f"/api/v1/art/plans/{x}", timeout=30)
            except Exception:
                pass
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_plan_tier_diff_snapshot():
    """agent 改水位：后端留改前快照（prev）里要有水位/衣物档，前端才比得出 diff 行。"""
    suffix = _suffix()
    pid = None
    plan_id = ""
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"水位diff自检-{suffix}"})
        pid = proj["id"]
        plan = _data("POST", "/api/v1/art/plans", {
            "title": "水位diff用例", "intent_text": "少女推门", "engines": ["novelai"],
            "tier": "tease", "clothing_level": "L0", "source": "ui",
        })
        plan_id = plan["id"]
        assert plan["tier"] == "tease" and plan["clothing_level"] == "L0"

        # agent 写盘（source != ui）：留改前快照
        _data("POST", "/api/v1/art/plans", {
            "id": plan_id, "title": "水位diff用例", "intent_text": "少女推门",
            "engines": ["novelai"], "tier": "explicit", "clothing_level": "L2",
            "source": "agent",
        })
        got = _data("GET", f"/api/v1/art/plans/{plan_id}")
        assert got["tier"] == "explicit" and got["clothing_level"] == "L2"
        prev = got.get("prev") or {}
        assert prev.get("tier") == "tease", prev
        assert prev.get("clothing_level") == "L0", prev

        # 页面自己改的：快照清掉（人已经看过了）
        _data("POST", "/api/v1/art/plans", {
            "id": plan_id, "title": "水位diff用例", "intent_text": "少女推门",
            "engines": ["novelai"], "tier": "undress", "clothing_level": "L1",
            "source": "ui",
        })
        got2 = _data("GET", f"/api/v1/art/plans/{plan_id}")
        assert not got2.get("prev"), got2.get("prev")
    finally:
        if plan_id:
            try:
                req("DELETE", f"/api/v1/art/plans/{plan_id}", timeout=30)
            except Exception:
                pass
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_comic_tier_and_plan_import():
    """水位档：剧本元信息 + 每格 tier/clothing → 拆格带进方案 → 直投包带 tier/comic 段。

    另测 L-Port 整页分镜回传（comic_page_diverge 的 panel_plan）落成剧本表。
    """
    suffix = _suffix()
    eid = f"EP-TIER-{suffix}"
    pid = None
    plan_ids = []
    pkgs = []
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"档位自检-{suffix}"})
        pid = proj["id"]
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "档位自检集"})

        # ① 存剧本：元信息 + 每格档位
        _data("POST", "/api/v1/art/comic-script", {
            "episode_id": eid,
            "premise": "深夜归巢",
            "characters": "成年女性 A：浅蓝及腰长发、黑弯角",
            "style_hint": "写实电影感，暖色台灯",
            "tier": "tease",
            "panels": [
                {"page": 1, "panel": 1, "text": "第一格：推门", "dialogue": "", "camera": "全景",
                 "tier": "tease", "clothing_level": "L0"},
                {"page": 1, "panel": 2, "text": "第二格：坐在床沿", "dialogue": "……先别开灯。",
                 "camera": "近景", "tier": "explicit", "clothing_level": "L2"},
            ],
        })
        sc = _data("GET", "/api/v1/art/comic-script", query={"episode_id": eid})
        assert sc["premise"] == "深夜归巢"
        assert sc["style_hint"] == "写实电影感，暖色台灯"
        assert sc["tier"] == "tease"
        assert sc["panels"][0]["tier"] == "tease" and sc["panels"][0]["clothing_level"] == "L0"
        assert sc["panels"][1]["tier"] == "explicit" and sc["panels"][1]["clothing_level"] == "L2"

        # ② 拆格：档位进方案，意图里带水位
        sp = _data("POST", "/api/v1/art/comic-script/split", {"episode_id": eid, "engines": ["novelai"]})
        assert sp["created"] == 2, sp
        plan_ids.extend(sp["plan_ids"])
        rows = _data("GET", "/api/v1/art/comics", query={"episode_id": eid})
        assert [r["tier"] for r in rows] == ["tease", "explicit"], rows
        assert [r["clothing_level"] for r in rows] == ["L0", "L2"], rows
        assert "【本图水位】explicit" in rows[1]["intent_text"], rows[1]["intent_text"]
        assert "【衣物档】L2" in rows[1]["intent_text"], rows[1]["intent_text"]

        # ③ 直投：包里有 tier / clothing / comic 段，水位写进意图与页上下文
        pushed = _data("POST", "/api/v1/art/push-lport", {"plan_id": sp["plan_ids"][1]})
        pkgs.append(pushed["package_id"])
        pkg_dir = INBOX / pushed["package_id"]
        art_plan = json.loads((pkg_dir / "art_plan.json").read_text(encoding="utf-8"))
        assert art_plan["tier"] == "explicit", art_plan["tier"]
        assert art_plan["clothing_level"] == "L2", art_plan["clothing_level"]
        assert art_plan["comic"]["tier"] == "explicit", art_plan["comic"]
        assert art_plan["comic"]["premise"] == "深夜归巢", art_plan["comic"]
        assert art_plan["comic"]["style_hint"] == "写实电影感，暖色台灯", art_plan["comic"]
        assert "本格水位：explicit" in art_plan["intent_text"], art_plan["intent_text"]

        # ④ L-Port 整页分镜回传 → 落成剧本表（字段映射：narrative/action/tier/clothing_level）
        plan = {"title": "深夜归巢", "style_base": "细线勾轮廓，暖橙冷蓝两极",
                "characters": [{"id": "A", "desc": "成年女性", "anchor": "浅蓝长发"}],
                "pages": [{"page": 1, "layout": "stack_4", "panels": [
                    {"index": 1, "panel_type": "establishing", "shot": "全景", "camera": "平视",
                     "action": "她反手压下门锁", "dialogue": "", "sfx": "咔哒",
                     "tier": "tease", "clothing_level": "L0",
                     "continuity": "起始格：衣物完整，赤脚",
                     "light": "床头灯从右侧打来", "narrative": "成年女性 A 站在门内，浅蓝长发。"},
                    {"index": 2, "panel_type": "emotional", "shot": "近景", "camera": "侧 3/4",
                     "action": "她坐在床沿，手停在领口", "dialogue": "……先别开灯。", "sfx": "",
                     "tier": "explicit", "clothing_level": "L2",
                     "continuity": "上衣半褪，被单堆在腿侧",
                     "light": "暖硬光打亮锁骨", "narrative": "成年女性 A 坐在床沿，长发垂到胸前。"},
                ]}]}
        r = _data("POST", "/api/v1/art/comic-plan/import", {"episode_id": eid, "panel_plan": plan})
        assert r["panel_count"] == 2, r
        sc2 = _data("GET", "/api/v1/art/comic-script", query={"episode_id": eid})
        assert sc2["title"] == "深夜归巢", sc2["title"]
        assert sc2["style_hint"] == "细线勾轮廓，暖橙冷蓝两极", sc2["style_hint"]
        assert "浅蓝长发" in sc2["characters"], sc2["characters"]
        assert sc2["panels"][0]["tier"] == "tease" and sc2["panels"][0]["clothing_level"] == "L0"
        assert sc2["panels"][1]["tier"] == "explicit" and sc2["panels"][1]["clothing_level"] == "L2"
        assert sc2["panels"][1]["dialogue"] == "……先别开灯。"
        assert "全景" in sc2["panels"][0]["camera"] and "平视" in sc2["panels"][0]["camera"]
        assert "反手压下门锁" in sc2["panels"][0]["note"]
        assert "咔哒" in sc2["panels"][0]["note"]

        # ⑤ 再拆格：已存在的格按新剧本刷新（仅未投递的），已投递的不动
        sp2 = _data("POST", "/api/v1/art/comic-script/split", {"episode_id": eid})
        assert sp2["created"] == 0, sp2
        assert sp2["refreshed"] == 1, sp2      # 第2格已投递（直投过），不刷
        rows2 = _data("GET", "/api/v1/art/comics", query={"episode_id": eid})
        assert [r["tier"] for r in rows2] == ["tease", "explicit"], rows2
    finally:
        for pkg in pkgs:
            _rm_push_dir(pkg)
        for x in plan_ids:
            try:
                req("DELETE", f"/api/v1/art/plans/{x}", timeout=30)
            except Exception:
                pass
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_comic_push_inherits_prev_panel_image():
    """拆格建出来的格不带上一格成图（拆格时还没出图）—— 直投那一刻必须接上。

    衔接只能发生在直投：拆格 → 第1格出图 → 第2格直投，包里必须有第1格成图。
    """
    suffix = _suffix()
    eid = f"EP-LINK-{suffix}"
    pid = None
    plan_ids = []
    pkgs = []
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"衔接自检-{suffix}"})
        pid = proj["id"]
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "衔接自检集"})

        _data("POST", "/api/v1/art/comic-script", {
            "episode_id": eid,
            "panels": [
                {"page": 1, "panel": 1, "text": "少女推门", "dialogue": "", "camera": "中景"},
                {"page": 1, "panel": 2, "text": "她回头看货架", "dialogue": "", "camera": "近景"},
            ],
        })
        sp = _data("POST", "/api/v1/art/comic-script/split", {"episode_id": eid, "engines": ["novelai"]})
        assert sp["created"] == 2, sp
        plan_ids.extend(sp["plan_ids"])
        p1, p2 = sp["plan_ids"]

        # 第 1 格挂成图
        img = UPLOADS / "c59dfe6a3b75426a9f0131d1e445b91a.png"
        assert img.is_file(), "缺基准图 %s" % img
        with open(img, "rb") as fh:
            body = (b"--BOUND\r\nContent-Disposition: form-data; name=\"file\"; filename=\"p1.png\"\r\n"
                    b"Content-Type: image/png\r\n\r\n" + fh.read() + b"\r\n--BOUND--\r\n")
            r = urllib.request.Request(
                f"{BASE}/api/v1/art/plans/{p1}/image",
                data=body, headers={"Content-Type": "multipart/form-data; boundary=BOUND"}, method="POST")
            with urllib.request.urlopen(r, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        assert payload.get("code") == 0, payload
        up_name = payload["data"]["image"]["name"]

        # 第 2 格自带参考图是空的（拆格时第 1 格还没出图）
        d2 = _data("GET", f"/api/v1/art/plans/{p2}")
        assert not d2.get("ref_images"), d2.get("ref_images")

        # 直投第 2 格：自动接上第 1 格成图，且物理进 zip
        pushed = _data("POST", "/api/v1/art/push-lport", {"plan_id": p2})
        pkgs.append(pushed["package_id"])
        assert pushed["ref_from"] == "prev_panel", pushed
        assert pushed["ref_count"] == 1, pushed
        pkg_dir = INBOX / pushed["package_id"]
        art_plan = json.loads((pkg_dir / "art_plan.json").read_text(encoding="utf-8"))
        assert art_plan["reference_images"] == [up_name], art_plan["reference_images"]
        import zipfile
        zf = zipfile.ZipFile(pkg_dir / (pushed["package_id"] + ".zip"))
        assert "ref_images/%s" % up_name in zf.namelist(), zf.namelist()

        # 第 1 格没有上一格：不该硬塞参考图
        pushed1 = _data("POST", "/api/v1/art/push-lport", {"plan_id": p1})
        pkgs.append(pushed1["package_id"])
        assert pushed1["ref_count"] == 0, pushed1
        assert pushed1["ref_from"] == "plan", pushed1
    finally:
        for pkg in pkgs:
            _rm_push_dir(pkg)
        for x in plan_ids:
            try:
                req("DELETE", f"/api/v1/art/plans/{x}", timeout=30)
            except Exception:
                pass
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_comics_endpoint_validation():
    # 不存在的集号：返回空列表，不报错
    rows = _data("GET", "/api/v1/art/comics", query={"episode_id": "EP-NOPE-XYZ"})
    assert rows == [], rows


def test_comic_script_split_flow():
    """正确顺序：大纲 → 剧本 → 拆格 → 方案（每格一个，带页/格/上一格链）。"""
    suffix = _suffix()
    eid = f"EP-SCRIPT-{suffix}"
    outline = (
        "# 方案大纲\n\n## 方向一句话\n雨夜便利店。\n\n"
        "## 分镜大纲\n"
        "| 镜号 | 内容 | 时长 | 运镜 | 备注 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | 少女推门进店 | 4s | 推 | 冷暖对撞 |\n"
        "| 2 | 她拿起汽水 | 3s | 固定 | 道具锚点 |\n"
    )
    pid = None
    plan_ids = []
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"剧本自检-{suffix}"})
        pid = proj["id"]
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "剧本自检集"})
        _data("PUT", f"/api/v1/scriptboard/outline/{eid}", {"outline_md": outline})

        # ① 还没有剧本时读：空
        sc = _data("GET", "/api/v1/art/comic-script", query={"episode_id": eid})
        assert sc["panels"] == [], sc

        # ② 从大纲转：分镜表一行 = 一格
        r = _data("POST", "/api/v1/art/comic-script/from-outline", {"episode_id": eid, "per_page": 4})
        assert r["panel_count"] == 2, r
        sc = _data("GET", "/api/v1/art/comic-script", query={"episode_id": eid})
        assert len(sc["panels"]) == 2
        assert sc["panels"][0]["page"] == 1 and sc["panels"][0]["panel"] == 1
        assert "推门进店" in sc["panels"][0]["text"]
        assert sc["panels"][0]["camera"] == "推"

        # ③ 拆格：一条 = 一个方案，页/格/上一格链排好
        sp = _data("POST", "/api/v1/art/comic-script/split", {"episode_id": eid, "engines": ["novelai"]})
        assert sp["created"] == 2 and sp["skipped"] == 0, sp
        plan_ids.extend(sp["plan_ids"])
        rows = _data("GET", "/api/v1/art/comics", query={"episode_id": eid})
        assert len(rows) == 2, rows
        assert [(x["page"]["index"], x["page"]["panel_index"]) for x in rows] == [(1, 1), (1, 2)], rows
        # 第一格没有上一格；第二格接第一格
        assert rows[0]["page"]["prev_plan_id"] == ""
        assert rows[1]["page"]["prev_plan_id"] == rows[0]["id"]
        # 方案意图来自剧本条目
        assert "画面：" in rows[0]["intent_text"], rows[0]["intent_text"]
        assert "推门进店" in rows[0]["intent_text"], rows[0]["intent_text"]
        assert rows[0]["engines"] == ["novelai"]

        # ④ 幂等：再拆一次不重复建
        sp2 = _data("POST", "/api/v1/art/comic-script/split", {"episode_id": eid})
        assert sp2["created"] == 0 and sp2["skipped"] == 2, sp2

        # ⑤ 剧本可以改完再存（整本覆盖）
        _data("POST", "/api/v1/art/comic-script", {
            "episode_id": eid,
            "panels": [{"page": 1, "panel": 1, "text": "改过的第一格", "dialogue": "台词一", "camera": "中景"}],
        })
        sc2 = _data("GET", "/api/v1/art/comic-script", query={"episode_id": eid})
        assert len(sc2["panels"]) == 1, sc2
        assert sc2["panels"][0]["text"] == "改过的第一格"
        assert sc2["panels"][0]["dialogue"] == "台词一"
    finally:
        for x in plan_ids:
            try:
                req("DELETE", f"/api/v1/art/plans/{x}", timeout=30)
            except Exception:
                pass
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass
