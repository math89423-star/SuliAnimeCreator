---
name: composition-camera
description: Plan STEP2 lens and composition for anime illustration: shot size, camera height ladder, composition rules, perspective proxy, advanced cinematic combos (depth layering / light separation), multi-shot grammar and STEP5 lighting hand-off. Use when user says STEP 2, pose, camera, composition, 透视底, 高级镜头, or needs a perspective-lighting placeholder separate from the character draft. Full illustrated manual: composition-camera.html.
---

# Composition Camera（STEP2 机位构图 canonical）

> 归属（2026-10-11 精修）：机位词表/构图法/透视底/镜头语法/Scene Bible空间覆盖以本文件为准；prompt组装8-block/ tag转译/风格头/Vague ban归 `illustration-prompt`；SVG图层渲染归 `svg-illustration-craft`；H3句式/对齐行/时间预算归 `h3-prompt-writing`（本文件只定落幅是什么、运镜动因，不写H3句）。

## 最高指令（压过一切审美词）

- STEP2 只定尺子，不盖房子：人物站位构图 + 机位。背景/道具/光影/色彩/材质一律留给 STEP3/4/5。
- 交付 = 姿态镜头 prompt × N + 配套透视明暗底（与姿态图同机位同构图）。空房白膜一律判废。
- 本地草稿不管角色一致性（瞳色/服装漂移允许），只看构图/镜头/姿态/表情的参考价值；一致性在云端恢复。

## 机位词表（vertical angle 带心理 + 度数，词义逐词对过 booru，见本节末出处）

- `eye-level, straight-on, zero tilt zero dutch`：中性平等，最稳，半身首选。机位高度 = 人物眼睛高度。
- `from above, high angle looking down ~15-30°`：压迫/弱小/被堵感。C1 靠墙抬眼用 ~30°；全身交代站位用 ~15°。
- `from below, low angle looking up`：权力/压迫反转，慎用（JK 题材易变味，能用平视就不用仰角）。
- `dutch angle ~15°`：失衡/不安。只配俯视用；平视+斜切双叠加脸必歪（C1 实测）。
- 水平向：`front` / `3/4 view` / `profile 90°` / `rear` / `3/4 back view`（回眸位）/ `over-the-shoulder` / `pov, first-person view`。斜睨类用 front 机位 + 头转向，不转机位。

### 词表出处（2026-10-11 逐词挂 booru，非自造）

- `cowboy shot` = 大腿上裁框含脸（thighs-up，见 https://danbooru.donmai.us/wiki_pages/cowboy_shot），与本表“大腿中”一致。
- `dutch angle` = 倾斜构图求动感，90° 另算 `sideways`（见 https://danbooru.donmai.us/wiki_pages/dutch_angle）；故本表限 ~15° 且禁与平视叠加。
- `wide shot` = 人全身可见但只占小部分画面（≤25% 经验线），与 `full body`（人满画面高）是两回事（见 https://danbooru.donmai.us/wiki_pages/wide_shot）；故本表禁两者同写。
- `from below` = 仰视强调重要性，但同页关联 upskirt（见 https://danbooru.donmai.us/wiki_pages/from_below）；故本表 JK 题材慎用仰角。
- `selfie` = 自拍（手臂向观者身后伸，相机可不入画，见 https://danbooru.donmai.us/wiki_pages/selfie）；故本表注“手机近大远小”。
- 景别（六选一，不叠写）：`extreme close-up` / `close-up`（脸）/ `portrait, head and shoulders` / `bust shot cropped at mid-torso`（半身，裁到胸）/ `upper body`（腰上）/ `cowboy shot`（大腿中）/ `full body` / `wide shot`（全身+留白）/ `extreme wide shot` / `lower body focus, thighs to shoes in frame`（腰下，只写裙摆做 context）。
- 防裁切：半身必带 `entire head in frame with margin above hair` + negative `cropped head, cropped chin`；全身 negative 加 `cropped feet`。

## 焦段 / 透视 / 画幅速查

- 焦段：`24mm`（戏剧拉伸）/ `35mm`（主体+读得出在哪的环境）/ `50mm`（中性）/ `85mm`（人像讨喜）/ `135mm`（压缩背景）/ `fisheye`（畸变即主题）；写数字比写 wide/telephoto 稳。
- 透视体系：一点 `one-point perspective`（灭点在框内=走廊/街道纵深）/ 两点 `two-point`（街角双墙，灭点框外）/ 三点 `three-point`（垂直线向天顶收束=仰拍高楼）。
- 画幅：人像 `3:4 / 4:5`；场景 `16:9`；概念图/头像 `1:1`（Mage Advanced 里选，prompt 不重复写；留白方向按画幅反推）。

## 特殊机位

- `surveillance camera view, cctv angle`（高角+广角=被观察感）/ `aerial shot`（航拍大全景=尺度感）/ `selfie`（手机近大远小）/ `view through a window`（窗外窥视=框内叙事）。

## 易混辨析速查（写前对一眼）

- `from above`（任意俯）vs `overhead / bird's eye`（垂直正俯）。
- 景别冲突：`close-up` + `full body` 同写=裁切混乱（六选一）。
- `dutch angle`（画面斜）vs `tilt`（镜头俯仰，静态图无效）。
- `wide shot`（人小环境大）vs `full body`（人满画面高度）。
- `pov`（机位=角色眼睛）vs `over-the-shoulder`（越肩前景）。
- `rule of space`（视线/运动方向留白）vs `negative space`（空本身是内容）。
- `symmetrical`（含环境镜像）vs `centered`（仅主体居中）。
- one-point vs two-point perspective（看灭点数）。
- `foreshortening`（近大远小现象）vs `wide angle`（镜头属性）。
- `cctv angle`（监控感）vs `high angle`（普通俯角）。

## 构图法（每次至少用 2 个，来源 Clip Studio Tips + 实战）

- 三分法：眼睛/脸放 power point（交叉点），地平线/眼位线压上或下三分线。只写主体位置不够，必须写满留白里是什么（环境/负空间/视觉母题），否则模型只能完成半张。
- 三角/金字塔：站姿求稳用正三角，动态用倒三角；双臂环胸+双脚撑地天然成三角（C3 全身成立根因）。
- 视线留白（rule of space）：人物不直视镜头时，视线方向必须留空；斜睨看向画外是本项目主表情，留白侧不放道具。
- 负空间：主情绪是孤独/对峙时，负空间就是内容，要写出"空"（`empty space in front`），不是不写。
- 引导线：墙角竖缝、墙地交线、灭点线收束到脑后/眼睛，让眼睛先落地再看脸。
- 对称/画框框：墙角两面天然对称框，人物压中缝；前景墙边可做 frame-in-frame，但 STEP2 只允许一条边，多了就是 STEP3 道具。

## 透视底分级（fx 实战固化）

- L1 半身像：眼位线 + 墙角两面。不画脚，无脚下阴影。竖缝落点（脊柱后/肩后）+ 眼位线穿眼 + 人物大小居中，三项写死。
- L2 全身像：L1 全套 + 墙地交线 + 脚下接触阴影 + 人 vs 墙高比例。强制项，缺一判废。
- 材质：中性灰白膜 `neutral gray clay, no texture`；明暗只分三阶（亮/中间/影）+ 压墙处接触闭塞加深。不做冷暖、不做顶光轮廓光设计，主光只写方向（如 `key from upper front-left matching reference shadow side`）。
- 与姿态图关系：分开单画两张，透视底含无五官人台只做比例尺；STEP3/5 按尺子施工，不得另起机位。

## 双 prompt 模板

本地 Illustrious tag 版（草稿）：
`score_9, ... + [pose] + [shot, angle, degrees, crop, centering] + [corner seam落点 + walls收分 + eye-level线] + plain gray + negative(rain/pipes/doors/neon/dramatic lighting)`

云端自然语言版（Pose Master，带一致性锚定 + 垫图说明）：
`same eye-level straight-on camera at subject eye height, zero tilt zero dutch, bust shot cropped at mid-torso, subject scale and center identical to reference, narrow corner with vertical seam directly behind spine, walls receding symmetrically, eye-level line passing through eyes, ...`

透视底版（云/本地通用，人台无身份）：
`grayscale clay perspective and value guide matched to the reference pose image, [同机位复述], narrow corner seam落点, walls收分, eye-level线穿眼, one-point grid脑后交汇, featureless mannequin identical pose, three-value separation, contact occlusion, no face no outfit no bricks no rain no props no neon no color`
negative 常驻：`empty room without figure, wrong camera angle, color, detailed bricks, rain, puddle, neon, pipes, doors, furniture, anime girl face, outfit details, dramatic lighting, text, watermark`

## STEP3 交接句（每次必带）

- `background perspective must follow STEP2 camera` + 复述眼位/竖缝/人物比例三项。
- 垫图声明：姿态草稿只借 pose/camera/composition，不借背景；透视底只借尺子。

## 本地实测沉淀（彩境天工 v7 + 细节 LoRA 0.5，Euler a 28 CFG 6）

- C2 平视零斜切最稳（S2C2_00001 冻结构根因）；C1 俯视+斜切双叠加脸歪手崩率高。
- 全身环胸+双脚撑地结构最全（S2C3_00001），红眼/紫眼漂移与构图无关，云端锁 `dark eyes` 即回。
- 透视底横幅 1536×1024 比竖幅线更干净；人物半身 1024×1280 batch 2。
- 云端加戏重灾区：砖纹/雨丝/管子/门锁，negative 常驻 + `no texture no props` 双压。

## MCP 路由

- 镜头机位词不确定 → 先按本表写，不调 booru（booru 是角色服装词库，不是电影机位词库）。
- 要高质量构图例文 → `civitai.search_images` withMeta=true 拿 prompt 里的 camera/perspective 段，只借机位不借人。
- 一次 STEP2 只查 1-3 次，结果沉淀为 prompt 里的机位 tag。

## 高度阶梯（垂直机位中间档，StudioBinder 心理学）

- 肩高 `shoulder-level shot`：微妙威势，不压人；对话/桌面对峙。
- 胸高 = `from below ~15°`：自信/轻威，比全平视多一口气场。
- 腰高 `hip-level shot, camera at waist height`：张力位，绷住不说破。
- 膝高 `knee-level shot`：对象显大显强，配仰视更狠。
- 贴地 `ground-level shot, camera on the ground`：巨大感/靴鞋特写（动漫足下机位）。
- **词频红利**：高角度在 9,599 条真实提示词里只占 0.74%——全场最被浪费的杠杆。清杂背景最快（镜头往下压，背景变地面）；该俯就俯，别只会平视。

## 构图法速查（完整 22 项见手册）

常用十项：三分法 / 三角形 / 视线留白 / 负空间 / 引导线 / 对称 / 画框框 / 中心 / 对角线 / 黄金分割。
备用：S 形、前景遮挡、反射镜像、重复与节奏、双人镜头、大小递进、疏密对比、视觉平衡、对比、压迫框、头顶空间、运动空间。
硬规则：每次 ≥2 个；只写主体位置不够——必须写清留白里是什么；留白单侧；引导线 ≤2 条且全指向主体。

## 高级镜头四配方（想要"电影感"先过这四条）

1. **纵深三层**：前景遮一件（虚）＋ 中景主体实 ＋ 后景压一档（长焦压缩/空气透视）。
2. **光分离**：主体与背景不在同一亮度层（受光或剪影，二选一）。
3. **引导收束**：线/光斑/视线 ≤2 条，全指向主体。
4. **节奏呼吸**：大-小递进 + 密-疏对比 + 单侧留白，忌四面均匀。

自检五问：前/中/后 ≥2 层有内容？亮度分层了吗？引导线 ≤2 且指向主体？留白是单侧的吗？有一个破格点吗？

## 落幅双可读（2026-09-30固化，运镜的落点标准）

- 起幅落幅都必须是完整可读的构图：`Start with [close/wide view], then [movement] to reveal [final view]`（Kling Pattern 2）；落幅终帧锐利定住（settle sharp），不许落在运动模糊里。
- 落幅=新信息三选一：脸/手/物（十字架/信/门/窗/字）；落空=白推，判废。
- FL2VA mechanics（对齐行/四步路径/锚点carry/时间预算）归 `h3-prompt-writing` skill，本 skill 只定落幅是什么；写 H3 句时两 skill 同查。
- 动笔前加问一嘴：这镜的落幅是哪件东西？答不上来不许写运镜句。

## 镜头语法（双人/多图必守）

- **一镜一目的总纲（2026-09-29固化）**：每镜、每切、每束光必须回答五选一——信息/权力/情绪/空间/节奏；答不上的镜头删，答不上的切镜合，答不上的光灭。禁止无意义镜头、无意义切镜、无意义运镜、无意义打光，分镜拆解第一刀先砍这四种。
- **转场五式（2026-09-29固化，H3 前三式可写）**：声音桥（声过切点不断）/ J-cut（下镜声提前 0.5s 进，`rattle enters under the end of Shot N`）/ 动作匹配（切点落动作中点，上镜抬一半下镜接完）/ 图形匹配（圆→圆瞳孔、竖线→衣褶，关键帧预埋）/ 前景穿越（柱/衣褶划过=天然擦除，`push past the column, emerging on her face`）。硬切默认，叠化后期做不进 prompt。
- **180 度线**：两人连线为轴，机位全在同一侧；双人 prompt 用「左/右 + 朝向」把轴线写死。
- **正反打**：视线互为反向、机位同侧。
- **视线匹配**：A 看画外右 → B 必须从画外左看回。
- **对话切镜（H3 执行，2026-09-28固化）**：两人对谈≥2轮必须分镜写多 `[Shot N] At 00:0X.000` 切，不许一镜演完；切点落在台词尾音（话音落→切→反应1s→下句起）；正反机位同侧、景别拉开一档（如中景↔近景），视线互为反向；单人独白才许一镜。对白 density 高时优先保切点，宁可镜短不可一镜到底。
- **人物背景双关系（2026-09-28固化，缺一判废）**：人物→镜头（机位四要素）之外，必须另写人物→背景：视线落点入背景（她看向哪，那件东西就写在哪侧，如面朝右则神像膝压右缘，禁止写"身后"这种机位系方位词）；身体朝向与背景主体的轴线关系（面对/背对/侧对写死）。三点成环：机位→人物→背景回机位，只写两条等于没写。
- **方位与视线 v2（2026-09-28固化，闭源云模型实战）**：方位词一律机位系（画面左/右/上/下、top-right、dead center），"身前/身后/左侧（人物系）"一律判废；视线=动词+目标物（`gazing at the statue knees on the image-right edge` / `looking down at the book, not at the camera`），不写"侧身/面朝"等姿态词指望模型脑补朝向；相对比例写死（`half frame height` / `child-sized relative to the table`）。英文 prompt 体积压到 150 词内，超了先砍形容词，保机位句和关系句（fal 实测：超限相干性跳水）。
- **方位介词单义（2026-09-29固化，教堂 K1 跪错行实战）**：`between` 侧向/纵向双关一律禁用——"末排凳之间"会被画成左右夹缝而不是凳外祭坛前。只许单义动词：之外=`past`/`beyond`（越过所有凳子）/ 两侧夹=`flanked by` / 之前=`a few steps before`；位置三重锁：纵向（past all benches）+ 横向（centered on the aisle）+ 距离（steps before platform），缺一即判废。
- **约束互验（2026-09-29固化，教堂 K1 自相矛盾实战）**：同一 prompt 内位置/比例约束必须先互验——写了"越过所有X"就不许再写"身后的X"（身后已无 X，模型为和解必把人塞回 X 堆里）。标尺只留不打架的两把（神像倍数+框高占比），互斥约束出现即判废，错的永远是导演不是模型。
- **主约束优先（2026-09-29固化，教堂 K1 一句话教训）**：一镜只设一个主空间关系句——谁在谁面前（如 `directly in front of the statue`），它必须是 prompt 里最短最硬的一句；配角约束（凳/窗/框高）最多一句，且只许为主约束服务。谁是主语谁先说：神像是主语，凳子是配角，不许让配角当主语。约束数与字数成反比：超 150 词先砍配角句，保主约束句；十个字能说清的事不许写五十个字。
- **身定头动（2026-09-28固化）**：转头/抬头/回眸必须分写两句——躯干朝向锁死（`torso stays facing the statue, shoulders square`）+ 只有头动（`only her head turns up-left`）。只写头不写身，模型必把全身一起转过去。
- **动作与反应分镜（2026-09-29固化，Shot2 窗颤教训）**：环境异动与人物反应同段出现时，强制拆 action（环境镜：窗颤升级）/ reaction（人物镜：转头慌）两切，不许首尾帧一镜包办。手里有首尾帧不等于必须一镜插值——首尾帧是资产，不是分镜；"保一镜过审"的省事动机一律判废，以叙事信息量为准。
- **统一时间轴（2026-09-29固化，Shot2 切点断裂教训）**：多切同段必须先画一条时间轴再分镜——切点两侧世界状态必须相等（Cut1 尾窗户剧颤→Cut2 头窗户必须延续剧颤，正文显式写）；人物反应延迟按人类标准 0.3~0.5s（切后 1s 才动=木头人）；每切的环境状态（颤/静/炸）逐切声明，不许只写在 action 镜里默认 reaction 镜继承。
- **双轴拆解 story_time vs camera_time（2026-09-29固化）**：剧本拆解与分镜拆解必须同时跑两条轴——
  - `story_time`（故事世界轴）：世界内真实发生的并行时间线。物理世界规则：没被拍到≠没发生。如本段 5s：1s 起彩窗微颤→3s 转剧颤→3.5s 圣女停祷转头，窗颤与人祷告全程并行。
  - `camera_time`（观众镜头轴）：即分镜脚本，观众看到的顺序。如 0-1s 圣女平静近景→1-3s 切彩窗微颤→3-5s 切回圣女（此时窗已在剧颤，reaction 镜必须声明延续状态）。
  - 铁律：先画 story_time（世界发生什么、何时并行），再排 camera_time（何时给谁镜头）；reaction 镜的世界状态必须从 story_time 取，不得从 camera_time 脑补；两轴时间戳逐一切对齐后才许写 prompt。
- **续帧背景逐项锁死（2026-09-28固化）**：续写上一 seg 的场景时，"同一教堂/同一牢房"四个字判废；背景每个元素逐项复述点名（石膝两倍大柔虚右缘+彩窗左+中间黑暗幽暗），位置数量缺一即废；只许声明的改动点能变，其余一字"完全一致零改动"。
- **对话切镜（H3 执行，2026-09-28固化）**：两人对谈≥2轮必须分镜写多 `[Shot N] At 00:0X.000` 切，不许一镜演完；切点落在台词尾音（话音落→切→反应1s→下句起）；正反机位同侧、景别拉开一档（如中景↔近景），视线互为反向；单人独白才许一镜。对白 density 高时优先保切点，宁可镜短不可一镜到底。

## 光位与景深速查（STEP5 交接 / 成品 prompt）

- 光位：顺光 `front light`（无影平铺=设定图光）/ 侧光 `side light`（立体最强）/ 伦勃朗 `rembrandt`（颊部三角亮斑）/ 逆光 `backlight`（剪影+发丝光）/ 轮廓光 `rim light`（只勾边不翻脸=暗背景剥离神器）/ 顶光 `top light`（眼窝影=压抑）/ 底光 `bottom light`（诡异）/ 蝴蝶光 `butterfly lighting`（美人光）/ 三点布光 `three-point lighting`（主+补+轮）。
- 光比调子：高调（亮多暗少）/ 低调（暗多亮少，必配轮廓光）/ 硬光（影缘刀切）/ 柔光（影缘羽化，动漫默认保险）。
- 氛围光：`god rays` 体积光 / `golden hour` 黄金时刻（长影暖光）/ `blue hour` 蓝调 / 窗光 / 斑驳树影 / 条纹光 / 湿润反光（`wet asphalt`）。
- 写光铁律：一个主光＋可选补光；方向+光比+色温一次写全（`key light from upper left, high contrast, warm 3200K`）。
- **光影目的（2026-09-29固化）**：主光三问——为谁打（主体/环境/气氛）/藏什么（阴影里藏什么信息）/变化对应什么转折（光变=事变，无转折不许光变）；光比=权力比（谁亮谁掌权， double check 亮的那个是不是该掌权的人）。答不上三问的光灭，等于默许随性打光。
- 景深三态：浅景深 `shallow depth of field`（虚化=指向；写 85mm + f/1.8 + 对焦点 + 主体背景距离）/ 深景深 `deep focus`（环境叙事）/ 焦外光斑 `bokeh`。

## 黑话与词频要点（社区数据）

- 词频结论：**结果词扎堆、设置词沉底**——景深 14.5%/浅景深 11.1%/特写 9.3%，而 f/1.8 只 2.0%、高角度 0.74%。写设置的人少，补上即领先。
- 相机块四行（贴 prompt 末尾）：`Camera / Focus / Distance / Composition`。
- 平视听着像废话但值得写：不指定会漂成「略低英雄机位」。
- 黑话对照：怼脸=`extreme close-up`；上帝视角=`bird's eye`；蚂蚁视角=`worm's eye`；广角大长腿=`low angle + wide + foreshortening`（脸别一起拉）；电影感三件套=`cinematic lighting + film grain + 2.35:1 letterbox`。

## 姿态动作速查（18 张线稿示意详见手册）

- 三件套：重心（骨盆位置）+ 动作线（脊柱曲线）+ 联动链（头颈肩胸腰盆腿脚一条链）。
- 常用姿势 tag：`standing` / `contrapposto`（重心偏移微 S）/ `crossed arms` / `hands on hips` / `hand in pocket` / `against_wall, leaning back` / `looking back` / `walking` / `running` / `reaching towards viewer` / `squatting, hugging own legs` / `wariza`（鸭子坐）/ `sitting on chair, knees together` / `sitting on chair, crossed legs` / `kneeling, one knee down` / `lying, on side, head on arm` / `hand on cheek, elbow on table` / `hand in hair`。
- 动势 = 前倾重心 + 对角四肢 + 飘动发衣；手永远有事做（扶/撩/插/握），但手部崩坏高发，别让手抢景别焦点。
- 机位联动：低机位配伸展、高机位配收缩；保形：转面/动作只许强化不许改型（体型 signature）。
- 二人互动 tag：`back to back` / `holding hands` / `walking side by side` / `two people facing each other` / `hugging` / `head on shoulder` / `height difference` / `princess carry` / `piggyback` / 前后站位（前景虚化）。铁律：连接点写清（手/肩/腰）+ 轴线锁死（左右+朝向）+ 身高差先行；两人同框手部翻倍，能剪影就剪影。
- 姿态↔机位速查（14 组）与情绪→机位速查都在 HTML 手册「速查表」页。
- 神态 tag：`expressionless` / `smile` / `grin` / `laughing` / `jitome`（半眯眼，50K）/ `angry, furrowed brow` / `pout` / `surprised, wide-eyed` / `blush` / `teary eyes` / `crying` / `smug`（35K）/ `looking down`（睥睨，139K）/ `glaring` / `wink` / `sweatdrop`（329K 符号）/ `gritted teeth` / `closed eyes`。铁律：**高光是情绪开关**（大高光=有生气，高光缺口=冷淡/不屑/黑化）；眼神方向单独写；远景靠眉嘴轮廓读情绪，近景才堆眼部；姿态先信脸才成立。
- 体型与细节 tag：比例（`7 heads tall` / `long legs` / `narrow shoulders` / `narrow waist` / `fingertips at mid-thigh`）+ 体型（`slim` / `curvy` / `tall` / `petite`）+ 肩型体态（`sloping shoulders` / `straight shoulders` / `upright` / `slouched` / `forward head`）+ 细节（`shiny hair` / `floating hair` / `wet hair` / `ahoge` / `eyelashes` / `shiny eyes` / `fang` / `collarbone` / `nape` / `sweat` / `hand focus` / `zettai ryouiki` 170K / `floating clothes` / `fabric folds` / `barefoot` / `hair ornament` / `nail polish`）。比例词写主体段；体型 signature 立下即保形（只许强化不许改型）；细节有预算：远景只给轮廓、半身 2-4 落点、特写才堆细节。**默认二次元女生视角**（≈95% 创作）。
- 发型 tag：`hime cut`（32K）/ `twintails` / `ponytail` / `side ponytail` / `twin braids` / `hair bun` / `double bun`（179K）/ `bob cut` / `layered hair` / `curly hair` / `wavy hair` / `half updo`（60K）/ `blunt bangs` / `see-through bangs`（空气刘海）/ `swept bangs`（162K）/ `parted bangs`（313K）。prompt 顺序：长短 + 样式 + 刘海 + 发色；发型是第一识别符，剪影测试：纯黑填充远距须认得出。
- 服装动态 tag：`skirt lift`（95K）/ `running, skirt flare` / `sitting, skirt spread` / `sleeve slipping` / `open collar, unbuttoned` / `floating ribbon` / `single off shoulder`（12.8K）/ `wet clothes`（62K；fx 端庄铁律：见水就压，不透）/ `loose socks`（22.8K）/ `untucked shirt` / `button strain` / `spread pleats` / `sleeves past wrists` / `scarf trailing` / `belt chain`。三个力：重力（垂坠滑落）/ 风与运动（裙摆飘带朝外）/ 贴体与离体；动态词 floating·fluttering·clinging·swaying·trailing。与姿态联动：跑=扬、坐=堆、抬手=滑。

## 叙事与活感（让画面「活着」）

- 公式：**动作瞬间 + 一个残响 + 一次环境接触 + 一个画外指向 + 情绪词≤1**。
- 三招：①动词换名词（`mid-stride / mid-turn / about to` 而非 `standing`）②加残响层（`still swaying, steam rising, half-open`）③情绪写行为不写标签（`tearing up but smiling` > `sad`）。
- 要素 tag：`caught mid-stride` / `steam still rising` / `reacting to something off-screen` / `palm against the glass` / `gripping the strap` / `smiling with tears` / `worn bag, patched strap` / `crooked bowtie, loose strand` / `looking off-screen` / `falling leaf, fading light` / `footprints, ripples`。
- 自检五问：正在发生？残响？环境接触？画外指向？情绪词≤1？

## 视频机位四要素（H3 每次必写，2026-09-28固化）

- 不写机位=给模型自由发挥。每镜正文必须带机位块：**站位**（机位在哪：中殿尾部中轴/牢房角落/人物身后三步）+ **高度**（眼平/肩高/腰高/膝高/贴地，写词不写感觉）+ **角度**（正直拍零倾斜/俯~20°/仰/荷兰~15°，只配俯视）+ **裁切**（大腿中/腰上/胸口/全身+留白在哪）。
- 顺序：机位块紧跟 `[Shot N]` 开头风格句之后、动作之前；运镜是机位的变化（push in/pull out/tilt），不是机位的替代——static 也要写 `static locked at eye level`。
- 远景交代空间三件：前景是什么（虚化椅背）/中景引导线收向哪/远点主体多小。近景交代裁切线（一刀切在大腿中/胸口，不切关节）。
- 双人必带轴线：左右+朝向写死，180 度线站哪侧。
- 比例双写（2026-09-28固化）：人物占比（占画面纵向几分之几/裁到哪：大腿中/腰上/胸口，不切关节）+ 人景比例（人 vs 身后门/桌/像：如人物高为门高的二分之一、跪姿仅及像座膝盖）每次必写；有参考图时写 `scale identical to reference`，新镜从零起时写具体比例。远近两人同框先定身高差，再定各自占比。
- **相对比例优先（2026-09-29固化）**：人景同框时相对句是主锁、绝对占比是辅锁——相对句缺失即判废（`her kneeling height is one-third of the statue's visible height, the statue towers at least three times her size`）；自检：人物站起来也只到背景主体腰部以下。

## 运镜必动（H3 每次必有主运镜，2026-09-28固化）

- 禁止整镜 static：`static` 只允许用在首尾定格（各 ≤2s），行进段每镜必有一个主运镜。影视剧几乎没有长时间完全静止的镜头，静止=画面死。
- 动因三选一，写进动作句：揭示（tilt up/down 开出新信息）/ 逼近（push in 压力累积）/ 释放或巡视（pull out / slow pan 交代空间）。无动因的运镜不写。
- **运镜五动因+换向落幅（2026-09-29固化）**：三选一扩成揭示/逼近/释放/跟随（truck/pan 跟人）/审视（slow arc 打量）；push 连用不许超 2 镜，第 3 镜必须换向（pull out/tilt/static）；落幅必落新信息（脸/手/窗/门/十字架），落空=白推；ease 写进句（eases in/holds/accelerates once），匀速=CG 味；运镜不抢戏（转头时 static 或反向，同向叠加超 budget）。
- **四段式运镜句（2026-09-29固化，多家教程收敛）**：`[运镜+速度] + [主体动作] + [揭示什么] + [情绪/节奏]`——"揭示什么"必填（reveal X / ending on Y / emerging on Z），缺落点=漂。速度词是独立指令（slow push-in vs crash zoom 是两种镜），该快写 fast。
- **高级运镜库（2026-09-29固化，H3 句式，小写+幅度+速度）**：POV 奔跑（`first-person POV sprinting, violent bobbing, arms at frame edges, rushing toward X`，必写身体入画）；FPV 穿行（`aggressive FPV flight, threading through A, banking past B, bursting into C, slight fisheye, motion blur`，航点 through→past→into 三站缺一即乱飞）；俯冲（`high-speed vertical dive from X straight down toward Y, ending in a sudden hover`，起点终点+急停缺一穿模）；环绕（`slow orbital arc 180 degrees`，不写 360°，5s 转不完）；crash zoom（`sudden crash zoom onto X`，一集最多一次）；whip pan（`rapid whip pan from A to B with motion blur`，A→B 同轴两侧，blur 必写）；dolly zoom（`pushes in as the lens zooms out, background stretching, vertigo effect`，反向写全）；crane（`rising from X to high above, revealing Y`，起点越低落差越大）。出处：Atlabs 2026/Seedance 官方/ScreenWeaver/Kling 3.0 Masterclass。
- 速度幅度挂情绪：累积压迫=slow + small amplitude；惊变=fast + whip/pan；呼吸感=FPV/手持全程叠 `faint handheld tremble`（次级，不占主运镜位）。
- 一镜一主运镜：行进段只写一个，定格段写 static；两者衔接写清切换点（如 0-2s static 定格，2-5s push in）。
- **Motion budget（2026-09-29固化，DirectorSKILL 引进）**：一镜预算 = 一主体动作 + 一运镜 + 一环境动，各一。超预算（窗颤升级+转头塞一镜）强制拆镜；static + 世界动供行进不算空定格，但世界动只许一种。
- **Motion load 量化（2026-09-29固化，云端架构评审引进）**：Camera/Character/Environment/Facial 四轴各计 1（多重叠加逐项+1，如转头+睁眼+张嘴=Facial 3）。Total>3 即超载，判 P1 强制拆镜或降级，不讨论。
- **空间复杂度预算（2026-09-29固化，云端架构评审引进）**：计数人物数/主要道具/前后遮挡层/换角≥90°/同步动作数；人物≥3 或遮挡≥3 或换角+运镜同镜出现，即超当前模型可靠区间，判 P1 简化（减人/减遮挡/拆镜），不许靠"写更细"硬刚。
- **Reviewer 双段分工（2026-09-29固化，云端架构评审引进）**：一审分两段先导演后生成——Director 段（叙事/节奏/信息/镜头语言/双轴，P0 为主）→Generation 段（动作负载/手/遮挡/空间/长度/negative，P1 为主）。"导演认为合理≠模型做得到"，两段结论独立写，Generation 段可推翻 Director 段的执行方式（换镜/降级）但不推翻叙事。

## 动笔三问（2026-09-28固化，写 prompt 前先答）

1. 与上一个 seg 什么关系？续写→必须点名垫哪张（main_ref 继承项逐项复述）；新开→叙述体。答不上来不许写。
   新生图 vs 编辑二选一（2026-09-28固化）：同机位同框只改神态/局部（抬头、睁眼、玻璃重影）→ 走 main_ref 编辑命令，背景像素级继承，措辞再严也替代不了一张底图；新机位/新场景/新主体 → 走首次生成叙述体。选错模式即废帧，不怪模型。
   **Bible 门禁（2026-09-29固化）**：新机位先查场景 Bible 覆盖表——表内直接派生（垫对应机位图走编辑）；表外=新增机位参考，先补 Bible 再出镜头，不许临场用文字发明机位。
2. 机位四要素+比例双写齐了吗？缺一项即废。框量先定距离：近大框（≥1/4）先反推机位离主体几步再写站位（K5 教训：1/4 近背+神像同框只能是圣女身后几步，不许写尾部/祭坛两端），框量与站位矛盾即废。
3. 人物→背景关系写了吗？视线落点、身定头动，缺一项即废。

## Scene Bible 与离散机位（漫剧空间一致性，2026-09-29固化）

- **总纲**：不要让 AI 理解整个房间，让它不需要理解整个房间。摄影机离散化：`Camera ∈ {Establishing, Medium-A, Medium-B, OTS-A, OTS-B, Close, Detail}` 八选N，不许连续 3D 运镜式临场发明。
- **story 后先判**：列场景清单逐个判——高频（≥3 镜或跨 seg 复用）必建 Bible；一次性场景（1-2 镜）不建，直接单帧处理。
- **母版标准**：空场景无人物；门窗桌椅固定结构齐；光源时间明确；透视清（灭点/眼位线可读）。母版是场景锚点，不是背景图。
- **锚点坐标**：门窗桌椅机位系方位钉死；人物站位只记相对关系（A 左 B 右、桌在中间、轴线 A↔B）。换镜头只改 Frame 不改 Blocking。
- **派生规则**：镜头机位必须命中覆盖表；大幅换机位（正面→正后方/绕背/新空间）= 新增一张机位参考；边界情况（90° 以上转向、原图未展示空间）用切镜绕开，不硬刚。
- **落盘**：`scene/<代号>/`（`scene.md` + `master/` + `cam-A/B/C.../` + `props/`）；评审见 AGENTS §5 场景 Bible 项。

## 配套手册（查完整图示与可复制段落）

- `composition-camera.html`（浏览器打开，30 页分页浏览）：220 张图示卡片覆盖 19 区（景别/垂直机位/水平机位/荷兰角/焦段透视/透视体系/构图法/特殊机位/画幅比例/镜头语法/姿态动作/二人互动/神态表情/人物细节/发型/服装动态/体型体态/光影/叙事与活感）+ 自然语言描述法 + 组合实战 8 例 + 高级镜头 8 例 + 拆解实战 3 例 + 活感工作台（死句→活句 10 组）+ 双速查表 + 易混辨析 10 组 + 避雷清单 10 条 + 黑话焚诀（黑话对照/词频榜/焚诀卡）+ 名词案例 220 词条 + 工具句 + 19 条外链。选词、看示意、抄成品段落时先查它；出图验证后回改词条。
