"""agent 基本问答（慢，调 dsh headless；超时放宽到 200s）。"""
import uuid

from conftest import req


def _fresh_key(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_agent_math():
    st, d = req("POST", "/api/v1/dsh/run", body={
        "scope": "story", "key": _fresh_key("test-qa-math"),
        "message": "1+1等于几？只答数字，不要任何解释。"}, timeout=200)
    assert st == 200 and d.get("code") == 0, str(d)[:300]
    ans = (d["data"].get("answer") or "").strip().rstrip("。.")
    assert ans == "2", f"agent 基础问答异常: {ans!r}"
    assert d["data"].get("retried") is False


def test_agent_chinese_constraint():
    st, d = req("POST", "/api/v1/dsh/run", body={
        "scope": "story", "key": _fresh_key("test-qa-cn"),
        "message": "用一句话说清短剧前3秒钩子的作用，不超过30个字，只输出这一句。"},
        timeout=200)
    assert st == 200 and d.get("code") == 0, str(d)[:300]
    ans = (d["data"].get("answer") or "").strip()
    assert ans and len(ans) <= 30, f"字数约束未遵守: {ans!r}"
