"""dsh 蓝图：原生 runtime 接管项目 agent，映射表隔离业务。
调用：subprocess `dsh headless --json [--session-id]`，固定 cwd=backend/。
映射：backend/data/dsh_sessions.json {scope,key} -> dsh_session_id。
"""
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from flask import Blueprint, request, jsonify, Response, stream_with_context

from ..services.disk_store import load, save

bp = Blueprint("dsh", __name__, url_prefix="/api/v1/dsh")

_STORE = load("dsh_sessions.json", {"sessions": []})


def _refresh():
    """每次读写前从磁盘重载：单例内存 + 整盘 _persist() 在进程交错时会用旧快照覆盖丢数据。"""
    global _STORE
    try:
        _STORE = load("dsh_sessions.json", {"sessions": []})
    except Exception:
        pass
_LOCKS = {}
_LOCKS_GUARD = threading.Lock()

BACKEND_DIR = Path(__file__).resolve().parents[1]
DSH_BIN = os.getenv("DSH_BIN", "dsh")
DSH_HOME = os.getenv("DSH_HOME", str(Path.home() / ".dsh"))
TIMEOUT_S = int(os.getenv("DSH_TIMEOUT_S", "180"))


def ok(data):
    return jsonify({"code": 0, "data": data})


def _persist():
    save("dsh_sessions.json", _STORE)


def _lock_for(sid):
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(sid or "__new__", threading.Lock())


def _find(session_id=None, scope=None, key=None):
    for s in _STORE.get("sessions", []):
        if session_id and s.get("dsh_session_id") == session_id:
            return s
        if scope and key and s.get("scope") == scope and s.get("key") == key:
            return s
    return None


def _upsert_mapping(scope, key, dsh_session_id):
    _refresh()
    s = _find(scope=scope, key=key)
    now = int(time.time() * 1000)
    if s:
        s["dsh_session_id"] = dsh_session_id or s.get("dsh_session_id")
        s["last_active"] = now
    else:
        s = {"scope": scope, "key": key, "dsh_session_id": dsh_session_id,
             "created_at": now, "last_active": now}
        _STORE.setdefault("sessions", []).append(s)
    _persist()
    return s


def _run_headless(message, session_id=None):
    """跑一次 headless --json，返回 (dsh_session_id, answer, events)。"""
    if not shutil.which(DSH_BIN):
        raise FileNotFoundError(f"dsh binary not found: {DSH_BIN}")
    cmd = [DSH_BIN, "headless", "--json"]
    if session_id:
        cmd += ["--session-id", session_id]
    cmd += [message]
    env = dict(os.environ, DSH_HOME=DSH_HOME)
    proc = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env,
                          capture_output=True, text=True, timeout=TIMEOUT_S)
    events = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            events.append({"type": "raw", "text": line})
    if proc.returncode != 0:
        err = (proc.stderr or "")[-2000:]
        # 未知 session id：dsh 直接报错，上抛 409 由调用方重建
        if session_id and ("unknown" in err.lower() or "error" in err.lower()):
            raise ValueError(f"dsh session resume failed: {err}")
        raise RuntimeError(f"dsh headless failed({proc.returncode}): {err}")
    if not events:
        # 防静默空跑（如容器内 node 版本过低导致入口跳过）：无事件=失败，不吞
        raise RuntimeError("dsh produced no output (events empty); check node>=22 and DSH_HOME mount")
    sid = session_id
    for ev in events:
        if isinstance(ev, dict):
            for k in ("session_id", "sessionId", "session"):
                v = ev.get(k)
                if isinstance(v, str) and v:
                    sid = v
                    break
    answer = ""
    for ev in reversed(events):
        if not isinstance(ev, dict):
            continue
        for k in ("final_message", "message", "text", "answer", "content"):
            v = ev.get(k)
            if isinstance(v, str) and v.strip():
                answer = v
                break
        if answer:
            break
    if not answer and events:
        answer = json.dumps(events[-1], ensure_ascii=False)[:4000]
    return sid, answer, events


@bp.get("/sessions")
def list_sessions():
    _refresh()
    scope = request.args.get("scope", "")
    rows = _STORE.get("sessions", [])
    if scope:
        rows = [r for r in rows if r.get("scope") == scope]
    return ok(rows)


@bp.get("/skills")
def list_skills():
    """skill 加载状态：扫 skills/*/SKILL.md 的 name/description，供前端展示已加载项。"""
    from pathlib import Path as _P
    roots = [
        _P(__file__).resolve().parents[3] / "skills",
        _P(__file__).resolve().parents[1] / "skills",
    ]
    seen, out = set(), []
    for root in roots:
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("SKILL.md")):
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue
            name, desc = "", ""
            for line in text.splitlines()[:20]:
                s = line.strip()
                if s.startswith("name:"):
                    name = s.split(":", 1)[1].strip().strip("\"'")
                if s.startswith("description:"):
                    desc = s.split(":", 1)[1].strip().strip("\"'")[:160]
            key = name or str(f.parent)
            if key in seen:
                continue
            seen.add(key)
            out.append({"name": name or f.parent.name,
                        "description": desc, "path": str(f.parent).replace(str(root.parent) + "/", "")})
    return ok({"skills": out, "count": len(out)})


@bp.post("/sessions")
def get_or_create():
    _refresh()
    b = request.get_json(force=True) or {}
    scope, key = b.get("scope", "story"), b.get("key", "global")
    s = _find(scope=scope, key=key)
    if s:
        return ok(s)
    s = {"scope": scope, "key": key, "dsh_session_id": "",
         "created_at": int(time.time() * 1000), "last_active": 0,
         "note": "lazy: dsh_session_id 落在首次 run 后"}
    _STORE.setdefault("sessions", []).append(s)
    _persist()
    return ok(s)


@bp.put("/sessions/rename")
def rename_session():
    """改名：同 scope 内 key 改名，dsh_session_id 不变；撞名 409。"""
    _refresh()
    b = request.get_json(force=True) or {}
    scope = (b.get("scope") or "").strip()
    key = (b.get("key") or "").strip()
    new_key = (b.get("new_key") or "").strip()
    if not scope or not key or not new_key:
        return jsonify({"code": 4001, "msg": "scope/key/new_key 为空"}), 400
    s = _find(scope=scope, key=key)
    if not s:
        return jsonify({"code": 4004, "msg": "会话不存在"}), 404
    if new_key != key and _find(scope=scope, key=new_key):
        return jsonify({"code": 4002, "msg": f"同组已存在 {new_key}"}), 409
    s["key"] = new_key
    s["last_active"] = int(time.time() * 1000)
    _persist()
    return ok(s)


@bp.delete("/sessions")
def delete_session():
    """删映射：清掉 {scope,key} 的本地映射与 dsh_session_id，前端同时清本地对话。"""
    _refresh()
    b = request.get_json(force=True, silent=True) or {}
    scope = ((b.get("scope") or "") or request.args.get("scope", "")).strip()
    key = ((b.get("key") or "") or request.args.get("key", "")).strip()
    if not scope or not key:
        return jsonify({"code": 4001, "msg": "scope/key 为空"}), 400
    rows = _STORE.get("sessions", [])
    _STORE["sessions"] = [r for r in rows if not (r.get("scope") == scope and r.get("key") == key)]
    _persist()
    return ok({"deleted": True})


@bp.post("/run")
def run():
    _refresh()
    b = request.get_json(force=True) or {}
    message = (b.get("message") or "").strip()
    if not message:
        return jsonify({"code": 4001, "msg": "message 为空"}), 400
    scope, key = b.get("scope", "story"), b.get("key", "global")
    session_id = b.get("session_id") or ""
    mapping = _find(session_id=session_id, scope=scope, key=key) if (session_id or (scope and key)) else None
    resume_id = (mapping or {}).get("dsh_session_id") or session_id or None
    lock = _lock_for(resume_id or f"{scope}:{key}")
    with lock:
        try:
            sid, answer, events = _run_headless(message, resume_id)
        except ValueError as e:
            # 续跑失败：清掉坏映射，409 让前端重建
            if mapping:
                mapping["dsh_session_id"] = ""
                _persist()
            return jsonify({"code": 4090, "msg": str(e)[:500]}), 409
        if scope and key:
            mapping = _upsert_mapping(scope, key, sid or "")
    return ok({"session_id": sid, "scope": scope, "key": key,
               "answer": answer, "events": len(events)})


def _sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@bp.post("/stream")
def stream():
    """SSE：把 headless --json 的 NDJSON 逐行转 SSE，结束帧写映射。"""
    _refresh()
    b = request.get_json(force=True) or {}
    message = (b.get("message") or "").strip()
    if not message:
        return jsonify({"code": 4001, "msg": "message 为空"}), 400
    scope, key = b.get("scope", "story"), b.get("key", "global")
    session_id = b.get("session_id") or ""
    mapping = _find(session_id=session_id, scope=scope, key=key) if (session_id or (scope and key)) else None
    resume_id = (mapping or {}).get("dsh_session_id") or session_id or None
    lock = _lock_for(resume_id or f"{scope}:{key}")

    def gen():
        if not shutil.which(DSH_BIN):
            yield _sse("error", {"msg": f"dsh binary not found: {DSH_BIN}"})
            return
        cmd = [DSH_BIN, "headless", "--json"]
        if resume_id:
            cmd += ["--session-id", resume_id]
        cmd += [message]
        env = dict(os.environ, DSH_HOME=DSH_HOME)
        lock.acquire()
        proc = None
        try:
            proc = subprocess.Popen(cmd, cwd=str(BACKEND_DIR), env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            events = []
            try:
                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        ev = {"type": "raw", "text": line[:2000]}
                    events.append(ev)
                    yield _sse("dsh", {"n": len(events), "event": ev if len(json.dumps(ev, ensure_ascii=False)) < 4000 else {"type": ev.get("type", "?")}})
                _, err = proc.communicate(timeout=TIMEOUT_S)
            except Exception as e:
                proc.kill()
                yield _sse("error", {"msg": f"dsh streaming failed: {str(e)[:500]}"})
                return
            if proc.returncode != 0:
                err = (err or "")[-2000:]
                if resume_id and ("unknown" in err.lower() or "error" in err.lower()):
                    if mapping:
                        mapping["dsh_session_id"] = ""
                        _persist()
                    yield _sse("error", {"code": 4090, "msg": err[:500]})
                else:
                    yield _sse("error", {"msg": f"dsh headless failed({proc.returncode}): {err[:500]}"})
                return
            if not events:
                yield _sse("error", {"msg": "dsh produced no output (events empty); check node>=22 and DSH_HOME mount"})
                return
            sid = resume_id
            for ev in events:
                if isinstance(ev, dict):
                    for k in ("session_id", "sessionId", "session"):
                        v = ev.get(k)
                        if isinstance(v, str) and v:
                            sid = v
                            break
            answer = ""
            for ev in reversed(events):
                if not isinstance(ev, dict):
                    continue
                for k in ("final_message", "message", "text", "answer", "content"):
                    v = ev.get(k)
                    if isinstance(v, str) and v.strip():
                        answer = v
                        break
                if answer:
                    break
            if not answer and events:
                answer = json.dumps(events[-1], ensure_ascii=False)[:4000]
            if scope and key:
                _upsert_mapping(scope, key, sid or "")
            yield _sse("done", {"session_id": sid, "scope": scope, "key": key,
                                "answer": answer, "events": len(events)})
        finally:
            # 客户端中断（停止按钮）→ GeneratorExit 走这里，直接杀掉 dsh 子进程
            try:
                if proc is not None and proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
            if lock.locked():
                try:
                    lock.release()
                except Exception:
                    pass

    return Response(stream_with_context(gen()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
