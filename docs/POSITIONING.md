# SuliAnimeCreator × L-Port 职责对齐（2026-10-11，YG 已裁：构想归 animecreator，A向胜）

> 一句话：SuliAnimeCreator 是**审计侧**（出构想、定规划、存定稿**与执行结果**、做审计），L-Port 是**执行侧**
> （拿交付包去生产）。两边只靠交付包与回执单说话，不共享 DB、不共享进程。
> 2026-10-11 会谈室裁定：A向胜，§2 原向有效；§1 修订为含执行结果存放（YG 口径：AnimeCreator 存放 l-port 产出的结果并规划后续）。call-YG 已关闭。

## 1. 各管什么

| SuliAnimeCreator（本项目） | L-Port（执行项目） |
|---|---|
| 构想与规划（故事/角色/剧本/分镜），可改可迭代 | 不原创构想，只译包生产 |
| 评审门与人工拍板（PASS→APPROVE） | 不做评审；按蓝图执行，模糊处停机上报（其 CLAUDE.md §0） |
| **定稿冻结**：版本 freeze、交付包快照、锁面 | 不冻结；执行时发现定稿问题→停手上报，不自行改语义 |
| **存放执行结果**：媒体、task单、日志回执入库并审计 | 产出媒体/task单/日志，交回执 |
| **审计与后续规划**：谁何时拍了什么、哪镜对应哪次执行、下集/下镜 brief | 提供执行事实（task id、引擎、媒体 URL、日志） |
| dsh 规划/评审 agent（suggest→confirm→review，禁直连生成） | 自家 Full/Lite 执行 Agent（22+22+12 工具） |
| 不轮询任务、不存生成 key（执行结果入库见§1存放行） | 存媒体（时光画廊）、单机串行执行（MySQL）、管 key |

## 2. 接口（两份文档）

**去程·交付包**（Suli → L-Port，本项目 `GET /v1/director/export` 扩展）：

```json
{
  "package_id": "PKG-EP001-20261011-01",
  "episode_id": "EP-xxx", "verdict": "APPROVE",
  "shots": [{"id": "SHOT-..", "assembled_en": "..≤150词", "locks_hit": ["LOCK-.."],
             "visual_basis": ["视觉设定·道具「取衣牌」"], "camera": {}, "boundaries": {}}],
  "locks": [{"id": "LOCK-..", "surface_en": ".."}],
  "review": {"verdict": "APPROVE", "findings": []}
}
```

L-Port 侧由 Translator 节点译成自家 `param_schemas.fields`
（`engine_type/provider/inject[{node_id,field}]`，见其 `models/param_schema.py`）——
翻译是执行侧的事，本项目只保证英文正文+锁面+依据三件齐。

**回程·执行回执**（L-Port → Suli，本项目新增登记口）：

```json
POST /v1/receipts {"package_id": "..", "shot_id": "..", "task_id": "..",
  "engine": "comfyui|cloud", "provider": "flux|gpt_image|..",
  "media_url": "..", "status": "done|failed", "log_tail": ".."}
```

回执只存**事实**供审计（哪镜、何时、用什么引擎出了什么图），不触发重生成。

## 3. 本项目要改的（后续任务池）

1. 定稿冻结：episode/verdict 级 freeze + 交付包快照（含版本号，不可改）。
2. 交付包 export 对齐 §2 去程格式（含锁面与三条依据）。
3. 执行回执登记口 + 回执列表页（审计视图）。
4. 状态机：draft → PASS → APPROVE → RELEASED（已交付）→ EXECUTED（有回执）。
5. dsh agent 保持规划/评审定位：禁 `/generate /jobs` 类动作（已有 FORBIDDEN_KEYS 思想）。

## 4. 不碰的红线

- 本项目永不直连生图/生视频；L-Port 永不改定稿语义与锁面。
- 跨项目只走上述两份 JSON，不共享 DB、不共享文件路径、不共享 key。
