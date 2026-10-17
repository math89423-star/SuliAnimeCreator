# OSS Subject Registry（多镜一致性锁 · 借鉴备忘）

> 来源：
> - `jnMetaCode/ai-shortfilm-prompts/templates/project-planner.md`（Subject registry + Atmosphere lock，原 MIT）
> - `hyyyyyyz/dramai/src/types/domain.ts`（Character/Storyboard/Asset 类型）
> - `gzxx-2025/aid-studio/sql/aid-init.sql`（aid_role_prop_scene / form / form_image / aid_scene_plot / aid_storyboard / aid_audio_record）
> 本文件只借数据结构，不改变本项目 `short-drama-assets` 的 canonical 归属。

## 1. Subject Registry（Shot 1 之前先填）

| Portrait # | Role | Face/features（逐字锁定） | Clothing/props（材质优先） | ≥2 imperfection anchors（每镜必现） |
|---|---|---|---|---|
| Portrait1 | 主角 | | | |
| Portrait2 | 配角/动物 | | | |
| Portrait3 | 场景参考 | | | |

规则：
- Portrait 编号全片固定，不中途换位（对应 aid-studio `name_normalized + aliases_name` 去重键）。
- 每镜 Character & Scene 段必须逐字复述本表措辞，不改写近似词。
- 先出首尾两镜定住长相，再填中间（pet-lifetime / family-recipe 两篇即此做法）。
- dramai 映射：`Character{referenceAssetId, locked}` = 本表 Portrait 行已绑定定妆图；`locked=true` 时分镜直接用该图做图生图源。

## 2. Atmosphere Lock（全片粘贴同一段）

```text
Core theme tags: {{3-6 tags, | separated}}
Camera + lens combo: {{e.g. Sony Venice + Canon K-35 / IMAX + Panavision C-series}}
Color & tone: {{one locked description — write once, copy verbatim}}
Grain / style core: {{}}
```

规则：各镜 Stage 3 逐字粘贴，不改写；发现第 4 镜颜色描述与第 1 镜差一个词即停，回贴本节原文（防色彩漂移）。

## 3. 可选落库字段（对照 aid-studio / dramai，只建议字段名）

- asset：`{name, aliases[], asset_type, introduction, profile_data, expected_appearances[{id, change_reason}], prompt_text, image_url, is_use, reference_images[], voice_binding{voice_id, speed, pitch, emotion}}`
- storyboard 镜：`{scene_code, shot_number, script_content, visual_description, dialogue, reference_assets, shot_size, camera_angle, camera_movement, composition, lighting, color_tone, duration_sec, image_prompt, video_prompt, status}`
- 专业版加 `shot_group{group_code, display_code}`；配音 `audio_record{storyboard_id, tts_text, voice_model_id, timbre_code, enable_lip_sync, status}`。
