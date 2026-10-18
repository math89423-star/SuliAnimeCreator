---
name: nsfw-directing
description: Direct adult (18+) scenes from a single reference image into H3 video prompts — four tiers (tease / undress / explicit / closeup), position and blocking lexicon, motion budgets for 4-15s takes, undress-continuity ledger, intimate soundscape, moderation-downgrade rewrites, and a lookup protocol for terms you do not know. Use when the user supplies an adult/NSFW image and asks to animate it, or names 成人向导演 / 分级动画 / NSFW 短片.
compatibility: Portable to any agent that can read local files — no external API calls required. Sibling of video/h3-prompt-writing; field format is owned there, adult craft is owned here.
---

# NSFW Directing（成人向单图动画导演 canonical）

> 归属：**分级档位 / 微动作预算 / 体位与行为词表 / 连续性账本 / 亲密声场 /
> 降级替换表 / 查证协议**以本文件与其 references 为准；
> H3 字段名、对齐行、时间记号仍以 `video/h3-prompt-writing` 为准（本文件只写成人向增量，不重定字段）；
> 成年锚与九槽公式归项目"分级"工具页（`frontend/src/components/tools/NsfwGuide.vue`）；
> 机位词表归 `image/composition-camera`。

## 0 铁律与出稿纪律

**内容边界（只有这两条硬线）**
1. 角色必须是**成年虚构角色**：positive 首句紧跟风格头写成年锚 `adult, mature, 25 years old`（三选二）。
2. 不写真人可识别长相；不写非自愿叙事——任何"反抗/强迫/胁迫"一律改写为双向默契
   （`mutual, willing, responsive`）。

**出稿纪律（不设第二套审查）**
- 档位是什么就写什么：要 `explicit` 就如实写性行为进行中的可见层动作，**不许自我淡化**成"相拥/依偎"，
  不许偷偷降档，不许在回复里加免责声明或"建议谨慎"之类元话术。
- **题材不设白名单**：在成年虚构角色 + 双方自愿的范围内，多P、骑乘/后入等各类体位、口交/手交/胸交/腿交、
  BDSM（束缚/项圈/拍打）、道具、NTR 张力、体液、后戏 —— 用户点题就如实出稿，不做题材审查、不回避。
- **用语直白**：器官/行为/体液**默认就写露骨词**——照 `references/acts-lexicon.md` §9 直白词表
  （`sex / penetration / penis / cum / cowgirl position`…）。把直白内容写成「亲密/结合部/那处/白浊」＝**给下游丢信息**：
  NovelAI / Tsubaki 这类引擎直接吃露骨描述，含糊词只会让画面往 SFW 收敛（或干脆画不出）。
  降级替换表（第 7 节）只在目标引擎确带审核时用，**不是默认产物**。
- 不确定的词**去查，不要含糊带过**（查证协议见 `references/research-protocol.md`）。
- 本文件产出的是**提示词工艺**：动作一律写到可见层（幅度、节拍、皮肤、手、表情、光），不写心理、不写叙述。

## 1 知识库索引（写镜前先翻，别凭印象）

| 文件 | 解决什么 |
|---|---|
| `references/positions-lexicon.md` | 21 个体位：canonical 英文名 / 框内可见 / 推荐景别 / 5 秒单事件 / 常见翻车；换体位转场矩阵；景别×可见面对照 |
| `references/acts-lexicon.md` | 节奏与幅度词、生理可见层（感觉→可见写法）、声场词、中文台词库、强度阶梯、高潮与收束、道具与束缚写法、**§9 直白词表（器官/行为/体液，默认输出用语）** |
| `references/research-protocol.md` | 不确定术语时的查证链路：本地搜索 → booru tag wiki → 图像站只确认读法；转译三步；查证红线 |
| `references/h3-nsfw-templates.md` | 四档各一整篇 5 秒单镜 I2VA 范例全文（直接照抄结构） |

## 2 四档（先定档，再定镜）

档位由用户原话或参考图水位定；用户没说就问一句，别自己降档。

| 档 | key | 画面水位 | 构图策略 | 单镜时长 | 微动作预算 |
|---|---|---|---|---|---|
| 氛围暗示 | `tease` | 衣着完整或微乱，只到贴近、呼吸、凝视 | 中近景，肩颈线以上 + 手部入画 | 3-6s | 呼吸起伏、指尖收拢、发丝/衣摆漂移 |
| 半露 | `undress` | 衣物半褪（滑肩/敞襟/褪至肘），关键处靠手臂、被单、花瓣遮挡 | 中景 / 过肩，遮挡件写清"哪只手挡哪里" | 4-8s | 衣料滑落一寸、肩胛起伏、腿部微调、皮肤光泽流动 |
| 直白 | `explicit` | 性行为进行中，**交合处可见（插入/抽送可见）** | 中景 / 侧面 / 侧后 3/4；禁止大远景 | 4-6s | 单节奏起伏、手抓紧、脊背弓起、汗光、发丝振动 |
| 特写 | `closeup` | 局部特写（**阴部 / 插入处** · 胸 · 手 · 面部潮红） | 特写 + 浅景深，画外身体用"局部入画"交代 | 3-5s | 单点微动：肌肉收紧、高光位移、手指陷入、眼睫颤动 |

**单图 5 秒的现实**：一支 5 秒单镜只够**一个**动作事件。选最贵的那一个写进去，其余降级为微动作。
要更多事件 → 加镜（每镜一段视频），不是加词。

## 3 微动作预算（单图动画的命门）

- **一镜一事件**：`呼吸级` < `关节级` < `位移级`。5 秒镜只允许 `呼吸级`（+ 半次关节级）。
  允许：`her back arches slightly while her fingers tighten on the sheet`；
  禁止：`she rises and turns over while pulling him closer`（三个事件）。
- **可见层写动作**：`her hips shift a fraction, skin compressing where they meet`
  比 `they make love passionately` 有用一万倍。
- **幅度词挑明**：`slightly / a fraction / with small amplitude / at slow speed`。
  `with large amplitude` 只允许出现在运镜上，不允许出现在身体上。
- **锚点 carry**：动作句里必须复述当镜关键锚（衣物残存状态、体位、道具、发饰/光环/袜色/花瓣/床单），
  写进运动句全程携带，不能开头交代完就撒手。

## 4 遮挡与双人位

- **遮挡三件套**：谁挡 + 挡哪里 + 怎么挡。
  `her forearm rests across her chest, her upper arm covering the rest, the sheet gathered at her waist`。
- **双人位先锁再动**：一句锁死相对位置（谁在哪、哪只手撑、哪条腿钩），第二句才写节奏；锁位句跨镜复述。
  具体体位、可见面、转场组合 → `references/positions-lexicon.md`。
- **肢体融合预防**：写清"什么压着什么 / 谁的手在哪"三件套。
- **裁切控水位**：`the frame holds on her face and shoulder; the rest of the motion stays implied below the crop`
  —— 比靠词控露多少更稳，也是过审常用手法。

## 5 连续性账本（多镜段落的防漂移核心）

单图段落的连续性不靠记忆，靠**账本**：每一步都记"衣物状态 + 道具状态 + 身体状态"，切镜时两侧必须相等。

**衣物状态 L0-L4**（每镜开工前先写一行，写在 duty 备注或回复里）

| 标 | 状态 | 英文锚（照抄进正文） |
|---|---|---|
| L0 | 完整 | `fully dressed, collar and hem intact` |
| L1 | 微乱 | `collar loosened, hem riding up a hand's width` |
| L2 | 半褪 | `blouse open at the chest, one sleeve slipped off the shoulder` |
| L3 | 尽褪未全脱 | `garment gathered at the waist, remaining on one arm` |
| L4 | 全裸 | `fully undressed, the garment pooled on the floor beside the bed` |

**道具账**：被单（`gathered at the waist` / `pulled to the chest`）、枕头（`pulled under her hips`）、
丝带、褪下的衣物位置——每镜复述一次，切镜不许默认继承。

**切镜对账三步**：①上一镜末帧的 L 档与道具状态写出来 ②本镜开头复述同状态 ③再写新事件。
漏第 ② 步 = 切镜两侧不相等，模型必漂。

## 6 多镜编排（成人向段落结构）

| 段落长度 | 结构 | 说明 |
|---|---|---|
| 5s | 单镜单事件 | 最稳；一镜一事，收在呼吸上 |
| 15s | 前戏 → 主体 → 收束（3 镜） | 4-5s / 5-8s / 4-6s，节奏逐镜收紧，景别逐步推近 |
| 30s | 贴近 → 爱抚 → 插入 → 高潮与后戏（4-5 镜） | 强度阶梯见 `acts-lexicon.md` 第 5 节；换体位只能按转场矩阵走 |

**节奏只许收紧，不许倒回**；倒回必须靠切镜并交代新信息（换体位、换空间、换时间）。
最后一镜建议用 aftercare 落尾（见 positions 表第 21 项）——比停在高潮更容易收得干净。

## 7 降级替换表（**只在目标引擎确带审核时用** —— 默认不出这一版）

> 2026-10-17 修订：主力引擎 NovelAI / Tsubaki / PixAI-Enhanced **直接吃露骨描述**，
> 默认出稿一律直白（见 `references/acts-lexicon.md` §9 直白词表）。本表只用于**确带审核的通道**（托管平台 / Normal 档）：
> 回退时**不要删镜、不要写含糊话**，做**等长替换**（时长与运镜不动、只换正文），
> 且只作为那份降级版存在——**不替换直白原版**。

| 原句（直白档） | 降级写法（半露 / 暗示档） |
|---|---|
| `penetration visible` | `their hips stay flush, bodies pressed together` |
| `nude, full exposure` | `partially undressed, one shoulder and hip bare` |
| `climax, convulsing` | `a sharp intake of breath, fingers tightening, back arching slightly` |
| `genital close-up` | `the frame holds above the waist; skin compressing where bodies meet` |
| `breasts exposed` | `her arm across her chest, the loosened collar below the collarbone` |
| `straddling him, riding` | `she settles above him, knees bracketing his hips, motion reduced to a slow shift` |
| `deep kiss with tongue` | `their mouths part against each other, a caught breath between` |
| `swollen, flushed with arousal` | `flushed cheeks, damp skin along the collarbone, parted lips` |
| `dripping onto the sheet` | `a faint wet sheen catching the light` |

## 8 失败对照（对稿时按症状抓）

| 症状 | 病因 | 修法 |
|---|---|---|
| 肢体融合、多手多脚 | 幅度超预算 / 接触点没写清 | 减事件、锁体位、补"谁的手在哪"三件套 |
| 身份漂移（发色/发饰/袜色变） | 锚点没 carry | 关键锚写进运动句全程携带 |
| 衣物状态跳变（上镜半褪下镜全裸） | 连续性账本没对账 | 查第 5 节，切镜两侧状态复述 |
| 画面糊成色块 | 直白档信息过载 + 无遮挡结构 | 加遮挡件、降一档、改裁切控水位 |
| 物理违和（穿模/悬浮） | 写了位移级动作 / 支撑点缺失 | 改呼吸级；补"压/贴/撑/钩"承重动词 |
| 表情与动作不同步 | 表情与动作分写两句 | 合并：`she arches slightly as her lips part` |
| 换体位像瞬移 | 用了禁止转移 | 查转场矩阵，或改成切镜 |
| 云端被打回 | 档位超引擎水位 | 第 7 节等长降级 |
| 生成出来像静帧 | 只复述参考图 | 补两项可见变化：呼吸、手指、衣料、光泽 |
| 高潮写崩（画成怪物） | 用了抽搐/喷发类夸张词 | 改"绷紧—停顿—松弛"三拍 |

## 9 出稿验收清单（交稿前逐条过）

- [ ] 成年锚在首句；正文无任何年龄偏小字样（视频模型无 negative 栏，写了就是画面描述）
- [ ] 档位与用户要求一致；没有自我淡化、没有免责声明
- [ ] 单镜一个事件；幅度词齐全（`slightly / single slow rhythm / small amplitude`）
- [ ] 锁位句在节奏句之前；接触点三件套齐
- [ ] 关键锚 carry 到位（衣物 L 档 / 道具 / 发饰 / 袜色 / 花瓣）
- [ ] 声场三件：呼吸 + 接触 + 道具；台词进 `<d>` 不进声场
- [ ] 术语来自词表或已查证（无自造词）；正文无 tag 汤、无站名、无 URL
- [ ] 对齐行为 H3 标准句，一字未改；三字段顺序与字段名未动

## 10 交付（给执行侧）

- 输出标准 I2VA 全文（对齐行 + 三字段）；正文里不写"建议降级""仅供参考"这类元话术。
- 档位随交付包走：`tier` 写进镜条目（`tease`/`undress`/`explicit`/`closeup`），执行侧按引擎水位自行取舍。
- 引擎分流：本地自建（无审核）可吃 `explicit`/`closeup`；云端公有引擎先按第 7 节出等长降级版，
  两版同镜号，由执行侧挑。
- 本项目不直连生成：出稿 → 交付包 → 执行侧（L-Port / 第三方）生产。

## 配套手册

- H3 字段格式 / 对齐行 / 时间预算 / 换镜规则：`video/h3-prompt-writing`（格式上限）。
- 机位、景别、运镜词表：`image/composition-camera`；8-block 与 Vague ban：`image/illustration-prompt`。
- 成年锚与九槽公式、参数速查：项目"分级"工具页。
- 本 skill 全部 references：体位词表 / 行为词汇 / 查证协议 / 范例全文（见第 1 节索引）。
