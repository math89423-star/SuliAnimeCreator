# v4.0 Preview 实战指南（官方现场验证版 · 精编）

> 来源：`blog.pixai.art/en/how-to-prompt-pixai-v4-0-preview/`（官方 field-tested guide）。
> 原话：**参考图怎么叠 > 提示词怎么写 > 失败怎么迭代**。多数人的失败不在文字，在参考图设置。

## 1 TL;DR（五条）

1. 用**一张干净的角色图**做参考——它不是首帧。
2. **不要在提示词里描述角色**——让参考图去承担身份。
3. 运镜写**真动词**（push in / tilt / orbit），不写 `zoom in`。
4. 先在 v4.0 Lite Preview 上试，再用 Preview 出终稿。
5. 前置工作（提案/剧本/镜头表/参考图）交给 Mio.2。

## 2 参考图：语义锚，不是起始帧

- 老模型（含 v3.x）把参考图当第一帧：图里她是坐着的，提示词写"她跳起来"——出来还是坐着。
- v4.0 把**身份**（发色、瞳色、服装、眼罩位置、猫耳、心形呆毛）与姿势/环境解耦，动作由提示词驱动。
- 实测：**4 张参考图比 6 张更锐**——6 张时模型要调和六个略有差异的轮廓，输出变软。
- 场景分图写法：`She stands in the scene from @image2, wearing the outfit from @image1.`

### 参考视频：借感觉不借内容

```text
Transform this static character art from @image1 into a gacha-style animated character card,
following the same camera motion and pacing style as @video1.
```

借来的是**运镜、节拍、构图感觉**；不会把参考视频的画风或角色带进来。
技术限制：mp4、<50MB、单段 <15s，多段合计也要 <15s。

### 参考音频：只给文字说不清的音色/气质

```text
Reference the rhythm and atmosphere of @Audio1.
```
台词、环境音、音效**不需要**音频参考——直接写进提示词（见第 4 节）。

## 3 写提示词的两种情况

### 情况一：你知道要什么

直接写。陷阱是"看起来像电影术语的空话"：`zoom in` 比不上 `the camera slowly pushes in during the turn`。
用 `then` / `and` 串动作：`She looks down, then slowly lifts her eyes to the camera and gives a small smile.`
没有连接词，模型会把一切塌成一个静态瞬间。

### 情况二：只有图，没有构想（多数人的真实起点）

**迭代循环**：
1. 起草丢给 LLM（把图给它，要一段短视频提示词）——当**素材**看，不当答案。
2. 便宜模型试结构：`v4.0 Lite Preview` / `v2.7 High Dynamics`。
3. **读失败，不读提示词**：看片子哪里不对，问题就在"你写的"与"它出的"之间的差。
4. 同一条提示词丢给 `v4.0 Preview` 出终稿。

## 4 格式要点（照抄）

### 4.1 时间分块：两种写法别混

```text
[0-1.2s] beat 结构  ← 同一镜内的节拍流动（连续长镜）
[Scene 1: 0-3s] framing 结构 ← 在这里切镜（多镜）
```
**混用是多镜提示词变幻灯片的头号原因**。每拍只放：一个主体 + 一个动作 + 一个环境元素。

### 4.2 语音行三段式

```text
音色描述 — 情绪 — 原生语言台词
Voice — shy prince vocal type, warm and slightly trembling: 「あの……お昼、一緒に行かない？」
```
**绝不罗马字**：写 `Konnichiwa` 出来是不可懂的音频。

### 4.3 SFX 破折号串

```text
SFX: heavy rain — thunder rumbling — silence — a single heartbeat
```
写成一整段描述音景，效果差很多。

### 4.4 漫画条模式

```text
From left to right, top to bottom, present this as a comic strip.
Add special sound effects for scene transitions.
```
切到多格动态漫画输出（动画面板 + 转场），用于动画漫画页与同人宣传片；2-6 格都适用。

## 5 五类失败与修法

| # | 症状 | 修法 |
|---|---|---|
| 01 | LLM 脑补参考图没有的特征（猫耳女孩自动加尾巴、水手服自动加领结），生成中途尴尬插入 | 拿草稿对着图逐句读，**删掉图里看不见的特征** |
| 02 | 提示词在"描述"而不是"导演"→ 出静帧 | 删掉描写句，只留描述"会变的东西"的动词 |
| 03 | 一帧堆十几个元素（玫瑰+花瓣+气球+巧克力）→ 视觉噪音 | 每拍限一主体一动作一环境元素 |
| 04 | 模型自造物理（写"金鱼游动"它造了一个水池） | 点明超现实：`goldfish drift through the air, this is a dream, no physical realism needed` |
| 05 | 想要溶解换场，每次都是硬切 | 给过渡一座"桥"：变成传送门的镜子、拉开的帘子、掠过画面的花瓣 |

## 6 可抄示例

### 6.1 单镜（本项目"一镜一段视频"的写法）

```text
@image1 — character reference throughout; keep her face, hair color, and outfit exactly as in the reference.

[0-5s] She sits by the window and slowly turns her head toward the camera, hair strands drifting in the breeze.
The camera slowly pushes in from medium to close-up during the turn. Soft window light from the left.

SFX: quiet room tone — fabric rustle — a single slow exhale
```
并声明：`fixed shot` / `camera holds still` 用于"完全不运镜"的场景。

### 6.2 多镜（带切镜与台词）

```text
0s–2s: The white-haired gambler spins a gold coin between her fingers, smirking. SFX: metallic spin — tense atmosphere
2s–4s: Cut to the sailor girl across the table, her hand trembling. She whispers: "You said you'd find me again." SFX: soft tearful voice
4s–6s: Back to the gambler, leaning in: "Cute line. Did you rehearse it?" Cards slap down. SFX: playful tone — card impact
6s–10s: Match cut — the coin falls through memory space. SFX: warm wind — ethereal chime — distant promise
10s–13s: The gambler blinks. "...sorry, kitten. Do I know you?" SFX: silence — single heartbeat
13s–15s: The sailor girl's hand closes around the pendant, smiling through tears: "Not yet. Deal again?" Fade to black. SFX: emotional catch — coin clatter
```

（官方成品：4 张参考图、6 个节拍、3 句台词、分层 SFX，15 秒。）

### 6.3 Mio.2 前置工作流六步（提示词原文可抄）

1. **提案**：`Based on the character in this image, suggest 5 short-form anime story pitches in the [genre] direction. For each, a logline, the opening shot or first line, and the emotional reaction it's going for.`
2. **收紧**：`Develop pitch #[N]. Change: [what]. Keep: [what]. Rewrite with these changes, keeping the same emotional core.`
3. **大纲**：`Outline this pitch as a [15-second] anime short with a hook (first 2s), build (story beats with rough timing), and final image. Include actual dialogue lines. The premise must be conveyed indirectly — never stated out loud.`
4. **镜头表**：`Break this script into a shot list with a maximum of [N] shots. For each: timing, composition, what's in frame, camera movement, key visual detail, dialogue/on-screen text. If more than [N], compress to exactly [N] — each shot must do irreplaceable work.`
5. **参考图**：`Based on the shot list, generate [N] storyboard images. Use the attached character reference to keep the character consistent. Do not include any text in the images. Match the art style of the reference.`
6. **出提示词**：`...write a v4.0 Preview prompt... For each timestamped beat include: time range, which @image, action and camera description, dialogue (exact lines from the script), and SFX cues. Use em dashes for layered SFX. Keep total prompt length under 2000 characters.`

**第 6 步的"逐字照抄台词"很关键**：AI 转写提示词时会悄悄改写，把第三步打磨过的潜台词丢掉。

## 7 与本项目的接法

- 分镜页"首帧"：构图要锁 → Start Frame（Keyframe）；只要身份 → `@image1`（Multi-Reference）。二者互斥，交付时标注。
- 组装引擎选 `pixai` 时，本项目按本文件格式出稿：`@image1` 行 + `[0-Xs]` beat + 相机动词 + `SFX:` 行。
- 成人向：PixAI 视频的成人向通道是 `Enhanced / Professional`（Plus+）；Normal 档只吃 SFW——
  因此直白档要同时准备一份按 `video/nsfw-directing` 第 7 节替换表出的**等长降级版**。
