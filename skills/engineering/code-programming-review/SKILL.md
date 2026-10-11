---
name: code-programming-review
description: 代码编程与自审查总纲。任何改代码前先读：先取证再动手、最小 diff、可验证收尾。覆盖 Python/TS 双栈：Google Review 维度、PEP8 命名布局、Vue 生产构建。触发词：写代码、改后端、改前端、重构、自查、review、门禁。
sources:
  - https://google.github.io/eng-practices/review/reviewer/looking-for.html
  - https://google.github.io/eng-practices/review/reviewer/
  - https://peps.python.org/pep-0008/
---

# Code Programming Review（代码编程与自审查）

> 联网依据，不自编：审查维度取 [Google What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html)（Design/Functionality/Complexity/Tests/Naming/Comments/Style/Consistency/Documentation/Every Line/Context）；Python 风格取 [PEP 8](https://peps.python.org/pep-0008/)；流程取 [How to do a code review](https://google.github.io/eng-practices/review/reviewer/)。本地适配（`backend/data` 唯一可写区、前后端同名契约）为本仓附加，不替代原文。

## 0. 动手前（先取证，不凭记忆写代码）

1. 先 `read` 要改的文件与上下游调用方（至少 1 层），再定 diff 范围。
2. 动后端先看 blueprint 注册表（`backend/app/__init__.py`）与契约（`frontend/src/api/client.ts`）；动前端先看路由表与 store。
3. 说明：`web_search` 通道因 key 失效不可用（401），改用 `web_fetch` 直取上文；`openviking-memory` 与编码无关未调用。

## 1. 审查维度（Google 原文映射）

- Design：各部件交互是否合理？该放库还是放本仓？与系统其余部分是否集成？现在是否该加这个功能？([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Functionality：是否做了作者想做的？对用户（终端+后续开发者）是否好？UI 变更要看演示；并行代码要推演死锁/竞态。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Complexity：行/函数/类是否“不能被快速读懂”？警惕 over-engineering：只解现在已知的问题，不解猜测的未来问题。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Tests：同 CL 配单测/集成/E2E；用例本身要对（坏代码下会红、改代码不误报、断言简单有用）；测试也是要维护的代码。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Naming：名字够长到讲清是什么，不长到读不动。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Comments：注释讲 why 不讲 what；看不懂先让代码变简单；正则/复杂算法例外可讲 what；同时看旧 TODO/警告是否已过期。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Style/Consistency：风格指南是绝对权威；指南推荐项则判读（偏向跟指南，除非局部不一致更迷惑）；无规则处跟周边现有代码。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))
- Documentation + Every Line + Context：改了构建/测试/交互/发布就同步文档；被分配到的每一行都要看懂；只看 diff 上下几行不够，要看全文件与系统上下文；看不懂就让作者澄清（你看不懂=未来人也看不懂）。([来源](https://google.github.io/eng-practices/review/reviewer/looking-for.html))

## 2. Python 落点（PEP 8）

- 4 空格缩进、顶层 def/class 间两空行、方法间一空行；导入分三组（标准/第三方/本地）各空一行，禁 `import sys, os` 同行与通配符。([来源](https://peps.python.org/pep-0008/))
- 命名：函数/变量 `lower_case`、类 `CapWords`、常量 `UPPER_CASE`、单下划线=内部；`is/is not None` 不用 `==`；`def f():` 不用 `f = lambda`；`except Exception` 不用裸 `except:`。([来源](https://peps.python.org/pep-0008/))
- 注释是完整英文句子（本仓允许中文，但首词大写、句号结尾的精神保留：写清原因）；docstring 按 PEP 257 给公开模块/函数/类写。([来源](https://peps.python.org/pep-0008/))

## 3. 本仓收尾三件套（每次必跑）

```bash
python3 -c "import sys; sys.path.insert(0,'/home/administrator/SuliAnimeCreator/backend'); from app import create_app; print(create_app().test_client().get('/api/health').json)"
npm run build 2>&1 | tail -n 3
docker compose config -q && echo "compose OK"
```

任一红即停。最小 diff、运行时数据只写 `backend/data/`、前后端同名契约为本仓硬门。
