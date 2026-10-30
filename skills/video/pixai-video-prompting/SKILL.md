---
name: pixai-video-prompting
description: Write PixAI video-generation prompts (v4.0 Preview / Lite, v3.2, v3.0 HC / Flash, v2.7) for anime image-to-video — reference stacking with @image tags, timed beat structure, camera verbs, voice-line and SFX formats, comic-strip mode, the iteration loop, and the five failure patterns. Use when the target engine is PixAI video / PixAI I2V, or the user names 椿 / Tsubaki 视频 / PixAI 视频模型.
compatibility: Portable — plain local files, no API calls required. Source: PixAI official docs and blog field guide (see PROVENANCE at the end).
---

# PixAI Video Prompting（PixAI 视频生成 canonical）

> 归属：**PixAI 视频的参考图机制 / 时间分块 / 相机动词 / 语音与 SFX 格式 /
> 迭代循环 / 失败模式**以本文件与其 references 为准；
> MiniMax H3 的字段格式仍归 `video/h3-prompt-writing`（两套格式互不通用，交付前先确认目标引擎）；
> 成人向档位与体位/行为词表归 `video/nsfw-directing`（本文件只管 PixAI 侧的格式与参数）。

## 0 命名澄清（查证）

- **Tsubaki / 椿 = PixAI 的图像旗舰模型**（Tsubaki.3 为最新，擅长漫画分页、版面文字、光照叙事、角色一致性）。
- **PixAI 的视频模型是另一条线**。**界面（專業档）已上 `Tsubaki Video` 与 `Tsubaki Video Flash`（标 NEW，
  多图参考 + 支援音讯）**；官方 Oct 6 周报原文提到 "Tsubaki Video animation generation … could fail in some cases"，
  即**确有其物，只是 docs/blog 尚未出专页**（`docs.pixai.art` 无 tsubaki-video 路径）。
  同档还有 `V4.0 Lite Preview`、`V4.0 Preview`、`V3.2`、`V3.0 Lite`、`V2.7`。
- **`Tsubaki Video` 是视频模型（不是图像 Tsubaki 的别名）**：图像线是 Tsubaki.1/.2/.3，
  视频线里的 Tsubaki Video / Flash 是 v4.0 之后的新旗舰档。
- **口径**：官方没出专页 → 按 **v4.0 家族口径**处理（同为多图参考 + 音频），
  **时长档位与模式名以界面为准**（本项目型号表对 Tsubaki Video 取宽松上限 15s，不会误截时长）。
  界面文案若与本文冲突，以界面为准并回写本文件。
- 分工不变：**图像提示词归 `image/production-image-models`，视频提示词归本文件**。
- 官方视频文档：`https://docs.pixai.art/docs/tools/video`；实战教程见 references。

## 0.5 提示词框架通用，但这三项按型号分叉（复核实测）

**同一套框架**（自然语言导演腔 + 时间轴/`[0-Xs]` beat + 真动词运镜 + 台词/SFX 行）在 PixAI 视频全线通用；
但下面三项**必须按型号改**，写错就是白跑：

| 项 | **Tsubaki Video / Flash** | V4.0 Preview / Lite | V3.2 | V3.0 Lite | V2.7 (HD) |
|---|---|---|---|---|---|
| 参考图语义 | **多图参考**（语义锚，同 v4 家族） | **语义锚**（`@image1`，非首帧）；多图+参考视频；Keyframe 与 Multi-Reference **互斥** | 首/尾帧锁帧 | 首/尾帧锁帧 | **仅首帧** |
| 时长上限 | 以界面为准（本项目取 15s 宽松上限） | **15s** | 10s | 10s | 10s |
| 音频 | 支持（Voice 三段式） | 支持（Voice 三段式） | 支持（配音） | **无音频** → 台词改口型提示 | **无音频** → 台词改口型提示 |
| 运镜写法 | 写进提示词 | 写进提示词 | 写进提示词 | 写进提示词 | **用相机下拉，正文不要写运镜** |
| 提示词预算 | **5000 tokens**（界面实测上限）；按 token 写满，不必按字符省 | ≤2000 字符（官方工作流建议） | ≤2000 字符 | ≤2000 字符 | ≤2000 字符 |

项目内已实现：组装时选「型号」，后端自动做型号级校准（时长夹取 / Voice→口型 / 删运镜句），
并在镜卡上显示"调整"提示；交付前对着这张表再核一遍。

## 1 选型（按用途定模型）

| 模型 | 强项 | 时长 | 参考输入 | 备注 |
|---|---|---|---|---|
| `V4.0 Preview` | 旗舰：运动质量/相机控制/一致性最强 | 5-15s | 多图（≤6）+ 参考视频（≤3） | 支持 15s；Multi-Reference 独占 |
| `V4.0 Lite Preview` | 同能力、更便宜 | 5-15s | 同上 | **草稿与迭代首选** |
| `V3.2` | 提示词遵循最好，**唯一支持语音/音效生成** | 5/10s | 首/尾帧 | 有声片、台词片用它 |
| `V3.0 (High Consistency)` | 角色/画风锁得最死 | 5/10s | 首/尾帧 | 配 9 个舞蹈预设；动作偏稳 |
| `V3.0 (Flash)` | 最快最省 | 5/10s | 首/尾帧 | 批量试结构 |
| `V2.7 (High Dynamics)` | 电影感运镜，有独立相机下拉 | 5/10s | 仅首帧 | 大动作、镜头感 |

**迭代循环（官方现场验证过）**：LLM 起草 → **便宜模型试**（v4.0 Lite / v2.7）→ 读失败原因（不是读提示词）→
**v4.0 Preview 出终稿**。同一条提示词，换更强的模型跑终稿。

## 2 参考图机制（最容易搞错的地方）

**v4.0 系列的参考图不是首帧，是"身份语义锚"。** v3.x 及更早把参考图当第一帧锁死，
v4.0 把身份（发色/瞳色/服装/标志配饰）与姿势/环境解耦，动作完全由提示词驱动。

| 你想要 | 用哪个槽 |
|---|---|
| 锁死开场构图与姿势（本项目单图动画的默认） | **Start Frame**（Keyframe 模式） |
| 让角色跑到新场景/新姿势，只保身份 | **@image1 参考图**（Multi-Reference 模式） |
| 借运镜与节奏，不借内容 | `@video1-3`（≤3 段，合计 ≤15s，mp4 ≤50MB） |
| 借音色或音乐气质 | `@audio1-3` |

- **≤6 张图，但 2-3 张最好**：官方实测 4 张比 6 张更锐——每多一张都是对角色长相的又一次投票，模型会平均化。
- **Keyframe 模式与 Multi-Reference 模式互斥**，一次只能选一种。
- 提示词里用 `@image1` `@image2` 指代；角色/场景/服装分图时写清楚谁用哪张：
  `She stands in the scene from @image2, wearing the outfit from @image1.`

**本项目映射**：分镜页的"首帧"两种用法都支持——
① 要构图不变 → Start Frame（Keyframe）；② 只保角色、动作自由 → `@image1` 参考图。交付时标清楚用的哪种。

## 3 提示词结构

### 3.1 分层（官方四层）

`Subject（身份锚，一句带过）+ Motion（动作，灵魂）+ Environment（环境与光）+ Camera（运镜，可选）`

image-to-video 已经有图了，**不要复述画面里已有的细节**（那是"描述"不是"导演"）；
只需一句身份锚帮助模型全程跟住特征：`A white-haired girl with cat ears and violet eyes`。

### 3.2 时间分块（写多镜/多拍时最重要的一条）

两种写法**长得像但含义完全不同**，混用是多镜变幻灯片的头号原因：

```text
[0-1.2s] ...       ← beat 结构：同一镜内的节拍流动（连续长镜用这个）
[Scene 1: 0-3s] ... ← framing 结构：告诉模型在这里切镜（多镜用这个）
```

- 单镜连续（本项目"一镜一段视频"）：用 `[0-<时长>s]` 一条 beat 包住整段，或按节拍拆多条 beat。
- 多镜切：`[Scene 1: 0-3s]` / `[Scene 2: 3-8s]`，每段各自写构图与运镜。
- 每拍只放 **一个主体 + 一个动作 + 一个环境元素**（堆元素 = 视觉噪音）。

### 3.3 写作习惯（官方实测总结）

- **像导演不像小说**：短陈述句，一句一事实。`Hair flutters slightly. Fixed shot. Eyes blink slowly.`
- **用真动词**：`pushes in / pulls back / tilts up / drifts / orbits / pans / dollies`，
  不写 `zoom in`、不写 `the camera moves`。
- **用连接词排序**：`then` / `and`。没有连接词，模型会把一切压成一个静态瞬间。
- **只写会变的东西**：把静止外观的描写句整段删掉，否则出静帧。
- **过渡要给桥**：想要"溶解换场"必须给一个可动画的物理对象（镜子/窗帘/越过画面的花瓣），
  否则一律被当硬切。
- **超现实点明**：出现不合物理的元素要直说 `this is a dream, no physical realism needed`，
  否则模型会自己造水/造地板来圆。

### 3.4 相机动词（照抄）

| 意图 | PixAI 写法 |
|---|---|
| 情绪推进 | `camera slowly pushes in from medium to close-up` |
| 交代环境 | `camera pulls back to reveal the whole room` |
| 横扫 | `camera pans smoothly from left to right across the scene` |
| 自下而上 | `camera tilts up from her feet to her face` |
| 环绕展示 | `camera orbits the subject in a slow clockwise motion` |
| 跟随 | `camera tracks alongside as she walks` |
| 升到大远景 | `camera cranes up from ground level to a high wide view` |
| 滑轨推进 | `smooth dolly shot moving forward while maintaining focus` |

## 4 声音与台词（v3.2 / v4.0 的语音格式）

- **台词三段式**：`音色描述 — 情绪 — 原文（用原语言字符，绝不罗马字）`
  ```text
  Voice — shy, warm and slightly trembling: 「あの……お昼、一緒に行かない？」
  ```
  中日韩都写原文字符（日文用 `「」`）；写成 `Konnichiwa` 这类罗马字，出来是听不清的音频。
- **SFX 用破折号串**：`SFX: heavy rain — thunder rumbling — silence — a single heartbeat`
  （写成一整段描述效果最差）。
- **Add Audio 三档**：`ON`（选语言，台词直接写进提示词框，模型生成配音并同步）/ `SE Only`（只要音效）/
  `OFF`（全静音）。
- 台词要**逐字照抄剧本**——让 AI 转写提示词时它常会悄悄改写，把打磨过的语气弄丢。

## 5 漫画条模式（真正存在的输出模式）

```text
From left to right, top to bottom, present this as a comic strip.
Add special sound effects for scene transitions.
```

多格动态漫画：面板会动、带转场。配合 PixAI Edit Pro 排版 → 导出单张漫画页 → 交给视频模型让它活起来。

## 6 五类失败模式与修法（官方现场统计）

| 症状 | 病因 | 修法 |
|---|---|---|
| 出现参考图里没有的特征（凭空长尾巴/加领结） | 起草的 LLM 自己脑补 | 对着图逐句删掉图里看不见的特征 |
| 出静帧、不动 | 提示词在"描述"而不是"导演" | 删掉描写句，只留会变的东西 + 动词 |
| 画面过载、乱 | 一帧里堆了十几个元素 | 每拍限：一主体 + 一动作 + 一环境元素 |
| 模型自造物理（凭空出现水池） | 没点明超现实 | 直说 `this is a dream, no physical realism needed` |
| 想要溶解却每次都是硬切 | 过渡没给桥 | 给可动画的物理介质（镜子/帘子/花瓣） |

## 7 成人向（NSFW）在 PixAI 侧的口径

- PixAI 视频有**两种内容模式**：`Normal`（**仅 SFW**）与 `Enhanced / Professional`（面向专业创作者，
  **Plus+ 会员**才可用）。也就是说 **PixAI 视频的成人向通道是 Enhanced/Professional，且需要 Plus+ 订阅**；
  Normal 档下投直白内容必然被挡。
- 出稿规矩：**默认只出直白原版**——Enhanced/Professional 通道直接吃露骨描述
  （NovelAI / Tsubaki 同原理）；**只有**明确要走 Normal 档时才补一份按 `video/nsfw-directing` 第 7 节替换表的
  **等长降级版**（同镜号，执行侧挑）。**不要把降级版当默认产物**。
- 露骨词照 `video/nsfw-directing/references/acts-lexicon.md` §9 直白词表写（`penetration / penis / cum / cowgirl position`…），
  不写「结合部 / 亲密」这类回避语——含糊只会让画面收敛成 SFW。
- 参考图本身有内容分级限制：成人向参考图请走 Enhanced/Professional；`V4.0 Preview` 仍是 Preview 模型，
  官方明确写了"部分内容类型暂不支持，跑不出就换素材或改提示词"——被挡时先降级，不要死磕。
- 档位、体位、行为、连续性的写法一律回到 `video/nsfw-directing`（本文件不重复定义）。

## 8 硬限制速查

| 项 | 限制 |
|---|---|
| 单次时长 | v4.0 系列 5-15s；v3.x 与 v2.7 只有 5s / 10s |
| 参考图 | ≤6 张（实测 2-3 张最优） |
| 参考视频 | ≤3 段，单段 ≤50MB / ≤15s，**合计也 ≤15s** |
| 参考音频 | ≤3 段 |
| 模式互斥 | Keyframe（首/尾帧）与 Multi-Reference 互斥 |
| 提示词长度 | **Tsubaki Video / Flash：5000 tokens（操作者核对界面输入上限）**；官方工作流建议的 **≤2000 字符** 仍适用于 v4.0 Preview / Lite 与 v3.x 口径 —— 两套别混用：给 Tsubaki 出稿按 token 预算写满，给 v4.0 出稿仍按 2000 字符收 |
| 会员门槛 | 视频功能需 Starter+（Normal）；Enhanced 需 Plus+ |
| 成本与耗时 | 远高于出图（起步约 16,000 credits），单次 1-5 分钟 |

## 8.5 API 现状（查证，重要）

- **PixAI API 不支持视频生成**——官方 Limits 原文：`Video generation is not supported.`
  所以 Tsubaki Video / Flash **只能走网页/App**，"出稿 → 人工粘贴生成"是目前唯一路径。
- 图片生成 API 可用：`https://api.pixai.art`，`POST /v2/image/create` → `GET /v1/task/{taskId}` → `GET /v1/media/{mediaId}/image`；
  鉴权 `Bearer`；每账号 10 个 waiting 任务；轮询 ≥1.5s；生成媒体不长期保存。
  API 模型白名单目前是 **Tsubaki.2**（不是网页版 Tsubaki.3）。
- 想自动化视频那一步 → 换执行侧（火山方舟 Seedance 系列有首帧/首尾帧生视频 API，24fps、4~30s），
  或等 PixAI 开放。细节见 `references/api-status.md`。

## 9 本项目里的落点

- 导演页组装时可切引擎：`pixai` 出本格式（时间分块 + `@image1` + Voice/SFX），`h3` 出 MiniMax 格式。
- 分镜字段映射：`duty_en` → 动作句；`camera.movement` → 相机动词短语；
  `duration_s` → `[0-Xs]` 时长；`sound` → Voice 行；首帧 → Start Frame 或 `@image1`。
- 出稿后仍走人工审：**读失败、不读提示词**（第 6 节）——先看生成结果差在哪，再改对应那一句。
- 多图参考：分镜 images 里 kind=ref/last 的图（每项可选 role/desc）会按 `@image2` 起排出，
  beat 自动追加 Carry 句；含首帧一镜最多 6 张（2-3 张最优），超了只取前 6 张；
  有额外参考时自动切 Multi-Reference。role 词表：character/outfit/style/face/pose/scene/prop（last 默认 ending）。

## 10 OSS 增补（jnMeta shortfilm-prompts 蒸馏，可直接用）

- 详见 `references/oss-5stage-and-negative.md`；本节只留可执行纪律。
- 5 段顺序不乱：`Core theme | Character & scene | Atmosphere & look | Camera rules | Storyboard`；单镜用 StyleA per-second（Action+Camera+VFX），多镜用 StyleB per-shot（Shot size+Composition+Camera move+Action）。
- 禁词 Rule1：禁 `epic/stunning/perfect/handsome/4K/HD/texture-rich/cinematic/movie-quality`，替换成机身+镜头+物理细节；自检挑 3 个形容词，不能成像就删。
- 机身锚对照：大场 `IMAX + Panavision C-series (35mm, f/4)` / 硬科幻 `Sony Venice + Canon K-35` / Noir `Kodak 35mm bleach-bypass` / 人像 `Canon EF 85mm f/1.2`；动漫转真人预设建议 `ARRI Alexa + vintage primes`。
- 每 beat = Action+Camera+Sound 三行；例 `0-2s hook + 2-8s confrontation + 8-12s cliff`，竖屏加 `faces upper-middle, 9:16`。
- Rule5 ≥2 残缺：每主体至少 2 处不完美锚（matte 磨损/油光/伤痕/线头），治塑料感。
- Rule6 空结尾：末行声明不发生什么，`No dialogue. No explosion. No blinding light. Just {{subject}}{{action}}, {{env}}.`；无 negative 栏模型用此正向护栏代替。
- Negative 路由：有栏（Veo/Kling/Wan/Hailuo）贴 canonical 逗号块不加 no/don't；Runway 禁 `no X`（会招 X）；Seedance 消费端无框则折叠进正向；单 ≤15s、多 ≤8 镜，超了重拆。
- 10 项自检：5 段齐 / 机身镜头 / 呼吸原句 / Sound 原句 / ≥2 残缺 / 空结尾 / 无禁词 / 无 IP 或加警告 / negative 已路由 / 时长镜数合法 / 末尾模型建议行。

## PROVENANCE

来源（全部官方页）：
- `https://docs.pixai.art/docs/tools/video`（核心设置、模型表、运动提示词建议）
- `https://blog.pixai.art/en/how-to-prompt-pixai-v4-0-preview/`（实战教程：参考图机制、时间分块、语音格式、迭代循环、五类失败）
- `https://blog.pixai.art/en/pixai-image-to-video-tutorial-model-guide-prompt-writing/`（六模型对比、面板设置、四层提示词、相机动词表）
- `https://blog.pixai.art/en/tsubaki-3-prompt-guide/`（Tsubaki.3 图像侧提示词，供上游出参考图时用）

配套：`references/model-lineup.md`（模型/设置细节）、`references/v4-preview-field-guide.md`（实战教程全文精编 + 可抄示例）。
