"""项目/集号/回执闭环：只建临时数据，跑完级联清理，不碰现成集。"""
import io
import json
import uuid
import zipfile

import pytest

from conftest import ok, req


def _suffix():
    return uuid.uuid4().hex[:6].upper()


def _data(method, path, body=None, query=None):
    st, d = req(method, path, body=body, query=query, timeout=60)
    assert st == 200, f"{method} {path} http={st} {str(d)[:300]}"
    assert d.get("code") == 0, f"{method} {path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]


@pytest.fixture(scope="module")
def workspace():
    suffix = _suffix()
    created = {"projects": [], "suffix": suffix}
    try:
        pa = _data("POST", "/api/v1/projects", {"name": f"自检项目-{suffix}"})
        pb = _data("POST", "/api/v1/projects", {"name": f"自检项目-{suffix}-B"})
        created["projects"].extend([pa["id"], pb["id"]])
        created.update({"a": pa["id"], "b": pb["id"], "episode": f"EP-TEST-{suffix}"})
        yield created
    finally:
        for pid in reversed(created.get("projects", [])):
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_project_episode_lifecycle(workspace):
    a, b, eid = workspace["a"], workspace["b"], workspace["episode"]
    title = f"自检集-{workspace['suffix']}"

    ep = _data("POST", f"/api/v1/projects/{a}/episodes", {"episode_id": eid, "title": title})
    assert ep["id"] == eid and ep["project_id"] == a and ep["title"] == title

    listed = _data("GET", f"/api/v1/projects/{a}/episodes")
    assert listed["current_episode_id"] == eid
    assert [x["id"] for x in listed["episodes"]] == [eid]

    st, d = req("POST", f"/api/v1/projects/{b}/episodes", {"episode_id": eid}, timeout=30)
    assert st == 409, d
    moved = _data("POST", f"/api/v1/projects/{b}/episodes", {"episode_id": eid, "move": True})
    assert moved["project_id"] == b
    assert _data("GET", f"/api/v1/projects/{a}/episodes")["episodes"] == []

    auto = _data("POST", f"/api/v1/projects/{b}/episodes", {"title": title})
    assert auto["id"].startswith("EP-") and auto["id"] != eid
    assert auto["project_id"] == b
    workspace["auto_episode"] = auto["id"]

    updated = _data("PUT", f"/api/v1/projects/{b}", {"current_episode_id": auto["id"]})
    assert updated["current_episode_id"] == auto["id"]
    assert eid in updated["episode_ids"]


def test_scoped_receipt_lifecycle(workspace):
    b = workspace["b"]
    eid = workspace["episode"]
    suffix = workspace["suffix"]
    package = f"PKG-TEST-{suffix}"
    shot = f"SHOT-TEST-{suffix}-M001"
    task = f"TASK-TEST-{suffix}"

    rec = _data("POST", "/api/v1/receipts", {
        "package_id": package, "shot_id": shot, "task_id": task,
        "engine": "test-engine", "status": "done",
        "project_id": b, "episode_id": eid,
    })
    assert rec["project_id"] == b and rec["episode_id"] == eid and rec["scope_source"] == "explicit"

    rows = _data("GET", "/api/v1/receipts", query={"project_id": b, "episode_id": eid})
    assert any(r["shot_id"] == shot and r["package_id"] == package for r in rows), rows
    assert all(r["project_id"] == b and r["episode_id"] == eid for r in rows), rows

    st, payload = req("GET", "/api/v1/director/export-bundle",
                      query={"episode_id": eid, "project_id": b}, timeout=120, raw=True)
    assert st == 200, payload[:200]
    z = zipfile.ZipFile(io.BytesIO(payload))
    assert "receipts.json" in z.namelist(), z.namelist()
    manifest = json.loads(z.read("manifest.json").decode("utf-8"))
    assert manifest.get("project_id") == b, manifest
    assert manifest.get("episode_id") == eid, manifest
    assert manifest.get("receipt_count", 0) >= 1, manifest
    receipts = json.loads(z.read("receipts.json").decode("utf-8"))
    assert any(r.get("shot_id") == shot for r in receipts), receipts

    st, d = req("POST", "/api/v1/receipts", {
        "package_id": package, "shot_id": shot, "task_id": task,
        "engine": "test-engine", "status": "done",
        "project_id": workspace["a"], "episode_id": eid,
    }, timeout=30)
    assert st == 409, d


def test_project_delete_detach_and_cascade(workspace):
    a, b = workspace["a"], workspace["b"]
    # A 已在迁移后变空：detach 只删项目行，不应报错也不应动 B 的内容。
    detached = _data("DELETE", f"/api/v1/projects/{a}", query={"mode": "detach"})
    assert detached["project_id"] == a and detached["mode"] == "detach"
    workspace["projects"].remove(a)
    assert all(p["id"] != a for p in _data("GET", "/api/v1/projects"))

    cascaded = _data("DELETE", f"/api/v1/projects/{b}", query={"mode": "cascade"})
    assert cascaded["project_id"] == b and cascaded["mode"] == "cascade"
    assert cascaded["receipts"] >= 1 and cascaded["episodes"], cascaded
    workspace["projects"].remove(b)
    assert all(p["id"] != b for p in _data("GET", "/api/v1/projects"))
    st, _ = req("GET", f"/api/v1/projects/{b}/episodes", timeout=30)
    assert st == 404
    assert _data("GET", "/api/v1/receipts", query={"project_id": b}) == []
    assert _data("GET", "/api/v1/scriptboard/shots", query={"episode_id": workspace["episode"]}) == []
