# SuliAnimeCreator × L-Port 职责对齐

> 一句话：SuliAnimeCreator 负责**起草方案与敲定方向**（做规划），L-Port 负责**创意发散与自评审迭代**，
> **最终成品保存在 L-Port 内**。暂且由人工手动搬运成果，两边互通以后再打通。
> A 向（审计/执行大方向）仍然有效。

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
| 角色 | `character.md` + `character_doc.html` + `ref_image/` + `character.json` + `slot_images/` + `slot_images.json` | md：`# 名 设定` + 四维（hairstyle/face/physique/identity，`GET /v1/characters/<id>/pack` 现成形状）；doc：角色页"文档交付" tab 的设计文档原文（有才有）；ref_image/：avatar 主图原文件；slot_images/：18 槽位 kind|slot 各最新一张 + json 索引（kind/slot/note）；json：机器字段（anchors/服装/各引擎槽位提示词） | `ref_images` 人物参照 + premise 人物描述 |
| 故事剧本 | `screenplay_draft.md` + `outline.md` + `beats.json` + `episode_refs/` + `episode_refs.json` | md：场景+动作+对白（scriptboard 的 screenplay_md）；outline：方案大纲（方向一句话/基调档位/分镜大纲表/合计，`GET /v1/scriptboard/outline/<集号>` 存取，进包）；beats 用 `[{beat_id, function, text_cn}]`（对齐它 beats_json）；episode_refs/：剧本参考图原文件 + json 索引（role/desc 模仿说明） | 产出 `script_md` 发散成稿 + `premise_cn`，存它那边 |
| 分镜 | `shots.json` + `images/` | `[{shot_id, duty_cn, duration_s, crop, sound_cn, key_text_en, tier, ref_roles, gen_mode, gen_mode_eff, ref_mode}]`（前 6 键对齐它 shots_json；`gen_mode` 是本项目定的意图，`gen_mode_eff`/`ref_mode` 是按型号能力结算后的结果，见下）；images/：首帧+尾帧+参考图文件 | 产出 shots_json 成稿，存它那边 |
| 提示词 | `prompts/<shot_id>.<engine>.txt` + `prompts.json` | txt：粘贴即用全文（pixai/h3 分引擎）；json：机器字段（engine/video_model/ref_mode/duration/tier/refs） | Translator 译参，或人工粘贴（PixAI 无视频 API，只能人贴） |

命名纪律：我们给的带 `_draft`（草案），它产出的无后缀（成稿），后缀即方向标记。
生成方式归属：一个 seg 用纯文本还是首帧/首尾帧/多图参考，**由 Suli 定，按 seg 生效，L-Port 只做能力校验**。

- 镜级 `gen_mode` 四值（意图，存的是选择不是结算值）：`t2v` 纯文本 / `i2v-first` 首帧锁构图 /
  `i2v-first-last` 首尾帧 / `multi-ref` 多图只锚身份。没标时按素材推断（首+尾→首尾帧，
  首+其它图→多图参考，只有首→首帧，只有参考图→多图参考，无图→纯文本）。
- 结算成 `ref_mode` 三值：`t2v` / `startframe` / `reference`。降级只降不改方案，降级原因写进 `ref_note`：
  v3.x/v2.7 只认首帧、v2.7 不认尾帧、缺首帧退纯文本、缺尾帧退首帧。
- 出包时 `ref_mode_default` 记页面请求值，每镜 `gen_mode` 记意图、`gen_mode_eff` + `ref_mode` 记结算值；
  L-Port 换型号时按镜上的 `gen_mode` 重新结算（不照抄 Suli 的 `ref_mode`），留痕上报，不得静默改判。
包装：一次搬运一个以 `package_id` 命名的文件夹 + `manifest.json`（文件清单 + sha256 + 版本 + 方向说明 + 档位）；
export 接口吐的 `/api/images/<名>` 只是 URL（过不了界，仅对账用），`images/` 文件夹必须一起拷走。

三层包：**P0 方案包**（Suli→L-Port：brief + 上面四类草案）→ **P1 发散包**（L-Port 自产自销：premise_cn/beats_json/script_md/shots_json，存它那边）
→ **P2 执行包**（定稿后：frozen shots + prompts + 媒体）。P2 有两种来源：L-Port 自己迭代到终稿的，P2 为其内部流转，
本项目只留方向批准记录；本项目定的终稿（小改、NSFW 专项、PixAI 手工粘贴），P2 由本项目出。

**回程·执行回执**（L-Port → Suli，暂由人工搬运登记，本项目登记口不变）：

```json
POST /v1/receipts {"package_id": "..", "shot_id": "..", "task_id": "..",
  "engine": "comfyui|cloud", "provider": "flux|gpt_image|..",
  "media_url": "..", "status": "done|failed", "log_tail": "..",
  "project_id": "PRJ-XXXXXX", "episode_id": "EP-XXXXXX"}
```

新建回执默认必须可归位：`episode_id` 可显式传入，或从 `package_id/media_url/task_id/shot_id`
推断；`project_id` 可显式传入，或按集号归属解析。归属冲突、未知项目或未知集号会
被拒绝（`allow_unscoped=true` 仅用于确实无法归位的例外登记）。
导出包会把当前项目写入 `manifest.json`，并附带同项目同集回执快照
`receipts.json`。

回执只存**事实**供审计（哪镜、何时、用什么引擎出了什么图），不触发重生成。
成品本体留在 L-Port，本项目只存回执指针；视频回执扩展字段（video_model/ref_mode/duration_s/refs_used）见组装层返回。

**远期互通目标**（未建）：方案包直传、成品与回执自动回流、媒体 sha 对账自动化。
互通建成前，人工搬运只做复制：sha 对不上→停手上报，不猜不补。

### 草案直投（去程自动、回程轮询）

导演草案页「直投 L-Port」调 `POST /v1/director/push-lport`
（body：`episode_id` + 可选 `project_id/character_id/engine/pixai_model/tier/ref_mode/note`，
与导出包同口径、归属冲突同样 409）：
后端用同一份构建函数出包，写进 L-Port 收件箱 `suli_packages/<package_id>/`
（含 `<包>.zip` + `manifest.json` + `package.json`，后者即 story_text 插件输入口径
`package_id/episode/shots/locks`），推送记录落 `director_push_db.json`。
收件箱与投流 `packages/` 隔离：导演 ZIP 不进投流包列表。
前端拿到 `package_id` 后每 5s 轮询 `GET /v1/receipts?package_id=..`（10 分钟上限），
回执一到即提示并可一键跳回执页（回执面板按 `refreshKey` 自动重刷）。
多包并行：投递记录是数组（`suli.director.pushes`），一个轮询同时跟所有包，
本集只显示本集的行、他集记一行提示，互不覆盖；刷新/切页回来自动续等。
L-Port 侧仍需人工一步：在 story_text 插件载入 `package.json` 跑完分镜后，
调 `push-shots-to-suli` 回写分镜并在本项目登记回执（带该 `package_id`）。

### 详细提示词回传（L-Port 细化产物回流）

story_text 回写分镜之后，L-Port 文本工作区再点「写详细提示词并回传」：
跑 `seg_prompt`（一镜一 seg，中文导演式提示词 + 相机句 + 英文关键帧句）→
`POST /api/pipeline/push-prompts-to-suli`
（body：`episode_id` + `prompts[]` + 可选 `package_id/source`；代理层轻转后转发）→
本项目 `POST /api/v1/scriptboard/shots/prompts/import` 逐镜写进 `shot.lport_prompts`
（`source/package_id/at` + `director_cn/camera_note/key_text_en/dialogue_cn/ref_status/ref_missing`）。

规则：只写已存在的镜，缺镜回报 `missing` 不造镜（造镜归 `shots/import`）；空提示词条目不落
（防假回执）；同一镜重传即覆盖（当前版本语义）。
查看口：导演页「提示词」页签（逐镜复制 / 复制全部）+ 草案页分镜卡内嵌块。

### 单图创作（art plan：方案在 Suli，发散翻译精修在 L-Port）

Suli 「单图创作」页（`/studio`）起草单图方案：意图文本 + 目标引擎（可多选）+ 可选参考图（≤6）+
改图指令；「与 agent 讨论方案」走本仓 dsh（agent 定稿后调 `POST /api/v1/art/plans` 落库）。
「直投 L-Port」写进同一收件箱 `suli_packages/<pkg_id>/`（`art_plan.json` + `manifest.json` + 参考图 zip），
包型 `kind: "art_plan"`（口径：`plan_id/title/intent_text/engines/reference_images/user_image_instruction`）。

L-Port 「单图方案」页（`/art-plan`）列出收件箱方案，一键跑链：
`intent_divergence`（意图 → 全景视觉叙事）→ `intent_blueprint`（→ 15 维 SlimBlueprintIR）
→ `blueprint_to_<引擎>`（anima / novelai / seedream / gpt_image / flux / sdxl / pony / cloud）。
参考图由 L-Port 从包里解到本地后喂 `intent_divergence`（走 VLM 看图，仅一张）。

回程：`POST /api/pipeline/push-art-prompts-to-suli`（代理层轻转）→ 本项目
`POST /api/v1/art/prompts/import` 逐引擎写进方案 `prompts`
（`source/package_id/at` + `positive/negative/params/note`，另可带 `blueprint`）。

规则：只认已存在的方案（`plan_id`/`package_id` 归位，不新建，防假回执）；空正文条目不落；
同一引擎重传即覆盖（当前版本语义）；引擎没有对应蓝图翻译器时 L-Port 跳过并回报 `skipped`。
查看口：Suli 单图创作页右侧（逐家复制 / 复制全部）。方案数据落 `backend/data/art_db.json`。

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
