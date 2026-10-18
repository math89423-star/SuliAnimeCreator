---
name: visual-aesthetics
description: 通用视觉美学指导（故事与剧本层的美术总纲）：色彩体系三层、光影设计三要素、材质语言、风格分级。 MouOnce 角色/服装/构图各有主之后，跨品类的统一口径。当用户说定调、美术指导、配色、光影、风格、质感，或剧本/故事需要视觉基调时使用。不画具体款式（款式归 costume-design/garment-flat），不定机位（机位归 composition-camera）。
---

# Visual Aesthetics（通用视觉美学，跨品类口径）

> 归属：本文件只定跨品类美学口径；服饰美学归 `aesthetic-fashion-design`，角色转译归 `character-design`，机位归 `composition-camera`，prompt 组装归 `illustration-prompt`。每条有出处（历史沉淀/Mage/booru），无出处不写。出处总表见 `docs/PROMPT_PROVENANCE.md`。

## 1. 色彩体系三层（历史：character-design 配色三层 + palette.html 764 色实测）

- 主色（最大面积）/ 辅助 / 点缀（小面积抓眼，必查 `palette.html`，不得自造色名）。
- 登记格式：主 `#HEX` 占比 + 辅 `#HEX` + 点缀 `#HEX` 落位（服装/发饰/徽章三处之一）。
- 冷暖结合：主色暖时在反射/阴影塞一抹反色（历史：illustration-prompt 冷暖结合）。

## 2. 光影设计三要素（历史：illustration-prompt 光影三要素 + composition 光位表）

- 方向 + 光比 + 色温一次写全（如 `key light from upper left, high contrast, warm 3200K`）。
- 主光三问（composition）：为谁打/藏什么/变化对应什么转折；答不上不许打。
- 光比即权力比：谁亮谁掌权， double check 亮的该不该掌权。

## 3. 材质语言（历史：aesthetic-fashion-design §材质对比 + costume-design 万能材质词）

- 每材质独立高光逻辑：缎面锐光 / 雪纺雾感 / 金属镜面 / 蕾丝网眼，禁一套渐变打天下。
- 写材质三件套：质地词 + 光反应 + 适用部位（如 `satin, sharp specular streaks, dress shell`）。

## 4. 风格分级（历史：教堂 Master 糊片教训 + Mage 四要素）

- 设定级头（漫剧统一）：`high-quality 2D anime illustration, anime key visual, official anime art, cel-shaded anime` + 平涂/两级阴影/干净线稿特征，禁 `2D tv anime screencap`（低码流声明，必糊）。
- 质量尾只用具体词（`sharp lineart, highly detailed background, film grain`）；Vague 形容词禁入正文（见 illustration-prompt Vague ban）。
- Mage 四要素顺序即权重：subject/setting/light/framing（见 https://docs.mage.space/prompting/basics）。
- V5 精华同步 （argon 指南）：复杂度四选一默认 `high complexity` (泛用高质量档，low/medium/high/ultra)；标准尾 `very aesthetic, masterpiece, high complexity, no text`，Add Quality Tags 开关已追加的不重复；功能词 `depthness/location` 保留，`location` 强化环境存在感。
