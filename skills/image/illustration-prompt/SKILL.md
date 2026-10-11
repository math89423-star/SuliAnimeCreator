---
name: illustration-prompt
description: Turn vague Chinese art ideas into generator-ready English prompts for anime/moe (Pony/Illustrious/SDXL) and photoreal (Mango/Flux) on Mage. Use when the user describes an idea or names SOP STEP 2, or needs reference-aware prompt structure instead of raw generation.
---

# Illustration Prompt（prompt组装 canonical）

> 归属（2026-10-11 精修）：8-block/双轨输出/风格头/Vague ban/tag转译/MCP prompt检索以本文件为准；机位构图透视底/镜头语法/Scene Bible空间覆盖见 `composition-camera`（此处不重定机位词表，直接引用）；SVG图层渲染见 `svg-illustration-craft`；Scene Bible此处只管prompt措辞（母版/派生/入场句式），空间覆盖表归 composition。

## What I do

- Translate a vague visual idea (often Chinese) into one structured, copy-paste-ready English prompt per direction.
- Keep references and explicit scene constraints above decorative adjectives.
- Adapt the same idea to moe tag-style (Pony/Illustrious) vs cinematic natural-language (Mango/Flux) as the target model requires.

## When to use me

- User says `我有一个idea` or names `STEP 2`; STEP 1 character design (motif/identity/palette/selection) goes through the `character-design` skill first.
- The task is prompt design / divergence / review, not code, not image generation.

## 8-block structure (output order)

1. `subject` — who + count (`1girl, solo`：1girl=画面内可见女性一人，见 https://danbooru.donmai.us/wiki_pages/1girl；单人配 solo) + age feel (no ambiguous terms)
2. `appearance` — hair, eyes, face, body, fixed traits (ahoge, cat ears, accessories)
3. `outfit` — top/bottom/socks/shoes, fabric words
4. `pose-expression` — pose + gaze + expression, consistent with each other
5. `scene` — setting + key props only (STEP 3 details stay out at STEP 1; STEP2 only perspective proxy: clay corner + eye-level + contact shadow, no texture/props/lighting)
6. `camera` — shot size, angle, lens feel (`close-up`, `3/4 view`, `low angle`)
7. `light-color` — light source + 2-3 main colors + 1 accent
8. `quality` — moe: `score_9, score_8_up, source_anime, masterpiece, best quality`;
   photoreal: `masterpiece, ultra detailed, 4k` + lens/film words

## Reference rules

- If a reference image/character is given, state in one line what is borrowed
  (identity, outfit, pose) and what is NOT borrowed (background, composition).
- Conflicting references are called out, never silently blended.
- Default to no text in image unless the user explicitly asks for text.

## MCP routing（只管prompt tag检索，机位例文检索归 composition-camera）

- Chinese word or uncertain spelling → `booru-pictag-get.autocomplete_tags` first,
  then build with canonical `underscore_tags`.
- "What does character X look like / costume variants?" →
  `booru-pictag-get.danbooru_get_character_profile` (traits + wiki + implications).
- Need a ready-made exemplar prompt for Pony/Illustrious →
  `booru-pictag-get.search_prompts` or `civitai.search_images` (withMeta=true
  gives prompt + negative + sampler + steps + CFG + seed).
- Multi-word tags use underscores (`blue_hair`); booru search is tag-AND, prefer
  one strong tag over stacking.

## Output

- One structured English prompt in its own code block per direction.
- A short kebab-case filename suggestion is optional.
- One line of generator note only when a model-specific tweak genuinely matters
  (e.g. Pony needs score tags, Mage Agent only has Low/High + Gems).

## Partial-body framing (部位构图，本地 Illustrious 实战固化）

- 景别 tag 决定构图，模型按 shot tag 裁框：`head-and-shoulders portrait`（大头）/
  `waist-up portrait`（腰上）/ `lower body focus, thighs to shoes in frame`（下半身）/
  `full body`（全身）/ `close-up` + 部位（瞳孔/手/鞋特写）。
- **不画的部位不写 tag**：写了就会抢构图挤进框。下半身单只写裙摆作 context
  （`skirt hem visible at top of frame`），不写脸/发；上半身单不写腿/鞋。
- **防裁切三件套**（按景别选）：`entire head in frame with margin above hair` +
  negative `cropped head, cropped chin`（大头/腰上）；下半身 negative 加
  `cropped feet`；转面加 `clean background no borders` 防胶片条伪影。
- **材质正负双压**（哑光丝袜案例）：只压单边压不住系统偏好。正面
  `matte, fully opaque, no sheen, no shine` + negative
  `glossy, sheen, shiny, oily highlights, skin visible through tights`，
  双边同时写才出得来。
- **分辨率配景别**：大头/腰上/下半身 `1024x1280` batch 2-4；全身转面
  `1536x1024` batch 2。链路：彩境天工 v7 + 细节 LoRA 0.5，
  Euler a 28 steps CFG 6，单批约 30-60 秒。
- 部位单归属：款式板/细节单进 `breakdown/`，不进人物包 Master。

## 双轨输出（本项目标配）

- **词表版**：tag 串联，给本地 Pony/Illustrious 草稿与 Anima 混写；短、硬、可扫。
- **自然语言版**：成品段落，给云端 Grok/GPT 与写实系；写清「相机在哪、看到什么」。
- 两版信息量必须对等，不许一个详一个略；中英双版时结构顺序一致。

## 高级写作焚诀（写 prompt 时逐条过）

- **具体数字 > 形容词**：`f/1.8` 比「梦幻虚化」稳；浅景深写全四件事——焦段 + 光圈 + 对焦点 + 主体背景距离。
- **相机块四行**（贴 prompt 末尾）：`Camera / Focus / Distance / Composition`。
- **光影三要素**一次写全：方向 + 光比 + 色温（`key light from upper left, high contrast, warm 3200K`）。
- **冷暖结合**：主色暖时，在反射/阴影里塞一抹反色，画面才活。
- **修饰词纪律**：质感词 ≤3 个（`film grain / chromatic aberration / dust motes`），多了互相打架。
- **Vague ban 表（2026-09-29固化，ai-shortfilm-prompts 引进）**：`cinematic / epic / masterpiece / stunning / spectacular / perfect / premium / 4K / 8K / HD / high quality / texture-rich` 一律禁入正文——模型对它们形不成具体图像。必须换具体物理量：`史诗感`→`IMAX + 35mm f/4 + 低饱和灰蓝`；`精致`→`film grain + 金属拉丝 + 布面纹`。自检：随机抽 3 个形容词，形不成画面的删。豁免：Pony/Illustrious tag 串里的 `score_9, masterpiece, best quality` 是模型方言功能词，不在 ban 列；ban 只管自然语言形容词。
- **风格头质量分级（2026-09-30固化，教堂Master糊片教训）**：`2D tv anime screencap`声明低码流电视截帧，模型往压缩画质走， heavenly大教堂必糊。漫剧统一改用设定级头——`high-quality 2D anime illustration, anime key visual, official anime art, cel-shaded anime`+原赛璐璐特征（平涂/两级阴影/干净线稿）保留，质量尾只用具体词（`sharp lineart, highly detailed background, film grain`），与Vague ban同查。
- **顺序即权重**：风格锚最前、主体次之、机位与光在中后段；重要词别埋尾巴。
- **留白必须带位置**：`negative space on the upper third for text`。
- **器材作弊码**：`shot on Sony A7R V, 35mm f/1.4, Fujifilm Classic Negative film simulation`——具体器材字符串比抽象形容稳。

## 避雷速查（出稿前 30 秒）

- 机位词打架（`from above` + `eye-level` 同写）/ 景别冲突（`close-up` + `full body`）/ 同义三连堆叠（high angle + from above + bird's eye）。
- **Targeted negative（2026-09-29固化，DirectorSKILL 引进；短原则有 Mage 背书）**：negative 每镜现配，只点名本镜真实风险的实例（`no plastic, no rubber soles, no wristwatch, no printed logos`），禁通用长单——长单稀释且可能召唤所禁之物（Mage 原话：field 不是句子、要短、长了反噬，见 https://docs.mage.space/features/negative-prompts）。正文已写明的风险不重复进 negative（正负同词正文赢）。
- **negative 分模型（2026-10-11 联网纠正，笼统写法作废）**：moe（Illustrious/Pony/Anima/SDXL 系）有栏照常用短 negative；Mango/Flux/GPT Image 2/Grok/MiniMax-H3/Nano Banana 2 **无 negative 栏**，不许写“有框就填”（见 https://docs.mage.space/features/negative-prompts 表）。
- 构图词不带留白内容 / negative 与正向打架（负词里混进要的概念）/ 垫图句不锁机位（缺 `same camera angle and composition as the reference`）。
- 双人不写左右与朝向（越轴）/ 远景却要求眼部细节（描述预算按景别分配）/ `tilt` 误当 `dutch`。

## 自然语言描述法（云端成品段落）

- **四步公式**：①机位（相机在哪、怎么转）→ ②主体（谁、在干嘛、朝哪）→ ③构图（怎么框、留白在哪）→ ④光/氛围一句收尾。
- **同一机位五种说法**：直述式（`Shot from above at about thirty degrees`）/ 视角代入式（`We look down on her`）/ 相对描述式（`well above her eye level`）/ 情绪先行式（`a heavy, off-balance look-down`）/ 指令·垫图式（`same high angle ... identical to the reference`）。
- **用哪套**：Pony/Illustrious → tag 串联；Anima → tag+NL 混写；云端 Grok/GPT/写实系 → 自然语言优先；本项目 → 本地草稿用词表版、云端成品用自然语言版（中英双版对照验证）。
- **活感三招**（成品段落必查）：动词换名词（`mid-stride` 而非 `standing`）＋ 加残响层（`still swaying, steam rising`）＋ 情绪写行为不写标签（`tearing up but smiling` > `sad`）。
- 成品段落范例与逐段拆解：查 `composition-camera.html`（组合实战 / 高级镜头 / 拆解实战 / 活感工作台）。

## 场景 Bible 提示词写法（漫剧多机位，2026-09-29固化）

- **母版 prompt（空场景，无人物）**：风格锚 + 空间结构句（房间类型/开间/门窗位置机位系双述）+ 固定家具清单（件数≤5，逐件方位）+ 光源时间（主光方向+色温+时间点）+ 透视（灭点/眼位线可读）+ 质量尾。禁人物词（出现 `1girl/boy/man` 一律判废）、禁氛围形容词堆砌。
- **机位派生 prompt（只改一变量）**：首句母版继承——`same chapel interior as the scene master, identical door window benches positions, keep layout fully consistent` + 本机位增量（机位四要素一句）+ 本镜可见物一句；其余一字不复述母版。改两处以上=新机位，拆成两步走。
- **人物入场写法**：人物站位用锚点相对关系（`kneeling left of the altar, facing the statue on the image-right`），不写绝对坐标；比例双写（人物占比+人景比例）必带。`between` 双关禁用，用 `past`/`beyond`/`flanked by` 单义动词，位置纵向+横向+距离三重锁。
- **相对比例优先于绝对比例（2026-09-29固化，教堂 K1 实战）**：人景同框时，绝对数值（几分之几框高）模型随手 inflation，**相对比例句才是唯一标尺**——必须写人物相对背景主体的倍数关系（如 `her kneeling height is one-third of the statue's visible height, the statue towers at least three times her size`）。绝对比例只作辅助，相对句缺失即判废；自检：人物站起来也只到背景主体腰部以下才算过。
- **家具作尺子（2026-09-29固化，教堂 K1 巨人症实战）**：相对比例第一标尺永远是**同深度已知高度的家具**（凳/桌/门），不是神像雕像这类未知高度物——神像可高可矮，凳高 0.9 米是死的。写法：`her kneeling height equals about 1.2 times the back height of the nearest bench at the same depth`；自检换算：跪姿≈0.9~1 米≈一凳背高，站姿≈1.6 米≈两凳背，超了就是巨人，直接 FAIL。神像倍数句只保"高耸叙事"，家具句保"真实身高"，两句都要写。
- **母版验收必过尺子（2026-09-29固化，教堂 Master 九米神像教训）**：母版冻结前除验透视收敛，必须拿同深度家具逐项量一遍非常物（神像/立柱/吊灯）：神像可见高 ÷ 同深度凳背高 = 倍数，×0.9 米即神像真实高度。倍数与故事不符（亲近祈福要 3~4 米，史诗仰望才许 8 米+）→ 重出母版，不许将错就错进派生。漏量即评审 FAIL。
- **机位间一致性锚定**：每张机位图带 `same space as <cam-X>, shared layout, only framing differs`，与角色一致性锚定句同级，不得省略。
- **避雷**：临场发明机位词（绕背/正后方/新空间）→ 先补 Bible 机位图；一次派生只动 Frame（框量/裁切），Blocking（站位/轴线/锚点）一字不许动。

## 云端大场面 background-master（Grok/Seedream/GPT-Image 通用，2026-10-01固化）

- **何时用**：云端出大场面环境建筑母版（教堂/街景/大殿）。本地不管，STEP1/2词表版不管，只管云端自然语言版。
- **三家收敛顺序**：`Goal/Canvas → Scene → Subject → Light/Camera → Finish → Constraints`。30-100词，前半放最重要的，虚词禁入（见Vague ban）。
- **母版五件**：用途+画幅（`16:9 for establishing, leave empty space on X for text`）+ 空间结构（类型/开间/门窗机位系方位）+ 家具≤5逐件方位 + 从近到远一句 + 光源时间（方向+光比+色温+时间点）+ 透视可读（灭点/眼位线）。禁人物词，禁氛围堆砌。
- **融合保真句**：换背景/入人物必带 `match perspective, shadow direction, color temperature` + `change only X, keep everything else identical`，每轮重复preserve清单。多图编号：`Image 1: shape, Image 2: light only, do not copy objects from Image 2`。Mage Grok最多3张，无seed，靠文字锁构图。
- **验收**：拿同深度家具量非常物（高÷凳背高×0.9米），倍数不符重出母版，不进派生。

## 配套手册

- 机位/构图/光影/姿态/神态/细节/发型/体型全词表 + 图示 + 成品段落：`composition-camera.html`（220 卡片 · 19 区 + 活感工作台）。
- 配色：`palette.html`。角色设计：`character-design` skill。镜头机位流程：`composition-camera` skill。创意发散：`creative-divergence` skill。
