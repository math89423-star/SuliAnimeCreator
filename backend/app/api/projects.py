"""projects 蓝图：顶栏项目切换。落盘 backend/data/projects_db.json。

项目是工作区容器：每个项目登记自己的集号（episode_ids），回执按项目 + 集号归位。
集号内容仍以 scriptboard 的 episode_id 为键；这里只维护归属索引，不复制业务数据。
"""
from flask import Blueprint, request, jsonify
import re
import time
import uuid
from ..services.disk_store import load, save

bp = Blueprint("projects", __name__, url_prefix="/api/v1/projects")

_STORE = load("projects_db.json", {"items": []})

_EP_ID_RE = re.compile(r"^[^\W_][\w\-]{0,63}$", re.UNICODE)


def ok(data):
    return jsonify({"code": 0, "data": data})


def _now():
    return int(time.time() * 1000)


def _refresh():
    global _STORE
    try:
        loaded = load("projects_db.json", {"items": []})
        if isinstance(loaded, dict):
            _STORE = loaded
    except Exception:
        pass


def _persist():
    save("projects_db.json", _STORE)


def _clean_text(value, max_len=80, default=""):
    text = str(value or "").strip()
    if not text:
        return default
    return text[:max_len]


def _clean_episode_id(value):
    eid = str(value or "").strip()
    if not eid or len(eid) > 64:
        return ""
    if any(ch.isspace() or ord(ch) < 32 for ch in eid):
        return ""
    if not _EP_ID_RE.match(eid):
        return ""
    return eid


def _clean_id_list(values):
    out = []
    for v in values or []:
        eid = _clean_episode_id(v)
        if eid and eid not in out:
            out.append(eid)
    return out


def _normalize_project(row):
    if not isinstance(row, dict):
        return {"id": "", "name": "", "episode_ids": [], "episode_titles": {},
                "current_episode_id": "", "created_at": 0, "updated_at": 0}
    episodes = _clean_id_list(row.get("episode_ids"))
    titles = row.get("episode_titles") if isinstance(row.get("episode_titles"), dict) else {}
    clean_titles = {eid: _clean_text(title, 120) for eid, title in titles.items()
                    if _clean_episode_id(eid) and _clean_text(title, 120)}
    current = _clean_episode_id(row.get("current_episode_id"))
    if current and current not in episodes:
        current = ""
    row["id"] = str(row.get("id") or "")
    row["name"] = _clean_text(row.get("name"), 80, "未命名项目")
    row["episode_ids"] = episodes
    row["episode_titles"] = clean_titles
    row["current_episode_id"] = current
    row["created_at"] = int(row.get("created_at") or 0)
    row["updated_at"] = int(row.get("updated_at") or row["created_at"] or 0)
    return row


def _find_project(pid):
    pid = str(pid or "").strip()
    for row in _STORE.get("items", []):
        if isinstance(row, dict) and row.get("id") == pid:
            return row
    return None


def get_project(pid):
    """跨蓝图只读出口：返回归一化后的项目副本。"""
    _refresh()
    row = _find_project(pid)
    return _view_project(row) if row else None


def _project_or_404(pid):
    row = _find_project(pid)
    if not row:
        return None, (jsonify({"code": 4040, "msg": "项目不存在"}), 404)
    return _normalize_project(row), None


def project_id_for_episode(eid):
    """集号归属查询：返回拥有该集号的项目，没有返回空串。"""
    eid = _clean_episode_id(eid)
    if not eid:
        return ""
    for row in _STORE.get("items", []):
        if isinstance(row, dict) and eid in (row.get("episode_ids") or []):
            return str(row.get("id") or "")
    return ""


def _episode_content(eid):
    from ..services import repo as _repo
    return _repo.get_episode(eid) or {}


def _episode_shot_count(eid):
    from ..services import repo as _repo
    try:
        return len(_repo.list_shots_by_episode(eid))
    except Exception:
        return 0


def _episode_title(ep, eid):
    title = _clean_text(ep.get("title"), 120)
    if title:
        return title
    for md in (ep.get("outline_md") or "", ep.get("screenplay_md") or ""):
        for line in str(md).splitlines():
            text = line.strip().lstrip("#").strip()
            if text:
                return text[:80]
    return eid


def _unique_project_id():
    taken = {str(r.get("id")) for r in _STORE.get("items", []) if isinstance(r, dict)}
    for _ in range(100):
        pid = "PRJ-" + uuid.uuid4().hex[:6].upper()
        if pid not in taken:
            return pid
    raise RuntimeError("项目 ID  exhausted")


def _unique_episode_id():
    from ..services import repo as _repo
    taken = set(_repo.episodes_map().keys())
    for row in _STORE.get("items", []):
        if isinstance(row, dict):
            taken.update(row.get("episode_ids") or [])
    for _ in range(200):
        eid = "EP-" + uuid.uuid4().hex[:6].upper()
        if eid not in taken:
            return eid
    raise RuntimeError("集号 exhausted")


def _view_project(row):
    row = _normalize_project(row)
    return {
        "id": row["id"], "name": row["name"], "episode_ids": list(row["episode_ids"]),
        "episode_titles": dict(row["episode_titles"]),
        "current_episode_id": row["current_episode_id"],
        "episode_count": len(row["episode_ids"]),
        "created_at": row["created_at"], "updated_at": row["updated_at"],
    }


def _view_episode(pid, eid):
    ep = _episode_content(eid)
    return {
        "id": eid, "project_id": pid,
        "title": _episode_title(ep, eid),
        "exists": bool(ep),
        "shot_count": _episode_shot_count(eid),
        "has_outline": bool(str(ep.get("outline_md") or "").strip()),
        "has_screenplay": bool(str(ep.get("screenplay_md") or "").strip()),
        "ref_image_count": len(ep.get("ref_images") or []) if isinstance(ep.get("ref_images"), list) else 0,
    }


def _set_episode_owner_content(eid, pid, title=""):
    """在剧本库骨架上同步归属/标题；不覆盖已有正文、镜头和参考图。"""
    from .scriptboard import _EPS
    from .scriptboard import _persist as _persist_sb
    ep = _EPS.setdefault(eid, {"id": eid, "screenplay_md": "", "segs": [], "verdict": "draft"})
    ep["project_id"] = pid
    if title:
        ep["title"] = _clean_text(title, 120)
    _persist_sb()
    return ep


def _clear_episode_owner_content(eid, pid):
    from .scriptboard import _EPS
    from .scriptboard import _persist as _persist_sb
    ep = _EPS.get(eid)
    if isinstance(ep, dict) and ep.get("project_id") == pid:
        ep["project_id"] = ""
        _persist_sb()


def _delete_episode_content(eids, project_id=""):
    """删除项目下属集号的内容骨架、镜头、回执和 Agent 会话映射；上传文件按既有 clear 语义留盘。"""
    from .scriptboard import _EPS, _SHOTS
    from .scriptboard import _persist as _persist_sb
    from .receipts import delete_scoped as _delete_scoped_receipts
    from .dsh import _STORE as _DSTORE
    from .dsh import _persist as _persist_dsh
    targets = _clean_id_list(eids)
    removed_shots = [sid for sid, shot in list(_SHOTS.items())
                     if isinstance(shot, dict) and shot.get("episode_id") in targets]
    for sid in removed_shots:
        _SHOTS.pop(sid, None)
    removed_episodes = [eid for eid in targets if _EPS.pop(eid, None) is not None]
    _persist_sb()
    removed_receipts = _delete_scoped_receipts(project_id=project_id, episode_ids=targets)
    sessions = _DSTORE.get("sessions", [])
    kept = [s for s in sessions if not (
        isinstance(s, dict) and s.get("scope") == "episode" and s.get("key") in targets)]
    removed_sessions = len(sessions) - len(kept)
    _DSTORE["sessions"] = kept
    _persist_dsh()
    return {
        "episodes": removed_episodes, "shots": len(removed_shots),
        "receipts": removed_receipts, "sessions": removed_sessions,
        "uploads_retained": True,
    }


@bp.get("")
def list_all():
    _refresh()
    rows = [_view_project(r) for r in _STORE.get("items", [])]
    _persist()
    return ok(rows)


@bp.post("")
def create():
    _refresh()
    b = request.get_json(force=True) or {}
    name = _clean_text(b.get("name"), 80, "新项目")
    if not name:
        return jsonify({"code": 4001, "msg": "项目名不能为空"}), 400
    row = {
        "id": _unique_project_id(), "name": name, "episode_ids": [],
        "episode_titles": {}, "current_episode_id": "",
        "created_at": _now(), "updated_at": _now(),
    }
    _STORE.setdefault("items", []).append(row)
    requested = _clean_episode_id(b.get("episode_id"))
    episode = None
    if requested:
        owner = project_id_for_episode(requested)
        if owner and owner != row["id"] and not b.get("move"):
            _persist()
            return jsonify({"code": 4002, "msg": f"集号已属于项目 {owner}"}), 409
        if owner and owner != row["id"]:
            old = _find_project(owner)
            if old:
                old["episode_ids"] = [e for e in old.get("episode_ids", []) if e != requested]
        row["episode_ids"].append(requested)
        row["current_episode_id"] = requested
        if _clean_text(b.get("episode_title"), 120):
            row["episode_titles"][requested] = _clean_text(b.get("episode_title"), 120)
        episode = _view_episode(row["id"], requested)
    _persist()
    out = _view_project(row)
    if episode:
        out["episode"] = episode
    return ok(out)


@bp.put("/<pid>")
def update(pid):
    _refresh()
    row, err = _project_or_404(pid)
    if err:
        return err
    b = request.get_json(force=True) or {}
    changed = False
    if "name" in b:
        name = _clean_text(b.get("name"), 80)
        if not name:
            return jsonify({"code": 4001, "msg": "项目名不能为空"}), 400
        if name != row.get("name"):
            row["name"] = name
            changed = True
    if "current_episode_id" in b:
        current = _clean_episode_id(b.get("current_episode_id"))
        if current and current not in row.get("episode_ids", []):
            return jsonify({"code": 4002, "msg": "当前集号尚未加入本项目"}), 409
        if current != row.get("current_episode_id"):
            row["current_episode_id"] = current
            changed = True
    for key, adding in (("add_episode_ids", True), ("remove_episode_ids", False)):
        if key in b:
            ids = _clean_id_list(b.get(key))
            if adding:
                planned = []
                for eid in ids:
                    owner = project_id_for_episode(eid)
                    if owner and owner != row["id"] and not b.get("move"):
                        return jsonify({"code": 4002, "msg": f"集号 {eid} 已属于项目 {owner}"}), 409
                    if eid not in row["episode_ids"] and eid not in planned:
                        planned.append(eid)
                for eid in planned:
                    owner = project_id_for_episode(eid)
                    if owner and owner != row["id"]:
                        old = _find_project(owner)
                        if old:
                            old["episode_ids"] = [e for e in old.get("episode_ids", []) if e != eid]
                            old["updated_at"] = _now()
                    row["episode_ids"].append(eid)
                    changed = True
            else:
                before = len(row["episode_ids"])
                row["episode_ids"] = [e for e in row["episode_ids"] if e not in ids]
                for eid in ids:
                    row["episode_titles"].pop(eid, None)
                    _clear_episode_owner_content(eid, row["id"])
                if row.get("current_episode_id") in ids:
                    row["current_episode_id"] = ""
                changed = changed or len(row["episode_ids"]) != before
    if changed:
        row["updated_at"] = _now()
        _persist()
    return ok(_view_project(row))


@bp.delete("/<pid>")
def delete(pid):
    _refresh()
    row, err = _project_or_404(pid)
    if err:
        return err
    b = request.get_json(force=True, silent=True) or {}
    mode = str(b.get("mode") or request.args.get("mode") or "detach").strip().lower()
    if mode not in ("detach", "cascade"):
        return jsonify({"code": 4001, "msg": "mode 只能是 detach|cascade"}), 400
    episodes = list(row.get("episode_ids", []))
    deleted = {"project_id": row["id"], "mode": mode, "episodes": [], "shots": 0,
               "receipts": 0, "sessions": 0, "uploads_retained": True}
    if mode == "cascade" and episodes:
        deleted.update(_delete_episode_content(episodes, row["id"]))
    if mode == "detach":
        for eid in episodes:
            _clear_episode_owner_content(eid, row["id"])
    _STORE["items"] = [r for r in _STORE.get("items", []) if r.get("id") != row["id"]]
    _persist()
    return ok(deleted)


@bp.get("/<pid>/episodes")
def list_episodes(pid):
    _refresh()
    row, err = _project_or_404(pid)
    if err:
        return err
    return ok({
        "project_id": row["id"], "project_name": row["name"],
        "current_episode_id": row.get("current_episode_id", ""),
        "episodes": [_view_episode(row["id"], eid) for eid in row.get("episode_ids", [])],
    })


@bp.post("/<pid>/episodes")
def create_episode(pid):
    _refresh()
    row, err = _project_or_404(pid)
    if err:
        return err
    b = request.get_json(force=True) or {}
    requested = _clean_episode_id(b.get("episode_id"))
    title = _clean_text(b.get("title"), 120)
    move = bool(b.get("move"))
    if requested:
        eid = requested
    else:
        eid = _unique_episode_id()
    owner = project_id_for_episode(eid)
    if owner and owner != row["id"] and not move:
        return jsonify({"code": 4002, "msg": f"集号 {eid} 已属于项目 {owner}"}), 409
    if owner and owner != row["id"]:
        old = _find_project(owner)
        if old:
            old["episode_ids"] = [e for e in old.get("episode_ids", []) if e != eid]
            old.get("episode_titles", {}).pop(eid, None)
            if old.get("current_episode_id") == eid:
                old["current_episode_id"] = ""
            old["updated_at"] = _now()
    if eid not in row["episode_ids"]:
        row["episode_ids"].append(eid)
    if title:
        row["episode_titles"][eid] = title
    row["current_episode_id"] = eid
    row["updated_at"] = _now()
    _set_episode_owner_content(eid, row["id"], title)
    _persist()
    return ok(_view_episode(row["id"], eid))


@bp.delete("/<pid>/episodes/<eid>")
def delete_episode(pid, eid):
    _refresh()
    row, err = _project_or_404(pid)
    if err:
        return err
    eid = _clean_episode_id(eid)
    if not eid or eid not in row.get("episode_ids", []):
        return jsonify({"code": 4004, "msg": "集号不在本项目"}), 404
    b = request.get_json(force=True, silent=True) or {}
    mode = str(b.get("mode") or request.args.get("mode") or "unregister").strip().lower()
    if mode not in ("unregister", "delete"):
        return jsonify({"code": 4001, "msg": "mode 只能是 unregister|delete"}), 400
    deleted = {"project_id": row["id"], "episode_id": eid, "mode": mode,
               "shots": 0, "receipts": 0, "sessions": 0, "uploads_retained": True}
    if mode == "delete":
        deleted.update(_delete_episode_content([eid], row["id"]))
    else:
        _clear_episode_owner_content(eid, row["id"])
    row["episode_ids"] = [x for x in row.get("episode_ids", []) if x != eid]
    row.get("episode_titles", {}).pop(eid, None)
    if row.get("current_episode_id") == eid:
        row["current_episode_id"] = ""
    row["updated_at"] = _now()
    _persist()
    return ok(deleted)

