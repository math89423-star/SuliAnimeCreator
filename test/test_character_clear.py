"""角色页「清除（槽位）/ 清空（提示词）」：DELETE assets + DELETE slot-prompts。

约定：自建一个临时角色跑全流程，跑完删掉；不碰现成角色（CHAR-233A04 等）。
"""
import base64
import json
import urllib.request

import pytest

from conftest import BASE, ok, req

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)


def _upload_slot(cid: str, kind: str, slot: str, filename: str = "probe.png"):
    """给槽位传 1px PNG（multipart：file + kind + slot）。"""
    bd = "----testbdclear"
    body = (
        f"--{bd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + PNG_1PX + (
        f"\r\n--{bd}\r\nContent-Disposition: form-data; name=\"kind\"\r\n\r\n{kind}\r\n"
        f"--{bd}\r\nContent-Disposition: form-data; name=\"slot\"\r\n\r\n{slot}\r\n"
        f"--{bd}--\r\n"
    ).encode()
    r = urllib.request.Request(
        BASE + f"/api/v1/characters/{cid}/assets/file",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={bd}"},
    )
    with urllib.request.urlopen(r, timeout=60) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    assert d.get("code") == 0, d
    return d["data"]


def _delete(path: str, body: dict):
    st, d = req("DELETE", path, body)
    assert st == 200, f"{path} http={st} {str(d)[:200]}"
    assert d.get("code") == 0, f"{path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]


def _assets(cid, kind="", slot=""):
    rows = ok(f"/api/v1/characters/{cid}/assets")
    return [a for a in rows if (not kind or a["kind"] == kind) and (not slot or a["slot"] == slot)]


def _prompts(cid):
    return ok(f"/api/v1/characters/{cid}/slot-prompts")


def _has_prompt(cid, kind, slot):
    return any(p["kind"] == kind and p["slot"] == slot for p in _prompts(cid))


@pytest.fixture(scope="module")
def cid():
    st, d = req("POST", "/api/v1/characters", {"name": "清除自测"})
    assert st == 200 and d.get("code") == 0, d
    c = d["data"]["id"]
    yield c
    req("DELETE", f"/api/v1/characters/{c}")


def test_clear_single_slot_image_and_both_prompts(cid):
    _upload_slot(cid, "head_dressed", "front")
    assert len(_assets(cid, "head_dressed", "front")) == 1
    req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
        {"kind": "head_dressed", "slot": "front", "prompt": "front en prompt"})
    req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
        {"kind": "head_dressed", "slot": "front_cn", "prompt": "正面中文提示词"})
    assert _has_prompt(cid, "head_dressed", "front")
    assert _has_prompt(cid, "head_dressed", "front_cn")

    d = _delete(f"/api/v1/characters/{cid}/assets", {"kind": "head_dressed", "slot": "front"})
    assert d.get("cleared") == 1, d
    assert _assets(cid, "head_dressed", "front") == []

    d = _delete(f"/api/v1/characters/{cid}/slot-prompts",
                {"kind": "head_dressed", "slot": "front", "which": "both"})
    assert d.get("cleared") == 2, d
    assert not _has_prompt(cid, "head_dressed", "front")
    assert not _has_prompt(cid, "head_dressed", "front_cn")
    # 只清 front，同组 side/back 的记录不受牵连
    req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
        {"kind": "head_dressed", "slot": "side", "prompt": "side en"})
    _delete(f"/api/v1/characters/{cid}/slot-prompts",
            {"kind": "head_dressed", "slot": "front", "which": "both"})
    assert _has_prompt(cid, "head_dressed", "side")


def test_clear_prompt_which_single_side(cid):
    req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
        {"kind": "half_dressed", "slot": "front", "prompt": "en keep"})
    req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
        {"kind": "half_dressed", "slot": "front_cn", "prompt": "中文待清"})

    d = _delete(f"/api/v1/characters/{cid}/slot-prompts",
                {"kind": "half_dressed", "slot": "front", "which": "cn"})
    assert d.get("cleared") == 1, d
    assert not _has_prompt(cid, "half_dressed", "front_cn")
    assert _has_prompt(cid, "half_dressed", "front"), "清中文不该动英文槽"

    d = _delete(f"/api/v1/characters/{cid}/slot-prompts",
                {"kind": "half_dressed", "slot": "front", "which": "en"})
    assert d.get("cleared") == 1, d
    assert not _has_prompt(cid, "half_dressed", "front")


def test_clear_whole_group_three_slots(cid):
    for s in ("front", "side", "back"):
        _upload_slot(cid, "full_dressed", s)
        req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
            {"kind": "full_dressed", "slot": s, "prompt": f"{s} en"})
        req("PUT", f"/api/v1/characters/{cid}/slot-prompts",
            {"kind": "full_dressed", "slot": f"{s}_cn", "prompt": f"{s} 中文"})
    assert len(_assets(cid, "full_dressed")) == 3

    # 清空本组：不传 slot → 该 kind 的 front/side/back 全清
    d = _delete(f"/api/v1/characters/{cid}/assets", {"kind": "full_dressed"})
    assert d.get("cleared") == 3, d
    assert _assets(cid, "full_dressed") == []

    d = _delete(f"/api/v1/characters/{cid}/slot-prompts", {"kind": "full_dressed"})
    assert d.get("cleared") == 6, d
    assert [p for p in _prompts(cid) if p["kind"] == "full_dressed"] == []


def test_clear_assets_ignores_other_character(cid):
    """按 cid 隔离：清别人角色的图不许命中本角色的行。"""
    st, d = req("POST", "/api/v1/characters", {"name": "清除自测-旁证"})
    other = d["data"]["id"]
    try:
        _upload_slot(other, "head_dressed", "front")
        _upload_slot(cid, "head_dressed", "front")
        _delete(f"/api/v1/characters/{other}/assets", {"kind": "head_dressed", "slot": "front"})
        assert len(_assets(cid, "head_dressed", "front")) == 1, "清旁证角色时误伤本角色"
    finally:
        _delete(f"/api/v1/characters/{other}/assets", {})
        req("DELETE", f"/api/v1/characters/{other}")
    _delete(f"/api/v1/characters/{cid}/assets", {})
    assert _assets(cid) == []
