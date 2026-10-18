# PixAI 视频：模型与面板速查

> 来源：PixAI 官方 I2V 教程 + 视频文档。用于选型、面板设置与相机动词查表。

## 0 界面（專業档）当前阵容 —— 2026-10-12 实测（以界面为准，docs 落后）

| 型号 | 界面标签 | 说明 |
|---|---|---|
| **Tsubaki Video** 🆕 | 多圖參考 · 支援音訊 | 新旗舰视频模型；官方 Oct 6 周报已提及；docs 未出专页 → 按 v4.0 家族口径 |
| **Tsubaki Video Flash** 🆕 | 多圖參考 · 支援音訊 | 上面的快速档，能力标签相同 |
| V4.0 Lite Preview | 多圖參考 · 影片參考 | v4.0 轻量档 |
| V3.2 ⚡ | 精準跟詞 · 支援音訊 | 提示词遵循强 + 配音 |
| V3.0 Lite ⚡⚡ | 複雜動作 · 首尾可控 | 界面上叫 V3.0 Lite（docs 里是 High Consistency / Flash） |
| V2.7 | — | 高动态、相机下拉 |

> 界面文案与本文冲突时**以界面为准**，并回写本文件。

## 1 六模型对比

| 能力 | V4.0 Preview | V4.0 Lite | V3.2 | V3.0 HC | V3.0 Flash | V2.7 HD |
|---|---|---|---|---|---|---|
| 运动质量 | 顶级 | 日常好用 | 自然有表情 | 稳定克制（偏僵） | 简单动作 OK | 高能、电影感 |
| 相机控制 | 细粒度 | 不错 | 模型驱动 | 可用但僵 | 基础 | **独立相机下拉** |
| 提示词遵循 | 很强 | 强 | 强 | 很严（宁可反直觉） | 需很精确 | 中（画面优先） |
| 一致性 | 优秀 | 很好 | 转场顺 | **最强** | 快速可接受 | 复杂场景会漂 |
| 最长时长 | **15s** | **15s** | 5/10s | 5/10s | 5/10s | 5/10s |
| 参考输入 | 多图+参考视频 | 多图+参考视频 | 首/尾帧 | 首/尾帧 | 首/尾帧 | 仅首帧 |
| 速度 | 中 | 快 | 快 | 中 | 最快 | 较快 |
| 独有 | Multi-Reference、15s | 同能力更省 | 🎙音频生成 | 💃 9 个舞蹈预设 | ⚡ 最快 | 🎥 相机下拉 |
| 最佳用途 | 冲刺高质量成片 | 日常/概念探索 | 有声剧情片 | 锁角色锁画风 | 草稿与快速测试 | 大动作镜头感 |

## 2 界面与设置

- **提示词栏**：左侧 `Start Frame` + 可选 `End Frame`（中间箭头表示过渡），右侧提示词框。
- **控制条**：模型选择（Basic / Professional 两个档页签）→ 时长 → Show a Demo（官方示例）。
- **内容模式**（右上角下拉）：`Normal`（仅 SFW）/ `Enhanced / Professional`（Plus+ 会员；成人向通道）。
- **Add Audio**（v3.2 与 v4.0 系列）：`ON`（选语言 → 台词直接写进提示词框，自动配音对齐）/
  `SE Only`（仅音效）/ `OFF`（全静音）。语言：JA / EN / ZH / KO 等。
- **Add Audio ON 时的写法**：台词写进提示词框，不要单独挂音频文件；只有想借"音色/音乐气质"时才用 `@audio1`。
- **Start/End Frame 策略**：想锁定收尾姿势与构图时给 End Frame，模型会算最平滑的过渡；
  只给 Start Frame 则完全靠提示词即兴。

## 3 两种参考模式（v4.0 系列）

- **Keyframe 模式**：`Start Frame`（+可选 `End Frame`）锁第一帧/最后一帧。构图、姿势、背景全锁死。
- **Multi-Reference 模式**：`@image1-6` 作为语义参考（身份），姿势与环境由提示词决定。
  `@video1-3` 借运镜与节奏；`@audio1-3` 借音色或音乐气质。
- **两者互斥**：一次生成只能选一种。
- 组合写法示例：

```text
@image1 character is the subject throughout this video, keeping her hair gradient, eyes, and outfit at all times.
[0-3s] She stands in the scene from @image2, turning her head toward the window.
[3-6s] The camera slowly pushes in as she lifts her hand to the glass.
Follow the slow camera pacing of @video1.
```

## 4 相机动词表（官方）

| 类型 | 写法 | 最佳用途 |
|---|---|---|
| Push In | `camera slowly pushes in from wide to close-up` | 情绪推进 |
| Pull Back | `camera pulls back to reveal the room` | 交代环境 |
| Pan | `camera pans smoothly from left to right across the scene` | 横扫揭示 |
| Tilt | `camera tilts up from her feet to her face` | 角色介绍 |
| Orbit | `camera orbits around the subject clockwise` | 动态展示 |
| Track | `camera tracks alongside as she walks` | 跟随动作 |
| Crane | `camera cranes up from ground level to a bird's eye view` | 尺度变化 |
| Dolly | `smooth dolly shot moving forward while maintaining focus` | 电影感推进 |

**V2.7 特例**：它带独立相机下拉（水平/垂直摇镜等），选了之后提示词只管场景与动作，不要重复写运镜。

## 5 时长与成本

- v4.0 系列 5-15s 可选；v3.x / v2.7 只有 5s 与 10s。
- 视频消耗远高于出图（起步约 16,000 credits），单次生成 1-5 分钟。
- 会员：视频功能需 Starter+（Normal 模式）；Enhanced 模式需 Plus+；免费号不可用。
- 迭代省钱法：结构测试全部丢给 `V3.0 Flash` 或 `V4.0 Lite`，只把终稿交给 `V4.0 Preview`。

## 6 常见问答（官方 FAQ 摘）

- **参考图数量**：上限 6 张；实测 2-3 张胜过 6 张（多图会平均化五官）。
- **参考图 vs 起始帧**：参考图是语义身份；Start Frame 在 Keyframe 模式下锁第一帧。两模式互斥。
- **日语/韩语台词**：写原文字符（日文 `「」`、韩文 `""`），**不要罗马字**——罗马字出不来可懂音频。
- **时长上限**：单次 15s；多个参考视频的**合计**时长也要 <15s。
- **草稿用哪个**：`V4.0 Lite Preview` 或 `V2.7 (High Dynamics)`；终稿再上 `V4.0 Preview`。
