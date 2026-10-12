"""disk_store：data/*.json 真落盘。进程重启不丢。

本模块是全仓唯一的 JSON 持久化出口：
- 原子写：先写 tmp 再 rename，避免半截 JSON；
- 读失败回 default，不抛。
业务蓝图不要自己拼 Path，一律走 load/save。
"""
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "data"
ROOT.mkdir(parents=True, exist_ok=True)


def load(name, default):
    p = ROOT / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(name, obj):
    """原子写：tmp + fsync + rename。保持旧签名，旧调用方无须改。"""
    p = ROOT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        os.replace(tmp, p)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
