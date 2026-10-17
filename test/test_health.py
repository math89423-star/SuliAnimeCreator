"""健康 + 蓝图注册（demo 蓝图必须已下线）。"""
from conftest import ok, req


def test_health_ok():
    d = ok("/api/health")
    assert d.get("ok") is True


def test_blueprints_no_demo():
    d = ok("/api/health")
    bps = d.get("blueprints", [])
    for b in ("story", "character", "scriptboard", "director", "uploads",
              "tools", "traffic", "dsh"):
        assert b in bps, f"缺蓝图 {b}"
    assert "demo" not in bps, "demo 蓝图应已删除"
