# Tsubaki.3（PixAI）出稿手册

> 来源：官方博客 `blog.pixai.art/en/tsubaki-3-prompt-guide/`（2026-09-09）+ 文档 `docs.pixai.art/docs/models/tsubaki3`。
> 一句话：**描述它，不要给它堆 tag**（官方原文 "Describe It, Don't Tag It"）。

## 1 核心：像给插画师下 brief 一样写

- 你给插画师下 brief 不会扔一堆词，而是说：**里面是谁、在做什么、从哪个角度看、光是什么样、要什么风格**。
- 真正在起作用的是**连接词**：`her back mostly turned to the camera as she looks back over her shoulder`（身体与头朝不同方向）、
  `a lit shop sign directly behind her throws a warm orange rim light along`（光来自哪个物体、落在哪里）。
- **介词与动词比形容词值钱**：画面成立靠"谁在谁后面、什么照亮什么、谁看着谁"。

## 2 五槽描述顺序（照填不会漏）

| 槽 | 回答 | 示例片段 |
|---|---|---|
| Subject 主体 | 谁 | `A black-haired girl in a white collared shirt and navy cardigan` |
| Details 细节 | 穿什么/在做什么/什么表情 | `stands on a rooftop at night in light rain, looking back over her shoulder` |
| Framing & Camera 构图机位 | 什么角度/多近 | `medium shot from slightly below, shallow depth of field` |
| Light 光 | 从哪来/什么氛围 | `a lit shop sign behind her throws a warm orange rim light` |
| Style 风格 | 插画/漫画/动画静帧/写实 | `anime illustration, crisp clean linework` |

**中间两槽（机位、光）是大多数人跳过的**，也正是"完成品"与"草图"的差别。
短提示词也行：只想要氛围时三句话足够——**想更具体就写得更具体，每多一句就从模型手里拿回一个决定权**。

## 3 语言

- **可以直接用中文/日文/韩文写**，不用先翻英文；同样的描述写成三种语言，风格会不同，但**写进去的要素都能过**。
- **例外**：专有名词与技术词留英文更可靠——`bokeh`、`rim light`、`wide-angle` 这类映射更准。

## 4 参考图（两个通道，用途不同）

| 你想保留什么 | 用哪个通道 |
|---|---|
| 构图/姿势/摆放（内容整体换掉） | **Base image**（右侧槽）——把角色也一起换掉，只借姿势/摆放/氛围；喂它**姿势清晰 + 背景干净**的图 |
| 只改一个指定部分（其余不动） | **提示词框里的 reference slot**——"改一处，留其余" |
| 角色外观搬到新场景 | **提示词框里的 reference slot** |

- 调用写法：`@image1` 指代参考图；`Put the character from @image1 in a rainy convenience store parking lot at night. Keep the character's appearance exactly as in the reference.`
- **改一处要写"保留什么"**：`Change her hair color from black to pale silver, keeping her hairstyle, expression, outfit, and the background unchanged.`
- **点名具体物件，不要用类别词**：`the navy ribbon bow at her collar` 能保住那个蝴蝶结；`her accessories` 太笼统，什么都护不住。
- 场景描述很细时，加一句兜底：`The character's appearance must be determined entirely by the reference image. Do not redesign the hair, outfit, or facial features.`
- 一张参考图还能出：三视图（`Generate a three-view sheet of the @image1 character: front view, side profile, and full back view.`）、表情表、手办、贴纸组。

## 5 图上文字（content + position + job 三件）

- 关键是**"这份文字在版面上干什么"**：headline / subhead / label / panel number / dialogue。定了职责，字号、位置、字性格一起落位。
- **点名字体形态**：`in Japanese hiragana` / `in printed English capitals` / `in Simplified Chinese` —— 字更干净。
- 多段文字：**先声明每段文字，再描述画面**：
  ```text
  headline text: "STRIDE", vertical tag text: 「一歩」, caption text: "NO.01"
  ```
- 文字当主角时给它地盘：`The character's name written in extremely large, bold, thick block letters, occupying the upper half of the cover, the character illustration overlapping the lower edge of the lettering.`
- 层级用尺寸+位置一起拆（报头在上、副题紧跟、期号小角落，可直接给比例）。
- **标注要带指向**：`Small label text "hood lining" with a thin leader line pointing to the inside of the hood` —— 有 `pointing to` 才出引线。
- 图里有 UI/图标/按钮时，结尾加 `no text` 让这些区域保持干净。

## 6 漫画面板格式

```text
Panel 1: a girl looks out a classroom window at the rain, speech bubble text "It's raining again."
Panel 2: close-up of her hand tapping a pen on the desk.
Panel 3: she stands under the school entrance roof, the empty schoolyard behind her.
Panel 4: a boy holds an umbrella out to her from off-panel, small speech bubble text "Share?"
```

- **一格一段、面板号开头**：编号把内容绑到位置，写几格出几格（4/6/9 格同法）；黑白就说 `black-and-white manga page`。
- 对话框还能指定三件事：形状（regular round / jagged burst / empty）、**尾巴指向谁**、内容（`text "..."` 精确引号）。

## 7 风格：拆成部件写（不要风格名）

四个角度：**线条**（有无描边/粗细/均匀或有压感）、**上色**（平涂/渐变/可见笔触）、**配色**（饱和/低饱和/限定色）、**表面**（纸纹/颗粒/干净无噪）。

```text
A girl standing by a window. Soft graded washes with visible paper grain, thin uneven ink outlines that break in places, muted low-saturation palette, white paper showing through in the highlights.
```

整句里**没有一个风格名**，但出来就是水彩——因为它写的是水彩的**物理证据**。
不必四角全填：挑该风格"不能没有"的一两角写透（水彩=纸纹+洇；赛璐璐=硬边阴影+有限层次；复古印刷=网点+套印偏移）。

**保留角色换风格**：走 reference slot + 点名保留项——
`Keep the character in @image1 exactly as she is — her face, hairstyle, and outfit — and redraw the whole image in a soft watercolor picture-book style with visible paper texture.`
跨度越大越要写"部件的构成方式"；长跳时再补一句"不要什么"（复古印刷加 `no smooth gradients`）。

## 8 光（四件事）

**方向 / 颜色 / 软硬 / 来自什么物体**——最后一件事最值钱：`Warm light` 不如 `the warm light from the shop sign behind her`。
光源一点名，模型就知道入射角、扩散范围、边缘软硬，还会把光源画进画面。

同主体同构图，只换光就换情绪（三组对照可直接抄）：

```text
Harsh midday sun from directly overhead through a skylight, short hard-edged shadows pooling at her feet, high contrast, bleached highlights.
Low golden sunlight raking in from the far end of the corridor behind her, a long shadow stretching toward the camera, warm rim light along her hair and arm, dust floating in the air.
A single fluorescent tube overhead is the only light source, a small pool of cold white light around her, the rest of the corridor falling into deep darkness.
```

再看**摄影方式**当光写：`direct flash` / `studio soft box` / `available light` / `security camera` —— 换一个词，整张图的"被拍摄感"就变。

## 9 材质与写实度：可以一格一格拨

- 写实度是**连续标尺**（扁平 2D ↔ 半写实 ↔ 照片级），**同一张图里允许不同元素处在不同档**：
  `A flat-shaded 2D anime character composited into a photorealistic photograph of a convenience store at night.`
  （角色层 `flat-shaded, flat colors, clean cel shading`；环境层 `photorealistic photograph`；中间用 `composited into` 连接。）
- **材质写物理特征**：问自己"这东西摆在桌上，哪几个特征一眼就看出它是什么材质"，然后写那几个。
  - PVC 手办：`glossy painted plastic surface with smooth highlights, visible seam lines`（**合模线**是关键）
  - 像素画：`visible pixel grid, dithering, hard-edged pixels, limited color palette`
  - 陶瓷=釉面反光+细开片；毛毡=纤维+毛边；刺绣=走针方向+底布；金属=镜面反射+倒角
- **让可信的环境替主体背书**：放进真实展示环境（`studio product photography, soft box lighting, seamless white backdrop`），物体就更像实物。

## 10 空间与构图

- **有"多少"就给数**：`More than 80% of the image is pure black negative space. The character is rendered small and positioned at the bottom center.`
  数字不必精确（`roughly 65%`、`about a third` 都行）——**重要的是给模型一个对齐物**。
- **位置用关系写**，不用绝对坐标：`the left panel positioned slightly lower and level, the right panel slightly higher and tilted`。
- **两个主体就写"谁看着谁"**：`the first standing at the foot of the bed seen from behind, the second lying on the bed seen from a high angle. The standing one looks down toward the lying one.`
  （位置 + 各自视角 + 视线关系三件，最后一件才把两人放进同一张画。）
- **透视可以点名**：`Ultra-wide / high angle / fisheye / isometric`；注意透视词会把画面推向摄影端。

## 11 交稿前八条自检（官方 checklist）

1. 是不是写成了连贯的描述句？
2. 五槽里的**机位**与**光**填了没？
3. 有参考图的话，放对通道了吗？
4. 图上文字：内容、位置、职责三件齐了吗？
5. 风格拆成部件了吗？
6. 光：方向、颜色、软硬、来源四件齐了吗？
7. 材质与写实度是否**逐元素**指定？
8. 每处"多少"有没有给数字？

> 官方提示：所有示例都是在 **Prompt Helper 关闭**下生成的——想看清"提示词本身做了什么"，就关掉 Helper 测。
