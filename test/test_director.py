"""短剧线：大纲/分镜只读 → 草案包导出（只读，不断言写盘）。"""
import io
import json
import zipfile

from conftest import EP, ok, req


def test_outline_exists():
    d = ok(f"/api/v1/scriptboard/outline/{EP}")
    assert d.get("episode_id") == EP
    assert (d.get("outline_md") or "").strip(), "演示集大纲为空"


def test_shots_present():
    d = ok("/api/v1/scriptboard/shots", query={"episode_id": EP})
    rows = d if isinstance(d, list) else d.get("shots", [])
    assert len(rows) >= 3, f"演示集草案镜数不足: {len(rows)}"
    for r in rows:
        assert int(r.get("duration_s") or 0) > 0, f"{r.get('id')} 时长非法"
    total = sum(int(r.get("duration_s") or 0) for r in rows)
    assert total > 0


def test_director_export_bundle():
    st, payload = req("GET", "/api/v1/director/export-bundle",
                      query={"episode_id": EP}, timeout=120, raw=True)
    assert st == 200, payload[:200]
    z = zipfile.ZipFile(io.BytesIO(payload))
    names = z.namelist()
    for n in ("manifest.json", "shots.json", "beats.json", "outline.md",
              "screenplay_draft.md", "prompts.json"):
        assert n in names, names
    shots = json.loads(z.read("shots.json").decode("utf-8"))
    rows = shots if isinstance(shots, list) else shots.get("shots", [])
    assert len(rows) >= 3
    for s in rows:
        assert "ref_mode" in s, f"shots.json 缺 ref_mode: {s.get('id')}"
    manifest = json.loads(z.read("manifest.json").decode("utf-8"))
    assert manifest.get("episode_id") == EP


def test_draft_doc_ok():
    st, payload = req("GET", "/api/v1/director/draft-doc",
                      query={"episode_id": EP}, timeout=60, raw=True)
    assert st == 200, payload[:200]
    text = payload.decode("utf-8")
    assert EP in text, text[:200]
