# 查证协议（不确定就去查，别猜，也别现造词）

> 场景：写镜时遇到不确定的**体位英文名/行为术语/画面可读性/物理是否成立**。
> 规矩：查证是出稿流程的一部分，不是可选项；查完只留**术语**，不留素材。
> 本项目**不直连生成、不存素材、不共享 key**（见 `docs/POSITIONING.md` §4），查证同样遵守。

## 1 什么情况必须查

- 想在正文里用一个自己没把握的英文词（体位、动作、道具、身体部位）。
- 不确定某体位在**这个景别**里读不读得出来（比如 full 拍插入必然读不出）。
- 不确定两个动作能不能在 5 秒里衔接（换体位/翻转/起身）。
- 不确定某个 tag 在动画成人向语境里的确切含义（booru 词常有反直觉定义）。

**不用查**：已经在 `positions-lexicon.md` / `acts-lexicon.md` 里的词——直接抄，别重复劳动。

## 2 查证链路（按顺序，够用就停）

### 第一站：本地搜索（首选，免 key）

```bash
curl -s -G "http://127.0.0.1:5001/api/v1/tools/websearch" --data-urlencode "q=<关键词>" --data-urlencode "n=8"
# 例：q="danbooru tag wiki doggystyle" / q="anime sex position terms glossary"
curl -s -G "http://127.0.0.1:5001/api/v1/tools/webfetch" --data-urlencode "url=<命中的url>"
```

注意 q 必须 URL 编码（中文裸写会 400）；返回 `data.results[]`（title/url/snippet/source）。

### 第二站：booru tag wiki（动画成人向的 canonical 术语层）

这是本项目最该依赖的术语源：动画成人向的**构图与行为定义**几乎都在 booru tag wiki 里，
tag 名就是业界通用词，且有"别称 / 常见误用 / implications"三件信息。

- 目标站点类型：`danbooru.donmai.us/wiki_pages/<tag>`、`gelbooru.com` wiki、`rule34.xxx` wiki 页面。
- 查法：本地搜索里带 `site:` 或关键词组合，例：
  `q=danbooru wiki_pages mating_press` / `q=gelbooru wiki paizuri`。
- 干什么用：确认 ①canonical 拼写（`doggystyle` 还是 `doggy_style`）②别称 ③定义边界（哪些动作算、哪些不算）
  ④implications（这个 tag 通常连带哪些构图词，如 `nsfw`、`rating_explicit`、姿势前提）。

### 第三站：图像站（只在"构图读法"卡住时看）

当文字定义仍然无法判断"这个体位在这个机位下长什么样"时，才看图像流确认读法。

- 站点类型：booru 系 tag 流（`gelbooru`/`rule34`）、pixiv 成人向 tag（`R-18`）、twitter 成人向画师 tag。
- **只用来确认**：机位读法、遮挡方式、景别适配、肢体关系是否成立。
- **禁止**：把参考作品的具体构图、画师角色、真人形象、摄影作品带进 prompt（本项目只做原创虚构角色）。
  抄结构不抄作品。

## 3 转译三步（查完必须落地成正文）

1. **术语**：booru tag / canonical 名 → 记下来（例：`prone_bone`）。
2. **画面**：在词表里补"框内可见什么"（例：俯卧躯干、压背的手、脸侧贴床）。
3. **正文**：转成 H3 自然语言句——锁位 + 接触点 + 单事件 + 反应；**不许把 tag 汤、站名、URL、参考编号写进正文**。

## 4 查证纪律（红线）

- 只查**术语与读法**，不下载、不入库、不转发任何素材（本项目不做素材库）。
- 不登录任何站点、不填任何凭据、不绕过付费墙或年龄门。
- 不把查到的**真人可识别长相**写进任何 prompt；作品与角色一律虚构化。
- 查证结果只在本会话内用于出稿；不回写词表以外的运行时数据区。
- 查不到 → 用词表已有的近似 canonical 词 + 更保守的写法（少写一个动作，别现造词）。

## 5 兜底话术（当用户说"这个体位你没写"）

照实说"词表里没有，我去查定义"，然后走第 2 节链路，**查完必须补一句**：
`已按 <canonical 词> 出稿；需要的话我把它补进 positions-lexicon.md 第 N 节。`
——查证过的新词要沉淀回词表，下次不用再查（本文件是项目资产，不是一次性消费）。
