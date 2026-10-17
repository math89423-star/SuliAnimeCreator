# OSS Director Package（先导演判断再写 Prompt · 借鉴备忘）

> 来源：
> - `62656456/ai-film-skills/skills/ai-storyboard-director/SKILL.md`（v5.8.3）+ `references/production-contract.md、shot-design-engine.md、framing-and-axis.md`
> - `skills/produce-ai-video/SKILL.md + references/autonomous-production-workflow.md`（DIRECTOR_SHOT_PACKAGE）
> - `skills/ai-short-drama-production/references/production-handoff.md、control-contracts.md`
> 本文件只借导演判断层与编译纪律，不改变本项目 `short-drama-storyboard / h3-prompt-writing` 的 canonical 归属。

## 1. 铁律：先导演判断，再写 Prompt

- `Direct before prompting. Decide what the audience must see and in what order.`
- 提示词只编码已完成的导演判断，不临时发明镜头；编译只忠实表达已定内容，不补人补戏改天气改结局。
- 落到本项目：分镜阶段先定观众信息差（何时知道什么）+ 权力转折（谁掌权何时翻转），再写关键帧与提示词。

## 2. World-State Lock（切分镜前先锁）

- 锁：空间轴线、光源世界位置/色温/光比、角色权力关系、进出场状态（`spatial_contract / visual_design / environment_baseline / filming_conditions` 四件套继承）。
- 换机位必须重算画面左右、纵深、遮挡、出框与受光；世界门墙不搬家。
- 落地字段建议：`blocking_map T0→T1→T2 + power_geometry{start,turn,end} + axis{a,b,camera_side}`；光源逐个 `Sxx{位置, 色温, 光比}`。

## 3. DIRECTOR_SHOT_PACKAGE（每镜必填）

```text
segment objective / entry-exit states / world-state lock / shot order / timing /
framing / camera / visible action / sound / cut motivation / continuity handoff
```

- 切镜动机五选一：信息 / 权力 / 情绪 / 空间 / 节奏（`Every cut must change what audience can understand`，长镜头亦需自觉，无免检）。
- 交接：持物、朝向、光源、环境进度（门合拢余程、背景人车进度），段首承接紧邻上一段真实尾态。
- 本项目映射：`起点 → 唯一动作 → 终点` 保留，追加 `剪辑动机 + 尾态交接` 两行；`critical_retention{距离, 尺度, 焦点接力}` + `decision_record` 短画框底稿保全。

## 4. 五列分镜 + 六模块母稿（编译用）

- 分镜五列：`时间｜景别/机位｜摄影机｜画面与动作｜台词/声音`。
- 六模块（同一总时长只一条母稿，不擅拆）：
  一生成任务 / 二主要主体 / 三场景状态 / 四情绪目标 / 五视觉风格 / 六分段脚本。
- 每段格式：`[起止秒点｜景别机位｜摄影过程→落点]` + 画面 + 台词（说话人｜绝对起止｜原句逐字）+ 表达情绪 + 声音。
- 四速分离：人物事件速度 / 摄影机速度 / 播放速度 / 剪辑密度各写何处变、何时停、为何触发恢复；不写 `快慢结合`。

## 5. 起中终三画框比较 + 反向验收

- 未锁定时先比较同剧情同台词同空间下的起始/关键变化/终点画框（框内多大、谁主导、何时显露），再定观察距离与路径；全程同尺中景只换前后跟随不算观看提升。
- 成文反查：去掉形容词后仍能还原光形色块反射；只剩 `手持/特写/快慢结合/电影级` 标签即打回重修对应编译。
- 轴线：`framing-and-axis.md §4-5`，180° 建立/换侧机制，判侧公式 `(Bx-Ax)*(Cy-Ay)-(By-Ay)*(Cx-Ax)`。

## 6. FCML 运镜库用法（按需索引，不背全库）

- `assets/fcml-motion-library.json`（117 条）+ `shot-design-engine.md §4`：先用观看位置缩小机制范围，选中后存 `motion{fcml_ids, operations, stages}`，编译不重查库。
- 七类：translation / orientation / focal / focus / time / composition / post，每类有 definition + diagnostic（如横移混摇摄、升降混俯仰），诊断纠偏用。
