"""receipts 蓝图：执行回执登记（只存事实，不触发重生成）。落盘 backend/data/receipts_db.json。
回执字段由我方定（A向裁定），l-port 按此交回执。

回执必须归位到项目 + 集号：新建回执默认需要可解析的 episode_id，并由此解析
project_id（或显式传入且必须与归属一致）。历史脏数据不强制改写，查询时用
显式值优先、推断值兜底的方式归位。
"""
from flask import Blueprint, request, jsonify
import re
import time
from ..services.disk_store import load, save

bp = Blueprint("receipts", __name__, url_prefix="/api/v1/receipts")

_STORE = load("receipts_db.json", {"items": []})

REQUIRED = ["package_id", "shot_id", "task_id", "engine", "status"]
_EP_RE = re.compile(r"\bEP-[A-Za-z0-9]{2,32}\b")


def ok(data):
    return jsonify({"code": 0, "data": data})


def _persist():
    save("receipts_db.json", _STORE)


def _clean(value, max_len=500):
    text = str(value or "").strip()
    return text[:max_len]


def _truthy(value):
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


def _infer_episode_id(*values):
    for value in values:
        if not value:
            continue
        m = _EP_RE.search(str(value))
        if m:
            return m.group(0)
    return ""


def _known_project(pid):
    if not pid:
        return False
    try:
        from .projects import _STORE as _PSTORE
        return any(isinstance(r, dict) and r.get("id") == pid for r in _PSTORE.get("items", []))
    except Exception:
        return False


def _known_episode(eid):
    if not eid:
        return False
    try:
        from ..services import repo as _repo
        if eid in _repo.episodes_map():
            return True
    except Exception:
        pass
    try:
        from .projects import project_id_for_episode
        return bool(project_id_for_episode(eid))
    except Exception:
        return False


def _project_for_episode(eid):
    if not eid:
        return ""
    try:
        from .projects import project_id_for_episode
        return project_id_for_episode(eid) or ""
    except Exception:
        return ""


def _normalize_row(row):
    src = row if isinstance(row, dict) else {}
    explicit_project = _clean(src.get("project_id"), 32)
    explicit_episode = _clean(src.get("episode_id"), 64)
    inferred_episode = _infer_episode_id(
        explicit_episode, src.get("package_id"), src.get("media_url"),
        src.get("task_id"), src.get("shot_id"))
    episode = explicit_episode or inferred_episode
    project = explicit_project or _project_for_episode(episode)
    if explicit_episode and inferred_episode and explicit_episode != inferred_episode:
        source = "explicit"
    elif explicit_project or explicit_episode:
        source = "explicit" if explicit_project and episode else "partial"
    elif episode:
        source = "inferred"
    else:
        source = "unscoped"
    out = dict(src)
    out["project_id"] = project
    out["episode_id"] = episode
    out["project_id_explicit"] = explicit_project
    out["episode_id_explicit"] = explicit_episode
    out["scope_source"] = source
    return out


def _row_matches(row, project_id="", episode_id="", package_id="", status="", shot_id=""):
    scope = _normalize_row(row)
    if project_id and scope["project_id"] != project_id:
        return False
    if episode_id and scope["episode_id"] != episode_id:
        return False
    if package_id and str(row.get("package_id") or "") != package_id:
        return False
    if status and str(row.get("status") or "") != status:
        return False
    if shot_id and str(row.get("shot_id") or "") != shot_id:
        return False
    return True


def scoped_rows(project_id="", episode_id="", package_id="", status="", shot_id=""):
    normalized = [_normalize_row(x) for x in _STORE.get("items", [])]
    return [r for r in normalized
            if _row_matches(r, project_id=project_id, episode_id=episode_id,
                            package_id=package_id, status=status, shot_id=shot_id)]


def delete_scoped(project_id="", episode_ids=()):
    """按项目/集号清理回执：只删归位命中的行，返回删除条数。"""
    targets = {str(eid) for eid in (episode_ids or []) if str(eid or "").strip()}
    kept = []
    removed = 0
    for row in _STORE.get("items", []):
        scope = _normalize_row(row)
        hit_project = bool(project_id) and scope["project_id"] == project_id
        hit_episode = bool(targets) and scope["episode_id"] in targets and scope["project_id"] in ("", project_id)
        if hit_project or hit_episode:
            removed += 1
        else:
            kept.append(row)
    if removed:
        _STORE["items"] = kept
        _persist()
    return removed


@bp.get("")
def list_all():
    project_id = _clean(request.args.get("project_id", ""), 32)
    episode_id = _clean(request.args.get("episode_id", ""), 64)
    package_id = _clean(request.args.get("package_id", ""), 128)
    status = _clean(request.args.get("status", ""), 32)
    shot_id = _clean(request.args.get("shot_id", ""), 128)
    rows = [_normalize_row(x) for x in _STORE.get("items", [])]
    rows = [r for r in rows
            if _row_matches(r, project_id=project_id, episode_id=episode_id,
                            package_id=package_id, status=status, shot_id=shot_id)]
    return ok(sorted(rows, key=lambda r: r.get("created_at", 0), reverse=True))


@bp.post("")
def create():
    b = request.get_json(force=True) or {}
    missing = [k for k in REQUIRED if not b.get(k)]
    if missing:
        return jsonify({"code": 4001, "msg": "缺字段: " + ",".join(missing)}), 400
    explicit_project = _clean(b.get("project_id"), 32)
    explicit_episode = _clean(b.get("episode_id"), 64)
    allow_unscoped = _truthy(b.get("allow_unscoped"))
    episode = explicit_episode or _infer_episode_id(
        b.get("package_id"), b.get("media_url"), b.get("task_id"), b.get("shot_id"))
    if not episode and not allow_unscoped:
        return jsonify({"code": 4001, "msg": "缺字段: episode_id（可从 package_id/media_url/task_id/shot_id 推断，或显式传入）"}), 400
    if episode and not _known_episode(episode) and not allow_unscoped:
        return jsonify({"code": 4002, "msg": f"未知集号 {episode}：先在项目下新建/加入该集号"}), 409
    if explicit_project and not _known_project(explicit_project):
        return jsonify({"code": 4002, "msg": f"未知项目 {explicit_project}"}), 409
    owner = _project_for_episode(episode)
    if explicit_project and owner and explicit_project != owner:
        return jsonify({"code": 4002, "msg": f"集号 {episode} 已属于项目 {owner}"}), 409
    project = explicit_project or owner
    if not project and not allow_unscoped:
        return jsonify({"code": 4001, "msg": "缺字段: project_id（该集号尚未归属任何项目）"}), 400
    source = "explicit" if (explicit_project or explicit_episode) else ("inferred" if episode else "unscoped")
    row = {
        "package_id": b["package_id"], "shot_id": b["shot_id"],
        "task_id": b["task_id"], "engine": b["engine"],
        "provider": b.get("provider", ""), "media_url": b.get("media_url", ""),
        "status": b["status"], "log_tail": (b.get("log_tail") or "")[:2000],
        "deviations": b.get("deviations") or [],
        "form": (b.get("form") or b.get("ref_mode") or "").strip(),
        "project_id": project, "episode_id": episode,
        "project_id_explicit": explicit_project, "episode_id_explicit": explicit_episode,
        "scope_source": source,
        "created_at": int(time.time() * 1000),
    }
    _STORE.setdefault("items", []).append(row)
    _persist()
    return ok(_normalize_row(row))
