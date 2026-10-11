# skills 规范（SuliAnimeCreator 统一存放）

 canonical 路径：`skills/<领域>/<名称>/SKILL.md`，全小写 kebab-case。

## 领域划分
- `character/` 原创角色设计：人设、服饰、款式图
- `image/` 单张插画总监：构图机位、提示词、SVG绘制
- `story/` 文本故事+剧本分镜+导演：发散、写作、资产、分镜、评审、导演
- `video/` 视频导演：H3/转绘/投喂

## 14 个 skill 一览（原路径→新路径）
| 新路径 | 来源 | 用途 |
|---|---|---|
| `character/garment-flat` | `D:\SuliCharacterMaker\skills\garment-flat` 全量（含references/scripts/templates） | 服饰flat三视图+工艺表+POM，后端服装生成链用它 |
| `character/character-design` | `SuliComfyUIAgent/.opencode/skills/character-design` | 角色身份冻结 SOP |
| `character/costume-design` | `ComfyUIAgent costume-design` | S1-3b 服饰选型定样 |
| `character/aesthetic-fashion-design` | `MirrorStage .opencode/aesthetic-fashion-design` | 先定方向再画 |
| `image/composition-camera` | `ComfyUIAgent composition-camera` | STEP2 机位透视尺子 |
| `image/illustration-prompt` | `ComfyUIAgent illustration-prompt` | 中英对照插画 prompt |
| `image/svg-illustration-craft` | `MirrorStage svg-illustration-craft` | SVG分区+resvg回看 |
| `story/creative-divergence` | `ComfyUIAgent creative-divergence` | 3-5异质发散 |
| `story/short-drama-write` | `ComfyUIAgent short-drama-write`（含agents/assets/references/scripts） | 剧本写作 |
| `story/short-drama-assets` | `ComfyUIAgent short-drama-assets` | 资产拆分 |
| `story/short-drama-storyboard` | `ComfyUIAgent short-drama-storyboard` | 分镜脚本 |
| `story/short-drama-review` | `ComfyUIAgent short-drama-review` | 审查 |
| `story/drama-director` | `MirrorStage backend/app/skills/drama-director`（含LICENSE/PROVENANCE） | 九宫格+Seedance导演判断，只借文本不走生成 |
| `video/h3-prompt-writing` | `ComfyUIAgent .agents/h3-prompt-writing` | H3视频字段校准 |

## character 域精修边界（2026-10-11，有交叉已去重）
- `character-design`：身份层 canonical（三锚/三色/选型单/身份对标/评审清单），唯一写 `character.md`。
- `costume-design`：只做个性层服装细化（部位矩阵/流派包/双层/分层L1-L5/大胆基线/素体三母版），三锚三色选型只引用不重定，服装层对标不碰脸发。
- `aesthetic-fashion-design`：只做画前通用检查（品类几何/纹样四层/工艺mm/zoning/反模式），配色只登记比例不讲理论。
- `garment-flat`：只做代码落盘（params→generate.py→flat.svg+门禁+事故库），不发明审美。
- 交叉点已收敛：三锚三色→character-design；服装对标→costume-design；几何纹样工艺→aesthetic；落盘门禁→garment-flat；palette.html 各家只查不定义。

## image/story/video 域精修边界（2026-10-11，同类一起修）
- image：机位构图透视底/镜头语法/空间覆盖→`composition-camera`；8-block/tag转译/风格头/Vague ban→`illustration-prompt`（机位词表不重定）；通用SVG图层渲染→`svg-illustration-craft`（服饰flat归 garment-flat）。
- Scene Bible：空间覆盖表→composition，prompt措辞（母版/派生/入场）→illustration，验收→review，建立→storyboard。
- story：发散→`creative-divergence`（身份发散归 character-design）；剧本→write；资产锁面建立→assets；分镜注入+边界→storyboard；审查验收→review；`drama-director`只借导演判断不走生成。
- video/运镜：落幅是什么+动因→composition，H3对齐行/句式/时间预算→`h3-prompt-writing`。
- MCP：prompt tag检索→illustration，机位例文→composition，锁死不串库。

## 工程 skill（2026-10-11 联网补，非自编；web_search 401 改 web_fetch 直取）

| 路径 | 联网依据 |
|---|---|
| `engineering/code-programming-review` | [Google looking-for](https://google.github.io/eng-practices/review/reviewer/looking-for.html) + [How to review](https://google.github.io/eng-practices/review/reviewer/) + [PEP 8](https://peps.python.org/pep-0008/) |
| `frontend/frontend-aesthetics` | [Element Plus Design](https://element-plus.org/en-US/guide/design.html) + [Vue Production](https://vuejs.org/guide/best-practices/production-deployment) + [Vue Performance](https://vuejs.org/guide/best-practices/performance) |
| `backend/restful-modular` | [Flask Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/) + [REST design tutorial](https://restfulapi.net/rest-api-design-tutorial-with-example/) |

## 命名铁律
1. 目录名 = skill 名 = `SKILL.md` 内 `name:`，三处一致，不一致拒绝落库。
2. 只允许 `a-z0-9-`，不许大写/空格/中文。
3. 每个 skill 必有 `SKILL.md`，配套按需 `references/ scripts/ templates/ agents/ assets/ examples/`，不另起名字。
4. 新增 skill 先定领域再定名，模板抄 `character/character-design/SKILL.md` 头。
5. 运行期 `backend/app/skills/drama-director` 是 `skills/story/drama-director` 的同内容副本（docker context 内要用），改完记得同步。
