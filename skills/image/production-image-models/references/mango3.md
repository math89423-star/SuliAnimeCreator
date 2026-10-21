# Mango 3（mage 平台 mango-v3）出稿手册

> 来源：Mage 官方文档 `docs.mage.space`（模型页 `/models/mango`、提示词页 `/prompting/basics`、参考页 `/features/references`、API 页 `/api/models/mango`）。
> 一句话：**自然语言 + 四件套（主体 → 场景 → 光 → 取景）**；Mango 的强项是"指令必须落地"，同一张脸/同一件衣服/同一个场景靠 `@handle` 跨图复用。

## 1 模型形态（先认清再下笔）

| 项 | Mango 3 |
|---|---|
| 形态 | 自然语言（不吃 tag 串，不认 `(word:1.3)` 权重括号） |
| 质量咒语 | 无意义：`masterpiece / best quality / 8k / cinematic` 一律不写 |
| 负向栏 | **没有**（接口无 `negative_prompt` 字段）→ 不输出负向段 |
| @handle | 支持（Mango 3 / 3S / 2；**Mango 一代不支持**）；角色与参考图共享 10 张额度 |
| LoRA / ControlNet | 无 |
| 分辨率 | Mango 3 = 1K / 2K；Mango 3S = 2K / 3K；Mango 2 = 2K / 3K / 4K |
| 比例 | 21:9 / 16:9 / 3:2 / 5:4 / 1:1 / 4:5 / 2:3 / 9:16 / 9:21（默认 4:5） |
| 编辑 | 能吃垫图重绘（`image` + `additional_images`） |

## 2 提示词骨架（官方四件套）

```
[主体：谁/什么 + 关键外观 + 服装] [场景：在哪 + 空间关系], [光：光源 + 方向 + 色温], [取景：景别 + 镜头]
```

- 一句到两句，逗号串联，**主体在最前**。
- **光**与**取景**是官方点名"人人都漏"的两件，必写。
- 官方范例：
  ```text
  a mountain climber in her 40s on a ridge above the cloud line, warm backlight at dawn, waist-up portrait, 35mm
  ```

## 3 @handle：角色与参考图怎么挂

- 账号里保存过的**角色**（Characters，保脸）与**参考图**（References：物体 / 地点 / 姿势 / 服装）都能用 `@名字` 挂进来。
- 官方范例：
  ```text
  @sasha wearing @redcoat, standing in @cafe, evening light, 50mm
  ```
- **只写真实存在的 handle**：接口遇到解析不到的 `@handle` 直接 400 拒单（`invalid_config`），一单全废。IR/文案里没有的 handle 就不写，改用自然语言描述。
- **引用是约束不是命令**：提示词跟参考图打架时得到的是折中，不是覆盖。
- **多参考不是越多越好**：超过几张模型会开始"平均"，画面变糊；一次加一张，看清它各自改了什么。

## 4 排除元素：没有负向栏怎么办

- Mango 无负向栏：想"别出现某物"，改成**正向陈述**（写画面里只有什么），别写排除清单。
- 官方口径：确需强排除时换到有负向栏的引擎（Mage 侧的 Guava，或本仓的 NovelAI）。
- 画面内文字是 Mango 的弱项之一：确需文字就把**内容 + 位置 + 字形**写进正文（`a sign reading "OPEN" above the door`），别靠负向去压。

## 5 参考图通道

| 通道 | 用途 |
|---|---|
| `@handle` | 账号已保存的角色/参考图，跨图复用同一张脸、同一件衣服、同一个场景 |
| `image` | 本次请求的主参考图（垫图重绘） |
| `additional_images` | 本次请求的追加参考图；Mango 3 总额度 10 张 |

- 垫图重绘（编辑形态）：提示词写 Edit 指令，**保留什么 / 改成什么各一句**：
  ```text
  Edit the image: keep the room layout and warm window light, change the girl's outfit to a red coat.
  ```
- 参考图越多不等于越准；先挂最关键的一张。

## 6 成人向口径

- Mage 侧有内容政策与 Mature Mode 开关；出稿前按平台规则确认档位。
- Mango 无负向栏这一条在成人向同样成立：**不要**为了规避审核写含蓄词——本仓口径是直白词直接用（器官/行为/体液照 `video/nsfw-directing/references/acts-lexicon.md` §9 写），含蓄＝模型往 SFW 收敛，画不出也画歪。
- 需要强负向（挡掉画歪的肢体等）时走有负向栏的引擎。

## 7 本项目出稿模板（角色/场景 → Mango 3）

```text
<主体：谁 + 关键外观 + 服装> <场景：在哪 + 空间关系>, <光：光源+方向+色温>, <取景：景别 + 镜头>
```

有 @handle 时把主体/服装/地点换成 handle：

```text
@sasha wearing @redcoat, standing in @cafe, evening light, 50mm
```

要点复述：
- **主体在最前**，光与取景必写；
- 具体物理量 > 形容词（`warm backlight at dawn` > `dreamy atmosphere`）；
- 连贯短句，不写 tag 串、不写质量咒语、不写分辨率/比例/步数/seed；
- 一次只改一个变量（光/镜头/主体/风格四者之一），否则失败无法归因；
- 出图管用的那版**提示词 + seed 一起存**，回炉时能原样复现。
