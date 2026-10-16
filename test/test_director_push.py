"""导演草案直投 L-Port：临时项目/集/镜 → push-lport 落收件箱 → 回执轮询基线 → 清理。"""
import json
import pathlib
import shutil
import subprocess
import uuid
import zipfile

from conftest import req

INBOX = pathlib.Path("/home/administrator/L-Port-Comfy/app/backend/data/libraries/投流素材库/suli_packages")


def _rm_push_dir(pkg):
    """收件箱是后端容器（root）写的，宿主测试用户直接删会权限不足：优先走容器内删。"""
    try:
        r = subprocess.run(["docker", "exec", "sulianimecreator-backend-1",
                            "rm", "-rf", f"/lport-lib/suli_packages/{pkg}"],
                           capture_output=True, timeout=30)
        if r.returncode == 0:
            return
    except Exception:
        pass
    shutil.rmtree(INBOX / pkg, ignore_errors=True)


def _suffix():
    return uuid.uuid4().hex[:6].upper()


def _data(method, path, body=None, query=None):
    st, d = req(method, path, body=body, query=query, timeout=120)
    assert st == 200, f"{method} {path} http={st} {str(d)[:300]}"
    assert d.get("code") == 0, f"{method} {path} code={d.get('code')} msg={d.get('msg')}"
    return d["data"]


def test_director_push_lport_roundtrip():
    suffix = _suffix()
    pid = None
    pushedPkg = None
    pushed_dir = None
    try:
        proj = _data("POST", "/api/v1/projects", {"name": f"直投自检-{suffix}"})
        pid = proj["id"]
        eid = f"EP-PUSH-{suffix}"
        _data("POST", f"/api/v1/projects/{pid}/episodes", {"episode_id": eid, "title": "直投自检集"})
        _data("POST", "/api/v1/scriptboard/shots",
              {"episode_id": eid, "duty": "直投自检镜", "sound": "", "duration_s": 4,
               "camera": {"crop": "medium", "movement": "固定"}})

        pushed = _data("POST", "/api/v1/director/push-lport",
                       {"episode_id": eid, "project_id": pid, "engine": "pixai"})
        pkg = pushed["package_id"]
        pushedPkg = pkg
        assert pkg.startswith(f"PKG-{eid}-"), pkg
        assert pushed["shot_count"] >= 1
        pushed_dir = INBOX / pkg
        assert pushed_dir.is_dir(), f"收件箱缺目录 {pushed_dir}"
        names = {p.name for p in pushed_dir.iterdir()}
        assert f"{pkg}.zip" in names and "manifest.json" in names and "package.json" in names, names

        z = zipfile.ZipFile(str(pushed_dir / f"{pkg}.zip"))
        for n in ("manifest.json", "shots.json", "prompts.json"):
            assert n in z.namelist(), z.namelist()
        manifest = json.loads(z.read("manifest.json").decode("utf-8"))
        assert manifest["package_id"] == pkg and manifest["project_id"] == pid
        package_json = json.loads((pushed_dir / "package.json").read_text(encoding="utf-8"))
        assert package_json["package_id"] == pkg and package_json["episode_id"] == eid
        assert isinstance(package_json.get("shots"), list) and package_json["shots"]

        # 回执轮询基线：刚投递还没有回执，前端轮询应拿到空列表（不等 404）
        rows = _data("GET", "/api/v1/receipts", query={"package_id": pkg})
        assert rows == [], rows
    finally:
        if pushedPkg:
            _rm_push_dir(pushedPkg)
        if pid:
            try:
                req("DELETE", f"/api/v1/projects/{pid}", query={"mode": "cascade"}, timeout=60)
            except Exception:
                pass


def test_director_push_validation():
    st, d = req("POST", "/api/v1/director/push-lport", body={}, timeout=30)
    assert st == 400 and d.get("code") == 4001, d
    st, d = req("POST", "/api/v1/director/push-lport",
                body={"episode_id": "EP-NOPE", "project_id": "PRJ-NOPE"}, timeout=30)
    assert st == 409, d
