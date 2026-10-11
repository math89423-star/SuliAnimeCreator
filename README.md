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

## 迁移对照
- MirrorStage：Shot Spec/SceneBible/双Reviewer思想已进scriptboard/director，opencode-go LLM后续接llm_client
- CharacterMaker：18槽位/服装四分类/garment-flat简化为character蓝图+前端角色页
- ComfyUIAgent：7个html工具→导演prompt模板，待Vue化为ArtDirector页
