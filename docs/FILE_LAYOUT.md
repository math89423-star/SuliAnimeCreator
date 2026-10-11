# SuliAnimeCreator 文件布局（WSL2 canonical）

```
SuliAnimeCreator/
  backend/                  Flask 后端（:5001）
    app/
      api/                  四蓝图：story.py character.py scriptboard.py director.py + uploads.py
      services/             llm.py（拆镜） disk_store.py（落盘）
      models/               SQLAlchemy 模型（预留，当前真源是 JSON）
      skills/drama-director/ 运行期副本（源头在 /skills/story/drama-director）
    data/                   真源落盘（唯一可写区）
      character_db.json / story_db.json / scriptboard_db.json
      uploads/              头像/槽位图真文件
    requirements.txt run.py Dockerfile
  frontend/                 Vue3+TS 三栏（:5173）
    src/api/client.ts       后端契约唯一出口
    src/components/        LeftNav / CenterWorkspace / RightChat
    src/stores/app.ts
  skills/                   全量 skill 唯一源头（14个，见 skills/README.md）
    character/ image/ story/ video/
  docs/                     架构与索引
  docker-compose.yml        backend/data:/app/data 持久卷
  README.md
```

## 落实规则
1. 可写区只有 `backend/data/`（含 uploads）。别处不写运行时数据。
2. `backend/instance/suli.db` 是 SQLAlchemy 旧库残留，当前 JSON 为真源，切库前勿删勿用。
3. 根下不建 `data/`（已删），`.pytest_cache` 随手清。
4. skill 只认 `/skills`，`backend/app/skills` 仅 drama-director 运行副本。
5. 前后端契约以 `frontend/src/api/client.ts` + 后端 blueprint 为准，`SKILL.md` 不写接口。
