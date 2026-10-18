# 行为 · 节奏 · 声音 · 台词词表（成人向 I2VA canonical）

> 用途：体位定了之后，这一本解决"动作怎么写"。核心原则不变：
> **写到可见层**——画面里看得见什么（幅度、节拍、皮肤、手、表情、光），不写心理、不写叙述。
> 中文用在看板与台词，**英文正文用右列 canonical 词**，不现造。

---

## 1 节奏与幅度（动作句的骨架）

一个动作句 = 节奏词 + 幅度词 + 接触面 + 反应。四件缺一就容易糊。

| 中文 | EN canonical | 用法提示 |
|---|---|---|
| 缓慢的一次 | `in a single slow rhythm` | 5 秒镜的默认节拍 |
| 深一次 | `one deeper stroke` | 单事件镜的"事件"本身 |
| 浅而快 | `short quick strokes` | 只给 8 秒以上镜 |
| 前后摆 | `rolls her hips` / `rocks` | 骑乘、对坐类 |
| 推进 | `pushes in` / `thrusts` | 后入、俯卧类 |
| 磨动 | `grinds` | 贴身摩擦类 |
| 收紧 | `tightens around him` | 接近高潮用，配呼吸描写 |
| 停住 | `holds still, deep` | 比加动作更高级的写法，收束前用 |
| 加速 | `quicken` / `stutters` | 只给结尾 1 秒 |
| 拔离 | `withdraws slowly` | 换动作/换体位的前置 |
| 幅度小 | `with small amplitude` | 成人向默认 |
| 幅度大 | `with large amplitude` | 只允许出现在运镜，不允许出现在身体 |

**句式定式（直接抄）**：

```text
their bodies stay pressed flush and move together in a single slow rhythm, skin compressing where they meet
```

## 2 生理可见层（"感觉"怎么写才看得见）

| 中文感觉 | 可见层英文写法 |
|---|---|
| 兴奋 | `a flush spreading across her cheeks and chest` |
| 汗 | `a fine sheen of sweat along her collarbone and shoulder blade` |
| 湿 | `skin glistening where they meet` |
| 发抖 | `a small tremor running through her thigh` |
| 失神 | `her eyes half-lidded, unfocused` |
| 呼吸困难 | `her breath catching in short, uneven pulls` |
| 抓紧 | `her fingers tightening on his forearm, knuckles paling` |
| 蜷趾 | `her toes curling against the sheet` |
| 弓背 | `her back arching slightly, shoulder blades lifting` |
| 咬唇 | `she bites down on her lower lip` |
| 泪光（情绪外化） | `eyes glistening, a single tear tracking down her cheek` |
| 高潮 | `her whole body holding taut for a beat before easing` |
| 余韵 | `short, slowing breaths as her grip loosens` |
| 体液（含蓄版） | `a faint wet sheen, catching the light` |
| 体液（直白版） | `dripping onto the sheet below` |

**用语纪律（2026-10-17 修订）**：**默认输出一律用直白版**（器官/行为/体液按 §9 直白词表写）；
含蓄版**只在**目标引擎确带审核时当降级替换用（见 `SKILL.md` 第 7 节）。把直白内容写成含蓄词＝给下游丢信息。

## 3 声音（`overall_soundscape` 专用词）

- 呼吸：`slow breathing` / `ragged breath` / `breathless exhale` / `a sharp intake of breath`
- 人声：`a low, throaty moan` / `breathy whimper` / `a stuttered gasp` / `soft humming sigh`
- 接触：`damp skin contact` / `a soft slap of skin` / `wet friction`
- 道具/环境：`fabric drag against the sheet` / `a faint creak from the bed frame` / `a headboard tapping the wall`
- 组合定式（4 句写法，抄）：

```text
overall_soundscape: Close breathing overlaps in a slow rhythm, joined by fabric drag against the sheet and a faint creak from the bed frame. Toward the end her breath shortens into a stuttered gasp.
```

**规矩**：声场里写进"呼吸/接触/道具"三件就够；台词不进声场（台词归 imm 的 `<d>` 块）；不写抽象情绪词。

## 4 台词库（中文原文进 `<d>[Chinese] …</d>`）

台词是亲密戏的信息密度最高的地方：一句气声台词能替代三个动作。
写时给说话人 `(S1)`，语气词写在外面（`in a breathy whisper`），原文原标点照抄。

| 类别 | 台词例 | 外部语气词 |
|---|---|---|
| 断续 | 别停… / 慢、慢一点 / 嗯…那里 | `in a breathy whisper` / `voice breaking` |
| 指挥 | 轻一点 / 抱紧我 / 看着我 | `her voice low and unsteady` |
| 亲密 | 你的名字 / 我一直在想这一刻 | `murmured against his ear` |
| 临界 | 我快不行了 / 别动…就这样 | `a stuttered gasp` |
| 后戏 | 别走 / 再躺一会儿 | `short of breath, half-laughing` |
| 无声 | （只有呼吸）→ sound 留空，由声场承接 | — |

**避雷**：不写长篇对白（5 秒塞不下）；不写解释性台词（"我们这样是不是…"）；不写旁白/心声——H3 没有内心戏通道。

## 5 强度阶梯（30 秒段落的四步爬升）

按"贴近 → 爱抚 → 插入 → 高潮与后戏"分四步，每步给一个镜，节奏逐步收紧、景别逐步推近：

| 步 | 时长 | 景别 | 事件 | 声音密度 |
|---|---|---|---|---|
| 贴近 | 4-5s | medium / 中近 | 一次贴近或一次接吻 | 呼吸 + 衣料 |
| 爱抚 | 5-6s | medium close | 一次单点动作（手/口/摩擦） | 呼吸 + 皮肤接触 |
| 插入 | 5-8s | medium / close | 一次插入或一次深推进 | 加床架/水声 |
| 高潮·收束 | 4-6s | medium close → medium | 绷紧一次 + 松弛（后戏） | 呼吸断续 → 放慢 |

**规矩**：节奏只能"逐镜收紧"，不许倒回去；倒回去必须靠切镜并交代新信息（如换体位、换空间）。

## 6 高潮与收束（最容易写坏的两处）

- **高潮**：写"绷紧—停顿—松弛"三拍，不要写抽搐/喷发这类夸张词（模型画成怪物）。
  推荐：`her body holds taut for a beat, then eases with a long exhale`。
- **收束**：最后一镜降速到呼吸级，用 aftercare 体位（见 positions 表第 21 项）落尾。
- **忌**：结尾仍在高速运动（糊帧）、结尾切黑（用户没要求就不切）、结尾加字幕/水印。

## 7 道具与辅助元素

- 常用：`the gathered sheet` / `a pillow pulled under her hips` / `a loosened ribbon` / `one strap slipped off the shoulder`
- 规矩：道具必须**写进运动句 carry**（`she pulls the sheet up to her chest while her breath slows`），
  否则模型会中途丢掉它。
- 束缚类（BDSM 档）：写清材质与受力（`silk ribbon looped around her wrists, tied to the headboard, wrists raised`），
  并写 `loose enough to slip` 之类可解状态；不写疼痛/伤痕细节（模型画成伤检图）。

**道具与玩法的 canonical 名**（tag 轨用；证据与别名见 `references/kb/play.md`）：

| 中文 | canonical tag | 热度 | 边界 |
|---|---|---|---|
| 项圈 / 牵绳 | `collar` / `leash` | — / — | 支配关系的可见符号；写松紧与走向，不写勒痕 |
| 绳缚 / 股绳 | `shibari` / `crotch_rope` | 25k / — | 只写可解状态；不写疼痛 |
| 性玩具 / 震动器 / 假阳具 | `sex_toy` / `vibrator` / `dildo` | 76k / 33k / 32k | 写出具体是哪一件，别只写"玩具" |
| 肛珠 / 飞机杯 | `anal_beads` / `onahole` | — / — | `object_insertion`（38k）慎用，优先具体玩具 |
| 露出 / 公共场合 | `exhibitionism` / `public_sex` | 11k / — | 参与者自愿；靠环境线索表达"有人可能看到" |
| 多人：3P / 群交 / 串刺 | `threesome` / `group_sex` / `spitroast` | 45k / 84k / 7k | **只写知情合意**；`gangbang`（25k）的 wiki 别称含贬义措辞，**本仓禁用该措辞**，写"多人轮替" |
| NTR 张力 | `netorare` | — | 只写张力与关系，不写胁迫、不写背叛过程 |

## 8 中→英转译三步（不确定时照这个走）

1. 中文口语（"后入"）→ 查 `positions-lexicon.md` 拿 canonical 名（`doggystyle`）。
2. canonical 名不确定定义 → 按 `research-protocol.md` 查 booru tag wiki（拿精确定义与别称）。
3. 转成 H3 自然语言句：**不写 tag 汤**，写成"锁位 + 接触点 + 单事件 + 反应"的一段。

例（后入 5 秒单镜）：

```text
He is positioned behind her as she kneels with both forearms braced on the mattress; his right hand holds her hip.
The camera holds a static shot as they move together in a single slow rhythm, skin compressing where they meet,
her fingers curling into the sheet as her back arches slightly.
```

## 9 直白词表（器官 / 行为 / 体液 —— **默认输出用语**）

> **这是默认用语，不是备选**（2026-10-17 修订）：拆解报告、镜头卡、提示词正文一律用这里的词。
> 把「性交/插入/阴茎/精液」写成「亲密/结合部/白浊」= 给下游丢信息——NovelAI / Tsubaki 这类引擎**直接吃露骨词**，
> 含糊词只会让画面收敛成 SFW（或干脆画不出）。
> 含蓄说法**只**活在 `SKILL.md` 第 7 节降级替换表里，且仅在目标引擎确带审核时才用（如 Seedream 托管侧）。

### 9.1 器官

| 中文 | EN canonical | 备注 |
|---|---|---|
| 阴茎 | `penis` / `cock` | tag 轨用 `penis`；自然语言直白档可 `cock` |
| 龟头 | `glans` | 特写镜用 |
| 阴囊 | `testicles` / `balls` | |
| 阴部 / 外阴 | `pussy` / `vulva` | tag 轨 `pussy`、`pussy lips` |
| 阴道 | `vagina` | 与 `penetration` 搭配 |
| 阴蒂 | `clitoris` | |
| 小 / 大阴唇 | `inner labia` / `outer labia` | |
| 乳头 / 乳首 | `nipples` / `areola` | |
| 乳房 | `breasts` | 大小另加 `large breasts` 等 |
| 臀 / 屁股 | `ass` / `buttocks` | tag 轨 `ass` |
| 精液 | `cum` / `semen` | tag 轨首选 `cum` |
| 前列腺液 | `precum` | |
| 爱液 / 淫水 | `pussy juice` / `love juice` / `wetness` | |

### 9.2 行为

| 中文 | EN canonical | 备注 |
|---|---|---|
| 性交 / 做爱 | `sex` / `fucking` / `intercourse` | tag 轨 `sex`；正文动词 `fucking` |
| 插入 | `penetration` / `insertion` | ⚠️ `penetration` 是**歧义 tag**：物体插入用 `object_insertion`、阴茎插入用 `sex` / `vaginal` |
| 抽送 | `thrusting` | |
| 骑乘位 | `cowgirl_position` | canonical 名见 `positions-lexicon.md` §1.1 |
| 后入 | `doggystyle` / `sex_from_behind` | 后者是后位总称 |
| 传教士 | `missionary` | |
| 对坐 / 面对面 | `upright_straddle` / `face-to-face` | `lotus` 是**荷花**、`sitting_sex` 不存在——别用 |
| 侧位 | `spooning` | |
| 口交 | `fellatio` / `blowjob` | tag 轨 `fellatio`；被主动挺入用 `irrumatio` |
| 深喉 | `deepthroat` | |
| 乳交 | `paizuri` / `titfuck` | tag 轨 `paizuri` |
| 手交 / 指交 | `handjob` / `fingering` | 手指入内用 `fingering` |
| 素股 / 腿交 | `thigh_sex` / `sumata` | `sumata` **不是 booru tag**（404），tag 轨用 `thigh_sex` |
| 内射 | `cum_in_pussy` / `creampie` | tag 轨 `cum_in_pussy`；拔后外流 `cumdrip`、体内溢出 `cum_overflow`（互斥） |
| 颜射 / 体外 | `facial` / `cum on face` / `cum on body` | |
| 潮吹 | `squirting` | |
| 掰开 | `spreading`（`spreading pussy`） | |
| 握持 | `holding his cock` / `jerking him off` | |

### 9.3 体液与状态

| 中文 | EN canonical | 备注 |
|---|---|---|
| 湿 / 润 | `wet` / `slick` | |
| 拉丝 | `strings of fluid` | |
| 滴落 | `dripping` | |
| 白浊 | `thick white cum` | 中文可写白浊，**英文必须落到 `cum`**；不写 `white fluid` 这类谜语 |
| 精液顺腿流下 | `cum dripping down her thigh` | |
| 收缩 / 绞紧 | `clenching` / `squeezing around him` | |
| 痉挛 / 颤抖 | `spasms` / `twitching` | |
| 绯红 / 潮红 | `flushed` / `blushing` | |

### 9.4 使用纪律

- **中文看板（duty）也直白**：写「骑乘位性交」「阴茎插入阴部特写」，不写「亲密接触」「结合部」。
- **tag 轨（NovelAI）**：明确词进 positive（`sex, vaginal, penis, cum, cowgirl position`）；
  成年锚 `adult, mature` 与负向词表照旧承担安全，不靠含糊化。
- **自然语言轨（Tsubaki.3 / Seedream / PixAI 视频）**：同样直写直白词，句式仍守可见层纪律（锁位 + 接触点 + 单事件）。
- **拆解报告同样直白**：报告要能**直接转提示词**——「结合部特写」这种写法等于把信息丢了（见 `video/deep-teardown/SKILL.md`）。
- **降级是例外**：只有目标引擎确带审核（如托管平台）时才走 `SKILL.md` 第 7 节等长替换；**默认出稿不出含蓄版**。

### 9.5 KB 词条索引（选词查这里，别再凭记忆拼）

本表每个词在 `references/kb/` 都有**抓取核实的 canonical 词形 + 中日别名 + 热度证据**（2026-10 从 booru wiki 抓，脚本与协议见 `kb/README.md`）：

| 文件 | 管什么 | 典型词 |
|---|---|---|
| `kb/anatomy-fluids.md` | 器官 + 体液落点/状态（§9.1 / §9.3 的证据层） | `penis` `pussy` `anus` `cum` `precum` `pussy_juice` `facial` `cumdrip` ⇄ `cum_overflow` |
| `kb/foreplay.md` | 前戏 | `foreplay` `french_kiss` `fellatio` `irrumatio` `deepthroat` `cunnilingus` `breast_sucking` `nipple_tweak` `fingering` `undressing` `groping` `paizuri` |
| `kb/during.md` | 进行时 | `sex` `vaginal` `cum_in_pussy` `ejaculation` `ahegao` `rolling_eyes` `tongue_out` `spread_legs` `sweat` `very_sweaty` `heavy_breathing` `moaning` |
| `kb/aftercare.md` | 事后 | `after_sex` `after_vaginal` `afterglow` `cuddling` `sleeping` `under_covers` `bed_sheet` |
| `kb/play.md` | 玩法 | `bondage` `restrained` `shibari` `collar` `leash` `sex_toy` `vibrator` `dildo` `anal` `threesome` `group_sex` `spitroast` `exhibitionism` `netorare` |
| `kb/positions-extra.md` | 体位补充（主表 §1.1 的证据层） | `reverse_cowgirl_position` `mating_press` `prone_bone` `suspended_congress` `spooning` `tribadism` |

**三条实测纠正**（写稿前扫一眼，省一次重跑）：

1. `cumdrip`（**已拔出**后外流）与 `cum_overflow`（**尚在体内**时溢出）互斥——混用会被画成矛盾状态。
2. `penetration` 是歧义 tag；`grinding` 也是（指向 crotch_rub / dry_humping / frottage / pussyjob）——tag 轨别用这两位。
3. 中文名优先取 wiki `other_names` 里的中文别名（`cunnilingus→舔阴`、`cowgirl_position→骑乘位`），不要自己硬译。
