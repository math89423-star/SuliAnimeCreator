"""投流线：生成(含挂载位) → 导出包 → 反馈回流 → 参数校验。"""
import csv
import io
import zipfile

import pytest

from conftest import EP, ok, req

MOUNT = {"search_word": "测试剧", "app_name": "测试小程序", "overlay_text": "点击左下角观看"}


@pytest.fixture(scope="module")
def pkg():
    st, d = req("POST", "/api/v1/traffic/generate", body={
        "tasks": [{"desc": "全量测试混剪卡点", "mode": "lib", "category": "红包点击",
                   "count": 2, "mount": dict(MOUNT)}]}, timeout=120)
    assert st == 200, d
    assert d.get("code") == 0, d
    return d["data"]


def test_generate_mount_ok(pkg):
    assert pkg["checks"].get("mount_ok") is True
    for v in pkg["variants"]:
        assert v.get("mount") == MOUNT, v


def test_generate_empty_tasks_rejected():
    st, d = req("POST", "/api/v1/traffic/generate", body={"tasks": []}, timeout=60)
    assert st != 200 or d.get("code") != 0  # 空任务必须被拦


def test_export_bundle_contents(pkg):
    pid = pkg["package_id"]
    st, payload = req("GET", "/api/v1/traffic/export-bundle",
                      query={"package_id": pid}, timeout=60, raw=True)
    assert st == 200, payload[:200]
    z = zipfile.ZipFile(io.BytesIO(payload))
    names = z.namelist()
    for n in ("package.json", "materials.csv", "splice.txt", "manifest.json"):
        assert n in names, names
    rows = list(csv.DictReader(io.StringIO(z.read("materials.csv").decode("utf-8"))))
    assert rows, "materials.csv 为空"
    for c in ("search_word", "app_name", "overlay_text"):
        assert c in rows[0], rows[0].keys()
        assert rows[0][c] == MOUNT[c]
    sp = z.read("splice.txt").decode("utf-8")
    assert "挂载[测试剧/测试小程序/点击左下角观看]" in sp


def test_export_missing_package_404():
    st, d = req("GET", "/api/v1/traffic/export-bundle",
                query={"package_id": "PKG-NOT-EXIST-0000"}, timeout=30)
    assert st == 404


def test_feedback_roundtrip(pkg):
    vid = pkg["variants"][0]["variant_id"]
    st, d = req("POST", "/api/v1/traffic/feedback", body={
        "package_id": pkg["package_id"], "variant_id": vid,
        "ctr": 0.08, "keep3s": 0.6, "cvr": 0.01}, timeout=30)
    assert st == 200 and d.get("code") == 0, d
    assert d["data"]["variant_id"] == vid
