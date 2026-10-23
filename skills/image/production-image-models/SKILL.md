---
name: production-image-models
description: Prompt the project's production image engines — NovelAI Diffusion (V5/V4.5/V4/Anime V3), PixAI Tsubaki.3, Seedream (4.0/4.5/5.0 lite via Volcengine Ark), and Mango 3 (mango-v3 on the Mage platform). Covers per-model syntax (tags vs natural language vs description order), quality tags, weight syntax, reference-image routes, multi-character, text rendering, sequential/group generation, and hard limits. Use when writing or reviewing image prompts for NovelAI / Tsubaki / Seedream / Mango 3, or when the user names 图像侧 / 出图模型.
compatibility: Portable — plain local files. Sources: NovelAI official docs, PixAI official docs+blog, Volcengine Ark official prompt guide, Mage official docs (see PROVENANCE).
---

# Production Image Models（本项目出图引擎 canonical）

> 归属：**NovelAI / Tsubaki.3 / Seedream / Mango 3 四家生产引擎的提示词写法**以本文件与其 references 为准；
> 本地 Pony/Illustrious/SDXL/Flux 的 8-block、风格头、Vague ban 仍归 `image/illustration-prompt`（本文件不重定）；
> 机位/景别/透视归 `image/composition-camera`；成人向档位与体位/行为词表归 `video/nsfw-directing`（出图同样适用其水位与遮挡规则）。

## 0 先选引擎（一句话判据）

| 引擎 | 提示词形态 | 最适合 | 入口 |
|---|---|---|---|
| **NovelAI** | 逗号 tag 为主 + 自然语言混合 | 动漫角色立绘、多角色同框（V5 最多 22 人）、需要精确权重微调、角色/风格参考 | `references/novelai.md` |
| **Tsubaki.3**（PixAI） | **自然语言描述**（禁 tag 堆） | 漫画分页与版面文字、光照叙事、角色与画风一致性成套产出、中途稿（线稿/上色分层） | `references/tsubaki3.md` |
| **Seedream**（火山方舟 doubao-seedream） | **自然语言**（主体+行为+环境+美学） | 高密度知识图/信息图、图上文字排版、图片编辑（增删改）、参考图迁移、组图批量 | `references/seedream.md` |
| **Mango 3**（mage 平台 mango-v3） | **自然语言**（主体→场景→光→取景） | 同一张脸/同一件衣服/同一个场景跨图复用（`@handle`）、指令必须落地的精准编辑、垫图重绘 | `references/mango3.md` |

**一句话分工**：角色与多角色同框 → NovelAI；成套漫画/版面文字/光照 → Tsubaki.3；带字图、编辑、组图、写实向 → Seedream；跨图一致性（角色/服装/地点复用）与精确指令 → Mango 3。

> **整页漫画**（单图内多格）的版面/阅读顺序/气泡写法 → `skills/image/full-page-manga/SKILL.md`；各家按上表轨道落笔。

## 1 四家共用的三条铁律

1. **tag 与自然语言不混用**：NovelAI 吃 tag（可混短句）；Tsubaki.3、Seedream、Mango 3 **明确反对 tag 堆**——只写描述。
2. **具体物理量 > 形容词**：与 `image/illustration-prompt` 的 Vague ban 同源（`cinematic / masterpiece / 8k` 这类词在自然语言模型里形不成画面）；
   NovelAI 的 `masterpiece, very aesthetic` 属模型方言功能词，只在它自己的质量标签位出现。
3. **参考图先定"要保什么"**：四家都有参考图通道，但语义不同（NovelAI Precise Reference 分角色/风格；Tsubaki.3 分 base image 与 reference slot；Seedream 要求"指明参考对象 + 描述生成画面"两部分；Mango 3 分账号已存的 `@handle` 与本次请求的 `image`/`additional_images`）。

## 2 四家各自的硬规则（详情见 references）

- **NovelAI**：质量标签用开关，不要手写；权重 `{}`/`[]` 逐层 ×1.05，数值权重 `1.5::x ::` 仅 V4+；
  步骤 28 以内不耗 Anlas（Opus）；Guidance 建议 5-6（V3+）；多角色用 Character Prompts（V4 ≤6 / V5 ≤22）；V4+ 约 512 T5 token 上限。
- **Tsubaki.3**：五槽描述顺序（主体 → 细节 → 构图机位 → 光线 → 风格）；介词与动词比形容词值钱；
  可以用中文/日文/韩文直接写，但**专有名词与技术词（bokeh、rim light、wide-angle）留英文**；
  风格拆成四个角度（线条/上色/配色/表面）；图像内文字写"内容+位置+职责"三件。
- **Seedream**：写明**用途**（"设计一个游戏公司 logo"）；有参考图只写两部分（指明参考对象 / 描述生成画面）；
  编辑操作用"增加/删除/替换/修改"动词 + 需要时用箭头线框涂鸦指位置；组图用"一系列/一套/组图"或直接给张数。
- **Mango 3**：四件套顺序（主体 → 场景 → 光 → 取景），光与取景必写；`@handle` 只写账号里真实存在的（凭空造会被接口 400 拒单），
  角色与参考图共享 10 张额度；**无负向栏**（要排除就正向改写）；无 LoRA/ControlNet；分辨率 1K·2K（3S 3K / v2 4K）、比例 9 档。

## 3 成人向口径（出图侧）

- **NovelAI**：`Undesired Content` 是可选的负向预设（不勾=不启用）；本项目出稿时按需自配，不默认清空用户的设定。
- **Tsubaki.3(PixAI)**：与视频侧同规则——`Normal` 仅 SFW，成人向走 `Enhanced / Professional`（Plus+）。
- **Seedream(火山方舟)**：托管平台侧有内容审核，投喂前按平台规则确认；本项目的成人向出稿优先走本地/NovelAI/PixAI-Enhanced 通道。
- **Mango 3(mage)**：平台侧有内容政策与 Mature Mode 开关；Mango 无负向栏这条在成人向同样成立——不要为规避审核写含混词（会往 SFW 收敛），直白词直接写。
- 水位、遮挡、器官与体液写法一律回 `video/nsfw-directing`（同一套词表，出图侧照用；该文件的动作预算对静图不适用，静图只需"遮挡结构 + 水位"）。
- **直白词直接用**：NovelAI / Tsubaki.3(PixAI-Enhanced) 都**直接吃露骨描述**——器官/行为/体液照
  `video/nsfw-directing/references/acts-lexicon.md` §9 直白词表写（`sex, vaginal, penis, cum, cowgirl position, creampie`…），
  **不要**为"稳"改用含蓄词（含糊＝模型往 SFW 收敛，画不出或画歪）。降级替换表只在目标引擎确带审核时用（如 Seedream 托管侧）。
- **成年虚构锚定同样适用**：NovelAI 正负双锚（`adult, mature` / negative 见 `references/novelai.md`），Tsubaki.3 与 Seedream 在自然语言里正面写定。

## 4 交付与归档

- 出图提示词交付时**带引擎名 + 参考图用法**（用了哪个通道、要保什么），否则执行侧无法复现。
- 角色资产（三锚/服装/槽位）来自 `character/character-design` 与项目角色页；本文件只管"把设定译成该引擎的提示词"。
- 一次生成只改一个变量（角色/机位/光/风格四者之一），否则失败无法归因。

## PROVENANCE

- NovelAI：`https://docs.novelai.net/en/image/{basics,models,qualitytags,strengthening-weakening,stepsguidance,multiplecharacters,precisereference,promptchunks}`
- PixAI Tsubaki.3：`https://blog.pixai.art/en/tsubaki-3-prompt-guide/`、`https://docs.pixai.art/docs/models/tsubaki3`
- Seedream：`https://www.volcengine.com/docs/82379/1829186`（Seedream 4.0-5.0 提示词指南，官方）、`https://www.volcengine.com/docs/82379/1824718`（模型能力/限流）
- Mango 3 / mage 平台：`https://docs.mage.space/models/mango`（模型能力/分辨率/负向栏）、`https://docs.mage.space/prompting/basics`（提示词四件套 + `@handle`）、`https://docs.mage.space/features/references`（参考图额度）、`https://docs.mage.space/api/models/mango`（API 字段与枚举）
