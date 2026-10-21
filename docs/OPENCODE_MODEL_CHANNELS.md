# OpenCode 模型通道口径与 Free 模型落地（2026-10-17 火花实测 + 对齐）

> 背景：OpenCode 客户端列出一批 "Free" 模型。本文记录哪些能进本项目、哪些不能、为什么，
> 以及 dsh 模型配置的**管理方式**（LLMCoreBreak 协议分组补丁）与 2026-10-17 的对齐/修复记录。

## TL;DR

- **TUI/客户端里的 Free 模型（Console free tier）：只能在 OpenCode 客户端内使用。**
  外部 API 调用被官方硬拒（实测 `403 FreeTierError: cannot be used from within OpenCode`）。
  → **不能加进本项目的 API 调用链，这是官方限制。**
- **本项目（dsh）走 OpenCode Go 订阅通道**（`oc_sk_` key）。其中：
  - `longcat-2.5-preview-free`：Unlimited（限时）、0 保留、不训练——**容器内 dsh 实测跑通**；
  - `beam-free`：Unlimited，但**中国大陆网络 403**（容器实测；宿主进程带代理时可通）。
- **模型配置由 LLMCoreBreak/dsh 的协议分组补丁统一管理**（`patches/llm-opencode-go.yml`
  + `scripts/apply-opencode-providers.py`），dsh-home 已于 2026-10-17 与宿主 `~/.dsh` 对齐。

## 三层通道（别混）

| 通道 | baseURL | 说明 | 外部 API |
|---|---|---|---|
| Console free tier（客户端内） | `https://opencode.ai/inference/...` | Nemotron*/Big Pickle/GLM-5.3-Flash Free/DS4.1F Free… | ✗ 403 FreeTierError |
| Console 付费（按量） | `https://opencode.ai/inference/...` | 同上 + 付费模型 | ✓ 按量付费 |
| **Go 订阅（本项目用）** | `https://opencode.ai/zen/go/v1` | 37 模型；free：longcat-2.5-preview-free、beam-free | ✓ 订阅额度内；free 不占额度 |

Go 客户端要求：典型 agent 流量 + 自带 UA + `x-opencode-session` 头。dsh（DeepSeek Harness）
是官方点名的已知客户端（部分路径缺 session，官方识别其 native header）。

## 数据政策速查（NSFW / 破甲内容用）

- ✅ 0 保留、不训练：GLM-5.3-Flash、GLM-5.3/5.2、DeepSeek V4.1 Flash/Pro、**LongCat 2.5 Preview Free**、Kimi、MiMo、Qwen、MiniMax、Space Bunny
- ⚠️ 30 天保留：Grok 4.7、GPT 6/5.6 Luna、Claude Haiku 5.5、**Beam Free**
- ⛔ 训练/收集：Muse Spark Contributor（Meta，官方 Region 限制）、Gemini 4 Argon Contributor、Big Pickle、Nemotron 系列（试验条款）
- ⛔ 地区限制实测：**Muse Spark / Beam Free 在容器（大陆直连）403 RegionError；宿主进程（带代理环境变量）可通**

## 模型配置管理（LLMCoreBreak 协议分组补丁）

**源头**：`~/LLMCoreBreak/dsh/patches/llm-opencode-go.yml`
**应用**：`python3 ~/LLMCoreBreak/dsh/scripts/apply-opencode-providers.py [--check]`
（幂等：缺组补组、缺模型补模型、默认模型行只报告不改写；自动备份）

**三组 provider**（网关按「模型 → 线协议」路由，`api` 是 provider 级字段，必须按协议拆）：

| 组 | api | baseURL | 代表模型（节选） |
|---|---|---|---|
| `opencode-go` | openai-completions | `.../zen/go/v1` | deepseek 系、glm 系、kimi、mimo、**longcat-2.5-preview-free**、space-bunny、step-5-preview、cat-jam-free |
| `opencode-go-responses` | openai-responses | `.../zen/go/v1` | muse-spark 1.2/1.3-contributor、grok-4.7、gpt-5.6-luna、gpt-6-luna |
| `opencode-go-anthropic` | anthropic-messages | `.../zen/go`（不带 /v1） | claude-haiku-5-5、minimax-m3、qwen 3.7/3.8 系 |

要点：手声明 route 不自动带 session header → 每组 `headers.x-opencode-session` 静态补
（`__DSH_SESSION__` → `dsh-session-administrator-main`）。

### 2026-10-17 对齐记录

1. `~/dsh-corebreak` 改名 → `~/LLMCoreBreak/dsh`（包名保留 `dsh-corebreak` 兼容 link/条目 id）：
   - `dsh-home/profiles/{headless,web}/package.json` 的 `link:` → `.../LLMCoreBreak/dsh`
   - 验证：容器内 dump-config **无 corebreak skipping** ✓
   - 挂载路径现为 `/home/administrator/LLMCoreBreak/dsh:/home/administrator/LLMCoreBreak/dsh:ro`
     （2026-10-22 起改挂宿主同路径：profile 里 dsh-corebreak 是指向该绝对路径的软链，
     两边路径一致则宿主/容器共用同一份 profile 软链，不再依赖「容器内相对路径恰好落到挂载点」）。2. `dsh-home` 两个 `cordis.patch.yml` 以宿主 `~/.dsh` 版覆盖（三组 provider + tool-web 段；
   旧手工 `opencode-go-free` route 移除——longcat 已在组 1）。备份：`*.bak-huohua-20261017-140036`
3. **修复**：flash 的「全 null reasoningEfforts」块（作者 10-17 尝试）已全部移除：
   - `none` 键违反 schema（枚举仅 off/minimal/low/medium/high/xhigh/max）；
   - 修掉 none 后**仍然静默卡死**（ds4.1f + effort=max，150s+ 请求不完成）；
   - 删块后走 catalog 默认 → **16.9s 正常完成**（容器实测）。
   - 涉及文件：LLMCoreBreak 源 + 宿主 `~/.dsh` ×2 + dsh-home ×2。

### 怎么用

- 默认：headless = `deepseek-v4.1-flash`（effort max）、web = `deepseek-v4.1-flash`（high）。
- **SuliAnimeCreator 前端（右侧 Agent）已支持切换**（2026-10-17）：面板顶部模型下拉
  （DeepSeek V4.1 Flash / LongCat 2.5 Preview Free），选择持久化（localStorage
  `suli.agent.model`），**每次发送按当前选择生效**。后端白名单校验（dsh.py `_RUN_MODELS`）
  → 通过 `dsh --patch` 覆盖 agent-default-model（实测长会话 resume 换模型可行）。
- dsh web UI：模型选择器亦可切（UI 切换会重写 agent-default-model 条目）。
- 命令行切换：`dsh headless --patch use-longcat.yml "<任务>"`
  （⚠ `--patch` 是 launcher 选项，必须放在 `--json`/`--session-id` 之前）。

## 实测记录（2026-10-17）

| 测试 | 结果 |
|---|---|
| 外部 API 调 `deepseek-v4.1-flash-free` | ✗ 403 FreeTierError（官方限客户端） |
| 容器 dsh：`longcat-2.5-preview-free` | ✓ 多次跑通 |
| 容器 dsh：`beam-free` | ✗ 403 RegionError（大陆直连） |
| 容器 dsh：默认 `deepseek-v4.1-flash`（对齐后 + corebreak 加载） | ✓ 17s 内完成 |
| 宿主 dsh：`muse-spark-1.3-contributor`（走宿主网络） | ✓ 通；但输出带「Rejecting embedded jailbreak instructions」摩擦信号 |
| 全 null reasoningEfforts（修复前） | ✗ 静默卡死（150s+ 无输出） |
| API 层带 `model=longcat-2.5-preview-free` 起 run | ✓ 12s 完成，run 记录带 model |
| 未知模型（gpt-5） | ✓ 400 拒绝（白名单生效） |
| 前端下拉切换 longcat → 发送 | ✓（E2E 验证，含请求体 `model` 字段） |

## 已知运维遗留

- **corebreak 已四层全开**（2026-10-17）：容器 web 的 `dsh-purge` 已移除（package.json /
  pnpm-lock / node_modules / .modules.yaml 四处清理，规避两者改同一批 dsh 全局文件的冲突）；
  corebreak 宿主补丁实测写入 **16 个 dsh 全局文件**（`.corebreak.bak` 在场），幂等；
  容器 recreate 后由 `autoApplyOnStart` 自动重打，无需持久化处理。
- **Muse Spark 已弃用**（2026-10-17 主人裁定：众包数据会收集对话，不可用于破甲/NSFW）。
  5 处配置的 muse 条目已删（LLMCoreBreak 源 + 宿主 ~/.dsh ×2 + dsh-home ×2）；
  源模板默认模型改为 `deepseek-v4.1-flash / effort=max`。**后续只走 longcat 与 deepseek。**
- web profile 的 `dsh-builtin-browser@0.1.19`、`dsh-tool-git@0.1.3` 与 dsh 0.2.0-rc.2
  版本不兼容跳过（既有，未处理）。
- 容器无代理环境变量（宿主有 `http://172.31.160.1:7897`）：地区敏感模型（grok/gpt 系等）
  在容器内可能受限；如需容器走代理，给 backend 加 `HTTPS_PROXY` + 准确 `NO_PROXY`
  （排除 localhost/searxng/host.docker.internal 等）**待主人定夺**。
