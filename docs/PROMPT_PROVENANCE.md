# 提示词出处总表（历史沉淀 + 联网权威，不自造）

> 立规矩（YG）：所有提示词只认两处出处。下表每行必填出处，查不到出处的词一律删。

## A. 联网权威（2026-10-11 实取）

| 主张 | 出处 |
|---|---|
| 好 prompt 四要素：subject/setting/light/framing；一句清楚话胜过形容词堆；light+framing 最易被省却最关键 | [Mage Prompt basics](https://docs.mage.space/prompting/basics) |
| Character/Reference 用 @+名字调用（跨图一致性正道） | [Mage Prompt basics](https://docs.mage.space/prompting/basics) |
| Anime 系（Anima/Illustrious/Pony）吃逗号 tag；Pony score tags 放最前；Anima 里括号转义 | [Mage Prompt basics](https://docs.mage.space/prompting/basics) |
| 出图先存 prompt+seed 才能复现；一次只改一样（光/镜头/模型）；模型不对换模型，加词没用 | [Mage Prompt basics](https://docs.mage.space/prompting/basics) |
| 手/文字/精细重复细节是全模型通病，商用前 100% 检查 | [Mage Prompt basics](https://docs.mage.space/prompting/basics) |
| negative 是独立字段，列词不写句子；要短，长了反噬；只降概率不禁用，顽固 artifact 换模型/加 LoRA 比加词管用 | [Mage Negative prompts](https://docs.mage.space/features/negative-prompts) |
| 有 negative 栏：Anima/SDXL 系/SD1.5/SDXL/Illustrious/Pony 等；**无**：Flux 2/GPT Image 2/Grok/Mango/MiniMax-H3/Nano Banana 2 等 | [Mage Negative prompts](https://docs.mage.space/features/negative-prompts) |
| `1girl` = 画面内可见的女性角色一人（物件/画外人不算）；单人图配 `solo` | [Danbooru 1girl wiki](https://danbooru.donmai.us/wiki_pages/1girl) |
| 机位词表：`cowboy shot` 大腿上裁含脸 / `dutch angle` 倾斜求动感（90°另算） / `wide shot` 人小环境大（≤25%）≠ `full body` / `from below` 仰视强调重要性（含 upskirt 关联故 JK 慎用） / `selfie` 自拍手臂向观者身后 | [cowboy_shot](https://danbooru.donmai.us/wiki_pages/cowboy_shot) [dutch_angle](https://danbooru.donmai.us/wiki_pages/dutch_angle) [wide_shot](https://danbooru.donmai.us/wiki_pages/wide_shot) [from_below](https://danbooru.donmai.us/wiki_pages/from_below) [selfie](https://danbooru.donmai.us/wiki_pages/selfie) |

## B. 历史沉淀（D 盘三项目，文件:节）

| 主张 | 出处 |
|---|---|
| 风格锚前置（模型吃前部 token 权重高）+ moe 质量头 `score_9, score_8_up, source_anime` | SuliComfyUIAgent/AGENTS.md §4.2 |
| 写实触发词默认禁用、三眼五停写 `balanced symmetrical`、人物写法 `1girl/solo/年龄感/发眼衣表情姿势` | SuliComfyUIAgent/AGENTS.md §4.2 |
| 一致性锚定句 + 服装原文复述 + 位置双述 + 遮挡五件套 + 垫图 KEEP/CHANGE 命令体 + 禁代称 | SuliComfyUIAgent/AGENTS.md §8（以 SkyReels/转绘实战沉淀） |
| reviewer 只标点不改写、P0/P1/P2、3 轮上限、送审全文+三附件 | SuliComfyUIAgent/AGENTS.md §5 |
| H3 对齐行/I2VA 句式/三字段顺序/运镜三维/`<d>`对白/声景三层/5s 铁律 | SuliComfyUIAgent/AGENTS.md §10 + skills/video/h3-prompt-writing |
| 服饰部位矩阵 tag（`choker/cross necklace/...`）、流派包、Illustrious 实测（JK LoRA 加戏/red 爬眼/reference sheet artifact） | skills/character/costume-design（本地 Illustrious 线 1536 实测） |
| 脸标唯一/三锚/点缀落位/70-30/可生成性预警 | skills/character/character-design 身份评审清单 |
| flat 门禁（generate.py 通过/XML 可解析/QA 打勾）+ 8 条事故库 | skills/character/garment-flat §6/§8 |
| 九宫格 image_prompt 模板 + motion 三段 + Archetype Router + 硬约束 | skills/story/drama-director（ATLAS 原样，PROVENANCE 在位） |

## C. 本次纠正（联网打脸历史，联网赢）

1. negative 分模型：moe（Illustrious/Pony/Anima/SDXL 系）照常用短 negative；Mango/Flux/GPT Image 2/Grok/MiniMax-H3 **无 negative 栏**，不许写“有框就填”。（历史 AGENTS.md §4.2 笼统写法作废，以本表为准。）
2. 后端 `director/character` 生成器不输出 negative 文本（只出正文），negative 由人工按模型栏位手填——已验代码无残留。
3. 后端风格头（`high-quality 2D anime illustration, anime key visual, cel-shaded`）与质量尾（`score_9, masterpiece, best quality`）取历史 AGENTS.md §4.2（风格锚前置+moe 质量头）与 skill 教堂 Master 糊片教训（设定级头替 `2D tv anime screencap`）；`1girl, solo` 取 [Danbooru](https://danbooru.donmai.us/wiki_pages/1girl)。code 层未自造新词。
