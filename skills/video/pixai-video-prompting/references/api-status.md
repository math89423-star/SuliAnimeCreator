# PixAI API 现状（查证）

> 来源：官方开发者文档 `https://platform.pixai.art/en/docs`（另有机器可读版 `/llms.txt`、`/llms-full.txt`，改版时优先拉这两份）。
> 结论先说：**图片生成有 API，视频生成没有 API。**

## 1 官方原文（Limits → Feature limitations）

- **Video generation is not supported.**
- PixAI Reference Pro / PixAI Edit / PixAI Edit Lite **not supported yet**（在开发中）。
- 等待队列：每账号最多 **10 个 `waiting` 任务**（`running` 不计），上限可按账号申请提升；不强制请求速率限制，
  但建议**轮询不高于每 1.5 秒一次**，重试用指数退避。

**含义**：Tsubaki Video / Tsubaki Video Flash 目前**只能走网页/App 界面**，
本项目的"出稿 → 人工粘贴到 PixAI 生成"这条路径在视频侧仍然是唯一路径。

## 2 图片生成 API（可用）

| 项 | 值 |
|---|---|
| Base URL | `https://api.pixai.art` |
| 认证 | `Authorization: Bearer <API_KEY>`（在 `pixai.art/en/profile/edit/api` 建 key；亦可向 API 团队申请） |
| 建任务 | `POST /v2/image/create`（prompt + model + 可选 aspect ratio / mode / style preset），返回 `waiting` 任务 |
| 查任务 | `GET /v1/task/{taskId}`（≤1.5s 一次；可改用 webhook 推送） |
| 取媒体 | `GET /v1/media/{mediaId}`；`GET /v1/media/{mediaId}/image` 直接重定向到文件 |
| 保留期 | **生成媒体不长期保存**，任务完成立刻下载 |
| 回调 | Webhook 可在任务完成时 POST 任务对象，免轮询 |

**可用图片模型（API 白名单，实测文档所列）**：

| 模型 | modelId | 备注 |
|---|---|---|
| Tsubaki.2 | `1983308862240288769` | DIT；提示词理解与执行强、解剖稳、多角色互动好 |
| Haruka v2 | `1861558740588989558` | SDXL；质量稳、手部准 |
| Hoshino v2 | `1954632828118619567` | 日系流行风格 |

⚠️ **注意**：API 白名单里目前是 **Tsubaki.2**，不等于网页版的 Tsubaki.3。要 Tsubaki.3 请先确认该模型 ID 是否已开放给 API
（文档"Models"页为准）；采样方法按各模型允许列表填（Haruka v2 支持 Euler a / DPM++ 2M Karras 等一串）。

## 3 若要自动化"视频"这一步，替代路径

PixAI 视频无 API → 想自动化只能换执行侧：

- **火山方舟 Seedance 系列**（本项目已在用它家的 Seedream 出图，同一套 key 体系）：
  控制台模型表里有 `doubao-seedance-2-5-260628` 等视频模型，能力含**首帧生视频 / 首尾帧生视频 / 参考生视频 /
  全模态参考 / 编辑视频 / 延长视频**；分辨率 480p / 720p / 1080p（10bit），**24fps，时长 4~30 秒**，输出 mp4/mov。
  它同样支持"首帧 + 提示词"的 I2VA 思路，与本项目分镜模型能对上。
- 其他第三方聚合视频 API（Kling / Veo / Wan 等聚合服务）——注意这类是转卖，账号与合规风险自负。

## 4 与本项目定位的关系

`docs/POSITIONING.md §4` 红线：**本项目永不直连生图/生视频**，执行侧（L-Port）负责生产。
所以上面的 API 事实是**给执行侧用的情报**，本项目只做两件事：
① 把提示词与交付包做对（含目标引擎格式）；② 把回执登记回来做审计。
真要接 API，接在 L-Port 那一侧，不要接进 SuliAnimeCreator。本项目如需"自动贴稿"，
最多做到**半自动**：生成提示词 → 复制到剪贴板 → 人工在 PixAI 界面粘贴生成。
