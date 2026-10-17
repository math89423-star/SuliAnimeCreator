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

## Docker 部署
- 镜像：`backend`（python3.11 + node24 + dsh CLI + ffmpeg）+ `frontend`（nginx  serving dist，反代 `/api/` → backend:5001）。
- 端口：`5173→前端80`，`5001→后端`。本机已有 dev 进程占着这两个口时，先停 dev 再 `up`，或改 compose 端口映射。
- 首次部署三件事：
  1. `mkdir -p dsh-home && cp -r ~/.dsh/profiles ~/.dsh/.credentials.yaml dsh-home/`（sessions/凭据落这里，不进镜像）；
  2. `cp .env.example .env`，填 `OPENCODE_API_KEY`（LLM/大纲/拆镜用；不填则全走本地模板回退）；
  3. `docker compose up --build -d`，验 `curl localhost:5001/api/health` + 打开 `http://宿主IP:5173`。
- 数据：`./backend/data` 挂进 `/app/data`（uploads/各 `_db.json`），删容器不丢；备份拷这个目录即可。
- 宿主 SearXNG（:8888）想给容器用：compose 里解开 `SEARXNG_URL=http://host.docker.internal:8888`；不解则搜索自动降级 Wikipedia/DDG。

## 迁移对照
- MirrorStage：Shot Spec/SceneBible/双Reviewer思想已进scriptboard/director，opencode-go LLM后续接llm_client
- CharacterMaker：18槽位/服装四分类/garment-flat简化为character蓝图+前端角色页
- ComfyUIAgent：7个html工具→导演prompt模板，待Vue化为ArtDirector页
