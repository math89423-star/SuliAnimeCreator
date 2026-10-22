# SuliAnimeCreator（WSL2自研整合版）

本目录即新大项目。来源：D盘三项目聚合。

## 四蓝图
- `backend/app/api/story.py` 文本故事：suggest(发散3方向)→confirm(落库)
- `backend/app/api/character.py` 原创角色：角色+服装，承接CharacterMaker
- `backend/app/api/scriptboard.py` 剧本分镜：screenplay保存→auto-split规则拆镜→review结构门
- `backend/app/api/director.py` 视频导演：prompts组装纯文本，复制到第三方生产

## 前后端分离
- 前端 `frontend/` Vue3+TS三栏式（LeftNav/CenterWorkspace/RightChat），`npm run build`已验证通过
- 后端 `backend/` Flask四蓝图，`:5001`，`GET /api/health` smoke通过

## human-in-loop
故事suggest→人工confirm→剧本保存→自动拆镜→人工改镜→review/run→approve→prompts/assemble→复制场外。suggest永不直写库。

## 启动
- 本地：`cd backend && python run.py` + `cd frontend && npm run dev`
- Docker：`docker compose up --build`

## 代码托管
- 远端：`git@github.com:math89423-star/SuliAnimeCreator.git`（**私有**，SSH 推；与 `SuliQQbot` / `L-Port-Comfy` 同账号同口径）。
- 推之前：`./cmd.bash check` 跑自检（扫密钥形态 + 核对 gitignore 覆盖 + 列待推规模），
  `./cmd.bash push` 自检+确认+推送一并做完。`dsh-home/`（含明文 key）与 `dsh-runtime/` 已被 gitignore 挡住。
- 破甲内核 `LLMCoreBreak/` 在另一个仓库，**无远端、不外发**；本仓只是引用它的路径。

## Docker 部署
- 镜像：`suli-anime-backend`（python3.11 + node24 + ffmpeg）+ `frontend`（nginx serving dist，反代 `/api/` → backend:5001）。
  **dsh CLI 不在镜像里**：装在宿主 `dsh-runtime/<版本>/`，容器挂载使用（见下）。
- 端口：`5173→前端80`，`5001→后端`。本机已有 dev 进程占着这两个口时，先停 dev 再 `up`，或改 compose 端口映射。
- 首次部署四件事：
  1. `mkdir -p dsh-home && cp -r ~/.dsh/profiles ~/.dsh/.credentials.yaml dsh-home/`（sessions/凭据落这里，不进镜像）；
  2. `cp .env.example .env`，填 `OPENCODE_API_KEY`（LLM/大纲/拆镜用；不填则全走本地模板回退）；
  3. `./cmd.bash dsh install 0.2.0-rc.2`（装 dsh 到宿主 `dsh-runtime/`，含打破甲补丁；约 1 分钟）；
  4. `docker compose up --build -d`，验 `curl localhost:5001/api/health` + 打开 `http://宿主IP:5173`。
- 数据：`./backend/data` 挂进 `/app/data`（uploads/各 `_db.json`），删容器不丢；备份拷这个目录即可。
- 宿主 SearXNG（:8888）想给容器用：compose 里解开 `SEARXNG_URL=http://host.docker.internal:8888`；不解则搜索自动降级 Wikipedia/DDG。

## dsh 版本管理
dsh CLI 装在宿主 `dsh-runtime/<版本>/`（每版自带完整的 `@deepseek-ai/*` bundle + 破甲补丁），
容器按 `.env` 的 `DSH_VERSION` 挂载使用。**升 dsh 不必重建后端镜像**：

```
./cmd.bash dsh list              # 已装版本 + 当前使用版本
./cmd.bash dsh install 0.2.1-rc.2   # 装新版本（宿主装 + 打破甲补丁）
./cmd.bash dsh use 0.2.1-rc.2    # 切默认版本（写 .env 的 DSH_VERSION）
./cmd.bash dsh status            # 看当前版本的破甲补丁状态
docker compose up -d             # 生效（不 build）
```

破甲补丁（`LLMCoreBreak/dsh`）在**安装时**逐版本打：corebreak 的补丁要改写 dsh 安装目录里的文件，
容器启动时那个定时器在 one-shot headless 下不可靠；且打补丁必须只落在目标版本上（corebreak 会枚举 PATH 里
所有 dsh 宿主），安装脚本用隔离 PATH + `DSH_AI_BASE` 双重定向。
安装时还会校正 profile 里 `dsh-corebreak` 的软链（须指向 `LLMCoreBreak/dsh` 真实位置）：
`dsh-home` 不入库，新机器上拷来的软链可能还指着仓库改名前的旧路径，悬空 = 破甲层整个不加载
（表现是 dsh 启动 stderr「skipping profile bundle "dsh-corebreak"」）。

凭据两通道并行：key 既写进 `$DSH_HOME/.credentials.yaml`（dsh ≤0.2.0 的交互式凭据存储），
也注入进程环境 `OPENCODE_GO_API_KEY`（dsh ≥0.2.1：headless bundle 刻意禁用 credentials/authorization，
改用「启动时凭据」）。少任一条，对应版本就报缺凭据。

## 迁移对照
- MirrorStage：Shot Spec/SceneBible/双Reviewer思想已进scriptboard/director，opencode-go LLM后续接llm_client
- CharacterMaker：18槽位/服装四分类/garment-flat简化为character蓝图+前端角色页
- ComfyUIAgent：7个html工具→导演prompt模板，待Vue化为ArtDirector页
