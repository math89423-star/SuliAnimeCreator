---
name: h3-prompt-writing
description: Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and Ref2VA. Use when rewriting multimodal requests into H3 prompt structures, composing integrated_multimodal_description, overall_soundscape, and non_diegetic_music, aligning keyframes, or defining reference labels for images, videos, and audio.
compatibility: Portable to any agent that can read local files — no external API calls, MiniMax Hub tools, or proprietary runtime required. The agents/openai.yaml file only adds optional ChatGPT/Codex UI metadata; it does not restrict the skill to OpenAI agents.
---

# H3 Prompt Writing（H3句式 canonical）

> 归属（2026-10-11 精修）：H3对齐行/多模态字段/时间预算/锚点carry以本文件为准；机位/落幅是什么/运镜动因归 `composition-camera`（本文件只做H3执行句，不重定机位词表）；本文件不拆镜，只接分镜输出的起终帧。

## Workflow

1. Identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA.
2. For base text/keyframe modes, read `references/base-en.txt` and follow its final prompt structure.
3. For full-reference mode, read `references/ref-en.txt` and follow its six-section rewrite format.
4. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.

## 落幅四步与对齐行（2026-09-30固化，FL2VA必走）

- 对齐行是死格式，首行+空一行再接字段：`How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.` N=实际终镜号，S.SS=两位小数（如8.00）；I2VA/L2VA各用自己的对齐句，不许混用（I2VA句+第二张图=尾帧被静默忽略）。
- 正文只写中间路径，四步缺一即糊：首帧态 → 可见中间变化（至少2-3个可观察状态）→ 差异收窄 → 尾帧态（`settles into the exact pose ... established by Picture 2`）。复述两帧长相不写路径=交叉淡化。
- 单shot优先：FL2VA默认一镜插值；多shot只在显式要求时用，加切则对齐行N跟着走。
- 时长先定：6-10s覆盖单次变换；改时长=对齐行+落幅句两处同改。

## 锚点carry（2026-09-30固化）

- 身份漂移的主因：衣服/颜色/关键道具只在开头写了一遍。锚点词必须写进运动句里全程携带（如伞：`raises the umbrella ... Water rolls from the expanding fabric while she steps beneath it, rotates the handle`），不能开头交代完就撒手。
- 切镜两侧世界状态相等：Cut1尾什么状态（窗剧颤），Cut2头必须延续声明，不许默认继承。

## 时间预算与失败模式对照表（2026-09-30固化）

- 预算：8s内容里动作/运镜/反应/对白/切镜抢同一时长；觉得赶=删事件，不加词。时间戳只许给切镜用，不许拿来定动作时序。
- 小变用运镜，大变才用切：切必须带新信息（主体/空间/状态/视角/时间），否则换push/pull/pan。
- 对照：尾帧不收→先加中间态，不动相机；运动糊→先调时长；乱切→删shot指令改运镜；错人说话→锁(S1)/(S2)；无端配乐→显式N/A。一次只改一个变量，双改等于没测。
## Tips for Better Results
- Always match the total duration of the description to the requested video length (4–15 seconds).
- Keep reference labels consistent (e.g. `<Picture 1>`, `<Video 1>`, `<Audio 1>`) across every section.
- Prefer concrete visual and audio details over abstract words like "cinematic" or "beautiful".
- When using keyframes (I2VA / FL2VA / L2VA), clearly state how the first and/or last frame connects to the timeline.
