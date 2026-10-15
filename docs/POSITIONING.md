# SuliAnimeCreator × L-Port 职责对齐（2026-10-12 修订，YG 裁定）

> 一句话：SuliAnimeCreator 负责**起草方案与敲定方向**（做规划），L-Port 负责**创意发散与自评审迭代**，
> **最终成品保存在 L-Port 内**。暂且由人工手动搬运成果，两边互通以后再打通。
> 2026-10-12 YG 裁定替代 2026-10-11 版 §1 分工表；A向（审计/执行大方向）仍然有效。call-YG 已关闭。

## 1. 各管什么

| SuliAnimeCreator（本项目） | L-Port（执行项目） |
|---|---|
| 起草方案：故事/角色/剧本/分镜的方案稿，可改可迭代 | 创意发散与自评审迭代：在方向内展开、自我评审、迭代到成品 |
| 敲定方向：做什么、什么档、什么约束；方向拍板与方向变更唯一出口 | 不改方向；迭代中需变方向→停手，方向打回 Suli 重定 |
| 出分镜与提示词：duty/duty_en、档位、运镜、时长、引擎格式 | 按方案与提示词生产（ComfyUI/云引擎） |
| craft 知识 owner：skills/tiers/词表在本项目编写与版本管理 | craft 只读（缺东西→上报 Suli 修，不自行改） |
| 存方案与方向定稿；执行回执登记备查（事实指针，不存成品本体） | **存最终成品**：媒体、task单、日志全量入库 |
| dsh 规划 agent（出方案、定方向，禁直连生成） | 自家 Full/Lite Agent（发散、迭代、执行，22+22+12 工具） |
| 不直连生成、不存生成 key、不建成品库 | 管 key、管队列、管重试、管媒体库（时光画廊）、单机串行执行（MySQL） |
| 人工搬运（暂行）：把方案送过去，把成品回执登记拿回来 | 配合搬运：成品按约定结构存放，搬运只读不改 |

## 2. 接口（暂行人工搬运 + 远期互通）

**去程·交付包**（Suli → L-Port，暂由人工搬运；本项目 `GET /v1/director/export` 扩展）：

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

### 草案形态（四类资产，文件名即规范）

L-Port `story_text` 插件输入已写明"接 Suli 交付包：`package_json` → 三文本产出包"，
吃的键是 `package_id/episode/shots/locks`，另有 `premise_text`、`ref_images`（上限 6，只看不改）、`edit_image`。
本项目给的 JSON 键名照抄它能直接吃的形状：

| 资产 | 文件 | 内容/形状 | L-Port 用途 |
|---|---|---|---|
| 角色 | `character.md` + `character_doc.html` + `ref_image/` + `character.json` | md：`# 名 设定` + 四维（hairstyle/face/physique/identity，`GET /v1/characters/<id>/pack` 现成形状）；doc：角色页"文档交付" tab 的设计文档原文（有才有）；ref_image/：avatar 主图 + slot 图原文件；json：机器字段（anchors/服装/各引擎槽位提示词） | `ref_images` 人物参照 + premise 人物描述 |
| 故事剧本 | `screenplay_draft.md` + `outline.md` + `beats.json` | md：场景+动作+对白（scriptboard 的 screenplay_md）；outline：方案大纲（方向一句话/基调档位/分镜大纲表/合计，`GET /v1/scriptboard/outline/<集号>` 存取，进包）；beats 用 `[{beat_id, function, text_cn}]`（对齐它 beats_json） | 产出 `script_md` 发散成稿 + `premise_cn`，存它那边 |
| 分镜 | `shots.json` + `images/` | `[{shot_id, duty_cn, duration_s, crop, sound_cn, key_text_en, tier, ref_roles}]`（前 6 键对齐它 shots_json）；images/：首帧+参考图文件 | 产出 shots_json 成稿，存它那边 |
| 提示词 | `prompts/<shot_id>.<engine>.txt` + `prompts.json` | txt：粘贴即用全文（pixai/h3 分引擎）；json：机器字段（engine/video_model/ref_mode/duration/tier/refs） | Translator 译参，或人工粘贴（PixAI 无视频 API，只能人贴） |

命名纪律：我们给的带 `_draft`（草案），它产出的无后缀（成稿），后缀即方向标记。
包装：一次搬运一个以 `package_id` 命名的文件夹 + `manifest.json`（文件清单 + sha256 + 版本 + 方向说明 + 档位）；
export 接口吐的 `/api/images/<名>` 只是 URL（过不了界，仅对账用），`images/` 文件夹必须一起拷走。

三层包：**P0 方案包**（Suli→L-Port：brief + 上面四类草案）→ **P1 发散包**（L-Port 自产自销：premise_cn/beats_json/script_md/shots_json，存它那边）
→ **P2 执行包**（定稿后：frozen shots + prompts + 媒体）。P2 有两种来源：L-Port 自己迭代到终稿的，P2 为其内部流转，
本项目只留方向批准记录；本项目定的终稿（小改、NSFW 专项、PixAI 手工粘贴），P2 由本项目出。

**回程·执行回执**（L-Port → Suli，暂由人工搬运登记，本项目登记口不变）：

```json
POST /v1/receipts {"package_id": "..", "shot_id": "..", "task_id": "..",
  "engine": "comfyui|cloud", "provider": "flux|gpt_image|..",
  "media_url": "..", "status": "done|failed", "log_tail": ".."}
```

回执只存**事实**供审计（哪镜、何时、用什么引擎出了什么图），不触发重生成。
成品本体留在 L-Port，本项目只存回执指针；视频回执扩展字段（video_model/ref_mode/duration_s/refs_used）见组装层返回。

**远期互通 TODO**（现在不建）：方案包直传、成品与回执自动回流、媒体 sha 对账自动化。
互通建成前，人工搬运只做复制：sha 对不上→停手上报，不猜不补。

## 3. 本项目要改的（后续任务池）

1. 方案包格式冻结：episode/方向级 freeze + 交付包快照（含版本号，不可改）。
2. 交付包 export 对齐 §2 去程格式（含锁面与依据；视频块 engine/video_model/ref_mode/duration/tier/refs 见组装层）。
3. 执行回执登记口 + 回执列表页（登记人工搬运回来的执行事实）。
4. 状态机：draft → 方向敲定 → 已交付（人工） → 已登记（有回执）。
5. dsh agent 保持规划定位：出方案、定方向，禁 `/generate /jobs` 类动作（已有 FORBIDDEN_KEYS 思想）。

## 4. 不碰的红线

- 本项目永不直连生图/生视频，不存生成 key，不建成品库（成品唯一真源在 L-Port）。
- L-Port 不改方向：迭代只能在方向内；方向变更必须回 Suli；定稿语义与锁面不动。
- 跨项目只走上述两份 JSON（暂行人工搬运），不共享 DB、不共享文件路径、不共享 key。
- craft 缺东西→上报 Suli 修；L-Port 不自行改 skill/词表/档位定义。
