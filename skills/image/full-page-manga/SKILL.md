---
name: full-page-manga
description: "整页漫画方案：把一页漫画（单张图内多格）写成可直投 L-Port 的方案。适用 NAI / Tsubaki.3 / Seedream / Mango 3。触发：整页漫画、漫画页、full page comic、一页多格、九宫格漫剧页、page layout。"
version: 1.0.0
---

# 整页漫画方案（Full-Page Manga）

> 与 `skills/image/production-image-models` 叠加：本文件管**整页多格的方案写法与版面**，各家写法（tag/五槽/自然语言）仍按 production-image-models 各家轨道执行。
> 本仓只起草方案与敲定方向，不直连生成；成品在 L-Port。

## 1. 何时用整页模式

- 一页 = 一张图内含 N 格（2/4/6/9 格），格间共享角色、场景、光影。
- 适用：漫剧九宫格分镜页、四格漫画、封面/扉页、需要"一图读完一页"的场景。
- **不适用**：需要每格独立高清、或格间需要不同引擎/不同参考图时 → 走现有"一格一图"模式（`page_mode: panel`）。

## 2. 方案字段（art_plan）

整页模式下，`page_mode = "full_page"`，其余字段约定：

| 字段 | 整页模式下的含义 |
|---|---|
| `intent_text` | **整页一句话** + 各格 beat 列表（见 §4 模板）；是 L-Port 发散的唯一输入 |
| `page_layout` | 版面网格：`2x2` / `3x3` / `4-koma`（竖四格）/ `1+2`（通栏+两小）/ `splash+insets`（大图+嵌入小格） |
| `reading_order` | `rtl`（日漫默认，右→左、上→下）或 `ltr` |
| `page_mode` | `full_page` |
| `tier` / `clothing_level` | **整页统一**；若某格要更露骨，整页档位取最高档（不混档） |
| `ref_images` | 角色/场景锚图（≤6），编号进「参考图 N」；整页内所有格共享 |
| `comic_context` | 仍带 `episode_id` / `index`（页号）/ `outline_text`（整页大纲）；`panel_index = 0` 表示整页 |

## 3. 版面网格与阅读顺序

- **格数与网格**：2 格 → `1x2` 或 `2x1`；4 格 → `2x2` 或 `4-koma`（竖列）；6 格 → `2x3` 或 `3x2`；9 格 → `3x3`。
- **主格放大**：高潮格占 2×2 或通栏，其余小格环绕；用"格 N 占两格宽"描述，不用坐标。
- **阅读顺序**：日漫默认 `rtl`（右上→左上→右下→左下）；明确写出，避免模型按 LTR 排。
- **分隔**：`bold black panel borders with thin white gutters`（Tsubaki 公式）；黑白页加 `black-and-white manga page`。

## 4. intent_text 模板（整页）

```
整页：[一句话故事/场景]。版面 [page_layout]，阅读顺序 [rtl/ltr]，[B/W 或 彩色]。
角色锚：@参考1（主角）、@参考2（场景）……（token 原文，打包时自动转「参考图N」）

Panel 1 (top-right): [谁在哪儿做什么，一整句]
Panel 2 (top-left): ...
Panel 3 (middle-right): ...
...
Panel N (bottom-left): [高潮/落幅]

风格：[线条/上色/配色/表面 四角，按 production-image-models §7]
光：[方向/颜色/软硬/来源物体，按 §8]
对话气泡：Panel X "台词"（regular round / jagged burst / empty，尾巴指向谁）
SFX：Panel X「拟声词」
```

- **一格一段、面板号开头**：编号把内容绑到位置，写几格出几格。
- **台词精确引号**：`speech bubble text "..."`；气泡形状/尾巴/内容三件事都要写。
- **角色一致性**：每格描述里写 `same character as Panel 1`，并强调 `Consistent character appearance across all panels`。

## 5. 各家写法（叠加 production-image-models）

### Tsubaki.3（首选整页引擎）
按 §6 公式直接写 `Panel N: ...`，自然语言，禁 tag 堆。黑白页加 `black-and-white manga page`。对话气泡三件事（形状/尾巴/内容）全写。参考图用 `@imageN`（L-Port 发散节点编号）。

### NovelAI
NAI 对整页多格的支持以**自然语言描述 + 参考图锚**为主：在 prompt 里明确 `manga page, N panels, [layout], bold panel borders, gutters`，然后按 Panel 顺序描述每格。角色一致性靠 reference image + `same character`。tag 轨（NovelAI）里可加 `comic, manga, multiple panels, panel layout` 等 composition tag，但**主体描述仍按 tag 轨**。建议整页模式优先 Tsubaki，NAI 作备选/角色锚强时用。

### Seedream
自然语言，整页描述为一个场景："一张 [N] 格漫画页，布局 [layout]，阅读顺序 [rtl]，Panel 1 …"。Seedream 擅长带字图与组图，对话气泡文字直接写进描述（`Panel 2 气泡文字 "..."`）。写实度可分格拨（§9）。

### Mango 3
精确指令 + 跨图一致性；适合角色/服装/地点在多格间复用。用 `@imageN` 锚角色，整页描述里每格一行，强调"keep character consistent across panels"。

## 6. 连续性与降级

- **角色锚**：至少一张参考图（角色全身/三视图）；整页所有格引用同一锚。
- **场景锚**：场景图单独一张参考图，写 `same background as @imageN`。
- **格间衔接**：整页模式下"上一格成图"不自动带入（因为是单图），如需跨页衔接，把上一页的整页图作为参考图挂进 `ref_images`。
- **降级**：引擎出不好整页时，回退到 `page_mode: panel`（一格一图）+ L-Port 拼页；方案里可注明 `fallback: panel`。

## 7. NSFW 水位

- 整页档位**统一**：`tier` 取整页最高档（tease/undress/explicit/closeup），`clothing_level` 同理（L0-L4）。
- 某格想更露骨 → 提高整页档位，不混档；或拆成两页。
- 角色一律成年锚点；血腥暴力全部剥除（与 R18G 划清）。

## 8. 交付给 L-Port

- 直投包 `art_plan.json` 带 `page_mode: "full_page"` + `page_layout` + `reading_order` + `intent_text`（含 Panel 列表）+ `reference_images` + `tier`/`clothing_level` + `comic_context`（页号/大纲）。
- L-Port 侧按 `page_mode` 分流：`full_page` → 单图生成（整页 prompt）；`panel` → 现有 comic_page_diverge 链路。
- 回传：整页成图挂到该页（`page.image`），不拆格。
