# NSFW 本地知识库（KB）—— 词条层

> 这一层解决**「该怎么描述、怎么写」**，是 skill 的**资料底稿**：先查证落条，再提炼进
> `positions-lexicon.md` / `acts-lexicon.md`（canonical 主表）。
> 主表是**结论**（写稿直接照抄），KB 是**证据与别名层**（含来源、热度、中文/日文别名，可回溯、可扩写）。

## 为什么要有它

1. **不许现造词**：术语第一次出现必须有源（同 `references/research-protocol.md` 的纪律）。
2. **别名收敛**：同一个东西有 5 种叫法（中/日/英），KB 负责把它们映射到**一个 canonical tag**。
3. **发现而不是回忆**：用共现数据（related_tag）系统性展开词表，而不是靠"我记得好像有这个词"。
4. **三方复用**：skill（agent 写稿）、前端（NsfwGuide 页）、拉片报告（引用同一套 canonical 词）。

## 数据源与访问方式

| 用途 | 接口 | 说明 |
|---|---|---|
| 发现词表 | `https://danbooru.donmai.us/related_tag.json?query=<tag>&limit=50` | 返回**共现 tag + 频率 + 热度 + 分类**；从 seed 出发滚雪球 |
| 定义 + 别名 | `https://danbooru.donmai.us/wiki_pages/<tag>.json` | `body`＝定义正文（含 `[[相关tag]]`）、`other_names`＝**别名（常带中文/日文，如 `cunnilingus → 舔阴`）** |
| 热度 | `https://danbooru.donmai.us/tags.json?search[name_matches]=<tag>` | `post_count`＝流行度；**热度即权威度**（同义 tag 里选热度高的做 canonical） |

**访问路径（重要）**：容器**直连不可达**（`Network is unreachable`），只能在**宿主侧走代理**抓：
```bash
cd skills/video/nsfw-directing/references/kb
python3 _fetch_booru.py expand     # 共现展开 → _candidates.json（缓存 _cache/，可续跑）
python3 _fetch_booru.py fetch      # 取定义/别名 → _raw.json + _raw.md（速览表）
```
- 脚本走 `BOORU_PROXY`（默认宿主代理 `http://172.31.160.1:7897`）。
- 只取**公开 wiki 文本**（定义/别名）；**图像站只用于确认读法**，不做取证、不下载素材。

**三条血泪教训（2026-10-17 第一次建库实测，别再踩）**

1. **必须用诚实 UA**：`User-Agent: SuliKB/0.2 (+local craft knowledge base)` → 200；
   **伪装浏览器**（`Mozilla/5.0 ... Chrome/126`）→ **403 Forbidden**。danbooru 的 WAF 专挡"半像浏览器"的脚本。
2. **必须节流**：无间隔连发 45 请求即被限流（表现为大面积 403/超时）。脚本内已加 1.0-1.2s 间隔与 429 退避。
3. **失败不落缓存**：早期版本把失败（空结果）也写进 `_cache/`，导致"看起来跑完了其实是全空"。
   现在 `cached()` 只在结果非空时落盘，重跑自动补。

## 词条字段（分类 md 的每张表都必须带这些列）

| 列 | 含义 |
|---|---|
| 中文名 | 优先取 `other_names` 里的中文别名；没有就由我方定名（须与日文/英文对得上） |
| canonical tag | 选定的 danbooru tag（**同义里取热度最高**）；写稿进 tag 轨就用它 |
| 英文写法 | 自然语言轨/正文用的词（可与 tag 不同，如 tag `doggystyle` → 正文 `from behind`） |
| 定义 | KB 结论式摘译（不是照抄 wiki 全文；英文原文片段留在 `_raw.json` 可回溯） |
| 框内可见 | 画面里看得见什么（构图/身体部位/构图；决定了能不能被画出来） |
| 写法要点 | 单镜一句话的写法提示（锁位/节奏/常见翻车），与项目 5 秒单事件纪律一致 |
| 热度 | post_count（量级即可，判断词是否主流） |
| 源 | tag 名（=`https://danbooru.donmai.us/wiki_pages/<tag>`） |

## 分类文件

| 文件 | 覆盖 |
|---|---|
| `foreplay.md` | 前戏：亲吻 / 手爱 / 口爱 / 爱抚（舔阴、口交、乳首、抚摸、脱衣…） |
| `positions-extra.md` | 体位姿势：danbooru canonical 体位表（补 `positions-lexicon.md` 21 条之外的别名与热度） |
| `play.md` | 玩法：多P / 束缚 / 道具 / 玩具 / 素股 / 乳交 / 露出 / 寝取张力… |
| `during.md` | 进行时：行为与节奏的 canonical 词 + 常见可见层组合（与 `acts-lexicon.md` §1/§9 对齐） |
| `aftercare.md` | 事后：相拥 / 清理 / 抚摸 / 睡颜 / afterglow 写法 |
| `anatomy-fluids.md` | 器官与体液：canonical + 别名（是 `acts-lexicon.md` §9 直白词表的**别名证据层**） |

## 落条 → 提炼（扩写协议）

1. **加词**：把新术语写进 `seeds.txt`（按分类加 `# 分类` 段），跑 `expand` + `fetch`。
2. **查证**：看 `_raw.md` 速览（热度/别名/定义）→ 同义 tag 里**取热度高的**做 canonical；拿不准的定义回 `wiki_pages` 读全文。
3. **落条**：写进对应分类 md（字段见上），**每条都要有热度与源**。
4. **提炼**：stable 的结论（canonical 名、写法要点）收进 `positions-lexicon.md` / `acts-lexicon.md`（主表）；
   KB 只留证据与别名。**主表有、KB 没有 = 可以；KB 有、主表没收 = 待提炼（不算漏）**。
5. **写稿引用**：报告/镜头卡/提示词里引用 canonical 词；出现新别名时，回 KB 补一行（并注明源）。

## 覆盖度（滚动更新）

| 分类 | 状态 | 备注 |
|---|---|---|
| 前戏 | ✅ 首批（22 条） | `foreplay.md`：亲吻/口爱/手爱/爱抚/乳首/脱衣 + 前戏段编排建议 |
| 体位姿势 | ✅ 首批（21 条） | `positions-extra.md`：canonical + 中日别名 + 热度（主表 21 条 curated 仍在 `../positions-lexicon.md`） |
| 性爱玩法 | ✅ 首批（25 条） | `play.md`：束缚/道具/玩具/多人/露出/NTR 张力（含两条红线：只写自愿、不写疼痛细节） |
| 进行时 | ✅ 首批（18 条） | `during.md`：行为/体液/表情/生理反应 + 体液落点互斥关系 |
| 事后 | ✅ 首批（9 条） | `aftercare.md`：事后证据词 + 关系收束 + 编排建议 |
| 器官/体液 | ✅ 首批（18 条） | `anatomy-fluids.md`：器官 + 体液落点/状态 + 湿度三点定律；是 `../acts-lexicon.md` §9 的别名证据层 |

**未覆盖（待扩）**：玩具细目（`onahole`/`anal_beads` 已收，缺乳房/阴蒂专用具）、束缚细目（`collar`/`leash` 已收，缺吊缚/固定点）、
cosplay/制服类玩法、双人以上构图的精确计数词。扩法见上文「落条 → 提炼」。

## 边界

- 只收**成年虚构角色**框架内的craft（与 `SKILL.md` §0 两条硬线一致：成年 + 自愿）；
  非自愿/BDSM 里的疼痛伤害细节等**不收**（`SKILL.md` 已定：不写疼痛/伤痕细节）。
- 词条是**写法工艺**，不是内容审核清单；不替代 `SKILL.md` 的档位纪律。
