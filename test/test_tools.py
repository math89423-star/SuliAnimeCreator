"""工具线：上传 → 视频抽帧（含无切点回退）→ 搜索透传。"""
import io
import json
import urllib.parse
import urllib.request

import pytest

from conftest import ok, req


def _upload(data: bytes, filename: str):
    bd = "----testbduuid"
    body = (f"--{bd}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode() \
        + data + f"\r\n--{bd}--\r\n".encode()
    from conftest import BASE
    r = urllib.request.Request(BASE + "/api/v1/uploads", data=body,
                               headers={"Content-Type": f"multipart/form-data; boundary={bd}"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_upload_text_kind_file():
    d = _upload(b"hello-test", "probe.txt")
    assert d.get("code") == 0, d
    assert d["data"].get("kind") == "file"
    assert d["data"].get("url", "").startswith("/api/images/")


def test_video_frames_missing_404():
    st, d = req("POST", "/api/v1/tools/video-frames",
                body={"path": "no-such-file-xyz.mp4"}, timeout=30)
    assert st == 404 and d.get("code") == 4004


def test_video_frames_needs_url_or_path():
    st, d = req("POST", "/api/v1/tools/video-frames", body={}, timeout=30)
    assert d.get("code") == 4001


def test_video_frames_response_shape():
    """用已上传的演示视频断言返回形态（含 mode 字段）；无切点片走 uniform 也有帧。"""
    name = "627aeeb767ba4d2b957775e688b8bfb0.mp4"
    st, d = req("POST", "/api/v1/tools/video-frames", body={
        "path": name, "max_frames": 4}, timeout=180)
    if st == 404:
        import pathlib
        cand = pathlib.Path("/home/administrator/L-Port-Comfy/app/backend/data/"
                            "libraries/投流素材库/videos/悬念提问_女孩微笑藏着什么_21.mp4")
        if not cand.is_file():
            pytest.skip("演示视频素材不在本机，跳过形态断言")
        up = _upload(cand.read_bytes(), "shape_probe.mp4")
        assert up.get("code") == 0, up
        name = up["data"]["path"]
        st, d = req("POST", "/api/v1/tools/video-frames", body={
            "path": name, "max_frames": 4}, timeout=180)
    assert st == 200 and d.get("code") == 0, str(d)[:300]
    data = d["data"]
    assert data.get("mode") in ("scene", "uniform")
    assert data.get("count", 0) >= 1
    assert data["frames"][0]["url"].startswith("/api/images/")
