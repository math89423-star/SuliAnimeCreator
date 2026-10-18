# NovelAI Diffusion 出稿手册

> 来源：官方文档 `docs.novelai.net/en/image/*`。
> 适用：V5 Full / V5 Curated / V4.5 Full / V4.5 Curated / V4 Full / V4 Curated / Anime V3。

## 1 模型选择

| 模型 | 特点 | 备注 |
|---|---|---|
| **V5 Full** | 最新旗舰：自然语言理解更锐、支持**多语言提示词**（日文等）、支持 **alpha 透明通道**、多角色上限 **22**、重做角色定位、文字渲染更强 | 订阅各档可用 |
| **V5 Curated** | 数据集更干净聚焦 | 想要"少出意外内容"时选它（官方原话：直播演示最安全） |
| **V4.5 Full / Curated** | 上一代主力 | 自定义角色定位限 **5×5 网格** |
| **V4 Full** | 数据集更全但更杂、更新更近一月 | "要生成很具体的东西而 Curated 出不来"时换 Full |
| **V4 Curated** | 更小更干净 | 通用首选 |
| **Anime V3** | 老动漫模型 | 有较少的自然语言理解、无多角色 |

要点：
- **V4 及以上**：多角色提示词、自然语言理解、更好的英文文字渲染。
- **V4+ 的提示词上限约 512 T5 token**（基础提示词 + 所有角色提示词合计）。
- **V4 用 T5 分词器**：大多数 Unicode 字符（彩色 emoji、日文字符）**不能**进提示词。
- **V5 支持日文等多语言提示** + 透明通道；V4/V5 支持数值权重。

## 2 提示词形态：tag 还是自然语言

- 两者都行：可以整句自然语言，也可以用 tag 描述主体；输入时模型会给出 tag 补全建议（建议旁的小圆点不透明度 = 模型对该 tag 的熟悉度）。
- **注意上下文上限**：冗余堆叠的词会吃掉 token；重复同义 tag 是负优化。
- 生产惯例：动漫角色 → 逗号 tag 串（可夹短句）；场景与氛围 → 短句；**不要把两者混成一锅粥**。

## 3 质量标签（用开关，不要手写）

Prompt 框底部的 **Add Quality Tags** 开关（默认开）会自动在提示词**末尾**追加标签；这些标签**不显示在提示词里但占 token**。

各模型实际追加内容：

| 模型 | Light | Standard |
|---|---|---|
| V5 Full / V5 Curated | `, very aesthetic, amazing quality, no text` | `, very aesthetic, masterpiece, no text` |
| V4.5 Full | — | `, location, very aesthetic, masterpiece, no text` |
| V4.5 Curated | — | `, location, masterpiece, no text, -0.8::feet::, rating:general` |
| V4 Full | — | `, no text, best quality, very aesthetic, absurdres` |
| V4 Curated | — | `, rating:general, amazing quality, very aesthetic, absurdres` |
| Anime V3 | — | `, best quality, amazing quality, very aesthetic, absurdres` |

**出稿规矩**：写了这些词就是**重复**（开关已经加了）→ 要么关掉开关手写，要么开关开着就**不要再写**。

## 4 强化与弱化（权重语法）

- **括弧法**：`{ }` 强化（×1.05/层），`[ ]` 弱化（÷1.05/层）。嵌套继续叠乘：`{{x}}` = ×1.1025。
- **数值法（V4+ 才有）**：`1.5::文字 ::` 把右侧内容强化到 1.5；`0.5::文字 ::` 弱化；`::` 单独出现即**闭合**所有未闭合的括弧（`{{{{{rain ::` 不用数括号）。
- **负值**：数值权重可输负数（反向推离）。
- **Undesired Content 里的方向是反的**：这里 `{ }` 表示**更强烈地避免**，`[ ]` 表示**较少避免**。

出稿示例（一套权重 + 负向）：

```text
1girl, black hair, 1.5::rain, night ::, 0.5::coat ::, black shoes
```

## 5 采样与参数

| 项 | 建议 |
|---|---|
| Steps | 先低步数试构图 → 满意后用 **Enhance** 细化；步数过高收益很小 |
| Prompt Guidance | **V3+ 建议 5-6**；更高 → 细节更锐但可能过硬；更低 → 更绘画感/柔 |
| Guidance Rescale | 高 Guidance 时颜色过饱和（"deep fried"）时用它 |
| Decrisper | 高 Guidance 下的颜色/画面伪影抑制；对低 Guidance 也有可见影响，按喜好开 |
| Seed | 换 seed 是同提示词下的第一变量 |

Opus 会员：**28 步以内、常规分辨率、非批量**不耗 Anlas。

## 6 多角色（V4 ≤6 / V5 ≤22）

- 结构：**一个基础提示词（场景/风格） + 多个角色提示词**（每人一个框）。基础管全局，角色框只写本人，减少特征串味。
- **顺序即位置**：按角色框从上到下、从左到右排布（两人 + `side-by-side` 时，第一个在左，第二个在右）；可用框右上角的箭头调整顺序。
- **自定义位置**：把 `AI's Choice` 改成 `Custom` → 打开 Character Positions 画布直接摆位（V4/V4.5 限 5×5 网格）；位置设定不要与顺序冲突。
- **串味处理**：某个角色框的 Undesired Content 里点名"不该出现在这个人身上的特征"。
- 多角色 = 一张图里多人；**多个 Precise Reference 会互相融合**，不是分成不同角色。

## 7 参考图通道（Precise Reference / Vibe Transfer）

- **Precise Reference** 三种类型：`Character Reference` / `Style Reference` / `Character & Style Reference`。
  - 角色参考：给一张角色图，往往**不用再 tag 细节**，模型尽量还原该角色（可用于模型本身不认识的原创角色）。
  - 风格参考：影响整体画风；与角色参考可混搭，混搭还能造新风格。
  - 注意：**同时用多个角色参考会互相融合**（不会当成多个角色）。使用 Precise Reference **额外消耗** Anlas。
- **Vibe Transfer**：借氛围/色调/笔触（不是角色）。两者用途不同：要角色 → Precise Reference；要感觉 → Vibe Transfer。

## 8 其他生产力特性

- **Prompt Chunks**：常驻片段（类似质量标签/负向预设），输入 `@` 触发补全；可建分类文件夹；双击 chunk 把内容展开成普通文本。
- **Text Rendering**：V4+ 英文文字渲染较好；V5 进一步改善英文/日文等；要图上文字就写真文字符（不要描述成"写着标语"）。
- **Alpha 透明**：V5 支持直接出透明通道（好做贴纸/立绘合成）。
- **Undesired Content**：全局负向框，支持 `{}`/`[]` 与数值权重；`rating:general` 是官方质量标签里出现过的安全向写法。

## 9 项目内出稿模板（角色立绘 · tag 轨）

```text
1girl, solo, adult, mature female, <角色锚：发型/瞳色/发饰>, <服装：材质优先，件数少而准>, <姿态/视线>, <场景：地点 + 时间 + 前景/背景一句>, <机位：景别 + 视角>, <光：方向 + 光比 + 色温>, {<关键道具>}
```

Undesired Content（按需，短而准，不堆通用长单）：

```text
<本镜真实风险的实例：no plastic, no printed logos, extra digits, cropped head, child, minor, underage, loli, shota, aged_down>
```

**纪律**：`{ }` 一次只加 1-2 个关键项；negative 每镜现配、短、只点名本镜真实风险（与 `image/illustration-prompt` 的 Targeted negative 同一条）。
