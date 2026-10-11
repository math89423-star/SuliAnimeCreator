"""disk_store：data/*.json 真落盘。进程重启不丢。"""
import json
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
    p = ROOT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
