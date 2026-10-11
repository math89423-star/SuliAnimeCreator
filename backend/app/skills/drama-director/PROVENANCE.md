# 导演 Skill 出处说明（PROVENANCE）

- Skill 名：`drama-director` v2.0.0（短剧/漫剧导演）
- 来源（网络，非本项目编写）：
  https://github.com/kianaliang-dev/drama-director-skill
- 拉取文件（原样，未改一字）：
  - `SKILL.md`（raw：`https://raw.githubusercontent.com/kianaliang-dev/drama-director-skill/main/SKILL.md`）
  - `LICENSE`（MIT，Copyright (c) 2026 Kiana Liang）
- 拉取时间：2026-09-29；若上游更新，重新 curl 覆盖即可。

## 使用边界（本平台约束，非导演指令）

1. 导演能力（节拍拆解、场景档位 Archetype Router、三段结构、硬约束、双重对比剪辑、
   语言合规）**全部来自 `SKILL.md` 原文**，本平台不自写导演规则替代。
2. `SKILL.md` 中 Step 3 / Step 4.7 / Step 5 的生图、生视频、轮询、汇总动作，
   与本项目“不接任何图像/视频生成 API”边界冲突，**一律跳过**：
   只执行分镜设计部分（Step 2 节拍 + Step 4 镜头语言/约束/合规）。
3. 为把 skill 输出落进本平台 `Shot` 表，仅追加一段机器可读输出格式约束
   （见 `llm_client.py` 末尾 `FORMAT_APPENDIX`）：它只规定序列化格式，
   不规定任何导演判断。
4. 附录 v2（门对齐）：为让拆完直达生成级，附录追加了三条**机械约束**
   （锁面逐字注入 / 过程词禁用表 / 相邻镜边界照抄），以及输出字段扩展
   （geo/站位/起终边界/visual_basis）：这些是本平台结构门
   （CON-07/SHT-10/CON-01/AST-05）的原文复述，不含审美与导演判断；
   落库前另有确定性修复 `repair_drafts`（删过程词/补锁面/补空缺边界），
   同样只补机械缺口。导演判断仍 100% 来自 skill 原文。
