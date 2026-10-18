"""L-Port 详细提示词回传：临时项目/集/镜 → prompts/import 落 lport_prompts
→ 覆盖语义/缺镜/空条目 → 清理（项目 cascade）。

口径（与 docs/POSITIONING.md「详细提示词回传」一致）：
- 只写已存在的镜，缺镜报告 missing 不造镜；
- 空提示词条目不落（防假回执）；
- 同一镜重传即整条覆盖（当前版本语义）。
"""
import uuid

from conftest import req


def _suffix():
    return uuid.uuid4().hex[:6].upper()


def _data(method, path, body=None, query=None):
    st, d = req(method, path, body=body, query=query, timeout=60)
    assert st == 200, f"{method} {path} http={st} {str(d)[:300]}"
    assert d.get("code") == 0, f"{method} {path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]


def _shots(eid):
    rows = _data("GET", "/api/v1/scriptboard/shots", query={"episode_id": eid})
    return {r["id"]: r for r in rows}


def test_lport_prompt_return_roundtrip():
    suffix = _suffix()
    pid = None
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"提示词回传自检-{suffix}"})
        pid = proj["id"]
        eid = f"EP-LPPR-{suffix}"
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "提示词回传自检集"})
        s1 = _data("POST", "/api/v1/scriptboard/shots",
                   {"episode_id": eid, "duty": "回传自检镜一", "duration_s": 4,
                    "camera": {"crop": "medium", "movement": "推"}})
        s2 = _data("POST", "/api/v1/scriptboard/shots",
                   {"episode_id": eid, "duty": "回传自检镜二", "duration_s": 5,
                    "camera": {"crop": "close", "movement": "固定"}})

        r = _data("POST", "/api/v1/scriptboard/shots/prompts/import", {
            "episode_id": eid, "source": "lport:seg_prompt", "package_id": f"PKG-{eid}-1",
            "prompts": [
                {"shot_id": s1["id"], "seg_id": "SEG-01", "director_cn": "她在窗边回头，镜头推近。",
                 "camera_note": "推镜：压近她的脸", "key_text_en": "she turns back by the window",
                 "dialogue_cn": "你回来了。", "ref_status": "待补", "ref_missing": ["起始帧画面"],
                 "duration_s": 4, "crop": "medium"},
                {"shot_id": s2["id"], "director_cn": "他放下杯子。", "duration_s": 5},
                {"shot_id": "SHOT-NOPE-999999", "director_cn": "不存在的镜"},  # 缺镜：报告不造
                {"shot_id": s1["id"], "seg_id": "SEG-99"},                    # 空正文：skip
            ]})
        assert r["count"] == 2, r
        assert s1["id"] in r["updated"] and s2["id"] in r["updated"], r
        assert r["missing"] == ["SHOT-NOPE-999999"], r
        assert r["skipped"] == 1, r
        assert r["source"] == "lport:seg_prompt", r

        rows = _shots(eid)
        assert set(rows) == {s1["id"], s2["id"]}, "缺镜不许被提示词造出来"
        lp1 = rows[s1["id"]].get("lport_prompts") or {}
        assert lp1.get("director_cn") == "她在窗边回头，镜头推近。", lp1
        assert lp1.get("source") == "lport:seg_prompt" and lp1.get("at"), lp1
        assert lp1.get("package_id") == f"PKG-{eid}-1", lp1
        assert lp1.get("ref_missing") == ["起始帧画面"], lp1
        assert lp1.get("duration_s") == 4, lp1
        assert rows[s2["id"]].get("lport_prompts", {}).get("director_cn") == "他放下杯子。"

        # 重传覆盖：整条替换（当前版本语义），旧字段不许残留
        _data("POST", "/api/v1/scriptboard/shots/prompts/import", {
            "episode_id": eid, "source": "lport:seg_prompt",
            "prompts": [{"shot_id": s1["id"], "director_cn": "改后的提示词。"}]})
        lp1b = _shots(eid)[s1["id"]]["lport_prompts"]
        assert lp1b["director_cn"] == "改后的提示词。", lp1b
        assert "key_text_en" not in lp1b and "camera_note" not in lp1b, "重传应整条覆盖"

        # 跨集防串：同 sid 换集号 → 应报 missing 不写
        st, d = req("POST", "/api/v1/scriptboard/shots/prompts/import", body={
            "episode_id": "EP-OTHER", "prompts": [{"shot_id": s1["id"], "director_cn": "串集"}]},
            timeout=30)
        assert st == 200 and d["data"]["missing"] == [s1["id"]], d
        assert _shots(eid)[s1["id"]]["lport_prompts"]["director_cn"] == "改后的提示词。"
    finally:
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_lport_prompts_validation():
    st, d = req("POST", "/api/v1/scriptboard/shots/prompts/import", body={}, timeout=30)
    assert st == 400 and d.get("code") == 4001, d
    st, d = req("POST", "/api/v1/scriptboard/shots/prompts/import",
                body={"episode_id": "EP-NOPE"}, timeout=30)
    assert st == 400 and d.get("code") == 4001, d
    st, d = req("POST", "/api/v1/scriptboard/shots/prompts/import",
                body={"episode_id": "EP-NOPE", "prompts": []}, timeout=30)
    assert st == 400 and d.get("code") == 4001, d
    st, d = req("POST", "/api/v1/scriptboard/shots/prompts/import",
                body={"episode_id": "EP-NOPE", "prompts": [{"director_cn": "x"}] * 65}, timeout=30)
    assert st == 400 and d.get("code") == 4001, d
