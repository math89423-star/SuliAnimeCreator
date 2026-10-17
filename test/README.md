# test/ 全量功能测试

纯标准库（urllib/zipfile/csv），不装额外依赖。

```bash
python -m pytest test/ -q            # 全量（含 agent 问答，约 3-5 分钟）
python -m pytest test/ -q --ignore=test/test_agent.py   # 快版（约 1 分钟）
python -m pytest test/test_diff_audit.py -q             # 只审 diff
```

前置：后端在 `127.0.0.1:5001` 就绪（`bash cmd.bash status`），
或 `Suli_BASE=http://host:port python -m pytest test/ -q`。
只读演示集 EP-81695F；写操作只建新包/传小文件。
