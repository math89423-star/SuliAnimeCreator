# OSS 5-Stage + Negative（他山备忘 · PixAI 侧可用）

> 来源（MIT）：
> - `jnMetaCode/ai-shortfilm-prompts/methodology.md`（5-stage，Mx-Shell 体系）
> - `templates/project-planner.md`、`multi-shot-narrative.md`、`genre-camera-sop.md`、`camera-move-library.md`、`negative-prompts.md`
> 本文件只借结构与措辞纪律，不改变 `pixai-video-prompting` 的 PixAI 官方口径归属；
> 与 H3 格式互不通用，交付前先确认目标引擎。

## 1. 5-Stage（顺序不乱）

```text
1. Core theme          ← 定调（一行 tags，| 分隔）
2. Character & scene   ← 谁在画里、穿什么、在哪（Face / Clothing / Scene 三行）
3. Atmosphere & look   ← 怎么看（Visual base + Color & tone + Style core + Sound）
4. Camera rules        ← 相机怎么动（Single-shot / Edited + Move + Breathing）
5. Storyboard          ← 按秒/按镜拆（每片只讲 action / camera / VFX / sound 四件事）
```

- Stage 1 例：`gritty dark tokusatsu | broken flesh | combat-damaged transformation | post-apocalyptic battlefield`
- Stage 2 要点：`No beautification`（写明保留瑕疵比写 high quality 管用）；有参考图写死 `100% preserve features`；衣服带材质（`Matte black leather` > `black jacket`）；场景带动势（风/烟/流星）。
- Stage 3 相机仿真锚（比 cinematic feel 管用）：
  大场 `IMAX film camera + Panavision C-series (35mm, f/4)`；硬科幻 `Sony Venice + Canon K-35`；港式 noir/wuxia `Kodak 35mm vintage, bleach-bypass`。
- Stage 4 硬规则：永远带 Breathing 行（`Handheld shot. Throughout, maintain an extremely subtle, breath-like camera float…`，定镜也带，否则像 CG）；永远声明 Sound（`Sound: No score. Production audio only.` + 本流派招牌环境音）。
- Stage 5：单镜用 per-second beats，多镜用 Shot1..N，每镜四必填 `Shot size / Composition / Camera move / Story content`，动词不用形容词（Enter/turn/step back/lower head/stare）。

## 2. 禁词（Vague ban 补集）

禁：`epic, 4K, movie-quality, cinematic masterpiece, stunning, breathtaking, seamlessly, flawlessly` 类空词。
替换：真实机身+镜头型号 + 物理破损/材质细节 + 具体光比色温。

## 3. 留白式结尾（防加戏）

每条 prompt 末加一行“不发生什么”，如 `No extra characters enter. No logos or text. No camera shake beyond breath-float.`
无 negative 栏的模型（Sora/Runway/Seedance 消费端）只能用这种正向护栏写法。

## 4. Negative prefab（有 negative 栏才用）

默认块（Veo/Kling/Wan/Hailuo 专用栏，原样逗号表，不加 no/don't）：
```text
blurry, low resolution, soft focus, watermark, text overlay, subtitles, logo, distorted face, asymmetric eyes, extra fingers, deformed hands, melting/morphing geometry, oversaturated colors, plastic skin, glossy CG render, video-game look, 3D cartoon, anime shading, flat even studio lighting, perfectly clean flawless surfaces, frame flicker, ghosting, jarring hard cuts, lifeless locked-off camera
```
- Runway Gen-4 / Seedance 消费端：无可靠 negative 栏，正向描述代替（`clean five-fingered hands, anatomically correct`），`no distorted hands` 反而招出手崩。
- 按流派追加一行场景变体（horror/action/romance 各自高频翻车项），见原 `negative-prompts.md §Scenario-tuned variants`。
- Seedance 消费端锁定 5s/10s 两档，不要承诺 15s 与 negative 框；完整 4–15s 与精细控制在即梦 web / 火山引擎控制台。

## 5. 流派 SOP 用法

`genre-camera-sop.md` 五类（horror/action/romance/…）每块 = 哲学一句 + Lens pairing + Move 表（粘贴句式 + 买到的效果）+ Do/Don't + 招牌环境音。
用法：按流派取一块贴进 Stage 4，再配 Stage 3 的 lens；horror 记住 hold 得比舒服多一拍、action 记住出画右进画左方向押韵。

## 6. Magic prompt 与流派差异速查（三组 subagent 蒸馏合订）

- Magic 句（jnMeta README 原句意）：`Anamorphic widescreen. Simulated IMAX + Panavision C-series (35mm, f/4). Handheld breath-like float. No score.`
- StyleA per-second（单镜）：`Action + Camera + VFX`，按秒切 `0-2s hook + 2-8s confrontation + 8-12s cliff`，竖屏加 `faces upper-middle, 9:16`。
- StyleB per-shot（多镜）：`Shot size + Composition + Camera move + Action`，`0-3s Enter + 3-7s Through + 7-10s Dissolve`。
- 流派差异只换 Stage3/4/5：micro-drama = shot-reverse-shot + vertical / cyberpunk = city 做主体 + active environment / fashion = movement-as-content + editorial hard key；50 运镜按 technique×genre 双轴交叉取。
- 10 项自检：5 段齐 / 机身镜头 / 呼吸原句 / Sound 原句 / ≥2 残缺 / 空结尾 / 无禁词 / 无 IP 或加警告 / negative 已路由 / 单 ≤15s 多 ≤8 镜 / 末尾模型建议行。
