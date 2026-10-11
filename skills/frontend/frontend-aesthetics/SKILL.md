---
name: frontend-aesthetics
description: 前端美学与工程设计总纲。Element Plus 四原则 + Vue 生产/性能实践在本仓的落地：主题 tokens、三栏、三态、路由懒加载、props 稳定、列表虚拟化。触发词：前端、页面、主题、样式、路由、分页、空状态、性能、Element。
sources:
  - https://element-plus.org/en-US/guide/design.html
  - https://vuejs.org/guide/best-practices/production-deployment
  - https://vuejs.org/guide/best-practices/performance
  - https://www.nngroup.com/articles/ten-usability-heuristics/
  - https://www.nngroup.com/articles/user-control-and-freedom/
---

# Frontend Aesthetics（前端美学设计）

> 联网依据：设计纪律取 [Element Plus Design](https://element-plus.org/en-US/guide/design.html)（Consistency/Feedback/Efficiency/Controllability）；生产构建取 [Vue Production Deployment](https://vuejs.org/guide/best-practices/production-deployment)；性能取 [Vue Performance](https://vuejs.org/guide/best-practices/performance)。本仓落地（`src/styles/theme.css`、三栏折叠、skeleton/empty 三态）为附加实现。

## 1. 设计四原则（Element Plus 原文映射）

- Consistency：贴合现实流程与用户习惯；界面内风格/图标/文字/位置全一致。([来源](https://element-plus.org/en-US/guide/design.html))
- Feedback：操作有样式与动效反馈；状态变化反映到页面元素。([来源](https://element-plus.org/en-US/guide/design.html))→ 本仓：按钮 loading、菜单激活态、卡片 hover 浮起、toast。
- Efficiency：流程简单直观；意图明确帮用户快决策；界面直白免记忆。([来源](https://element-plus.org/en-US/guide/design.html))→ 本仓：一句话 idea→发散→确认；18槽位同卡（图+提示词+生成/保存/传图）。
- Controllability：可给建议不替用户决策；后果可控（可取消/中止/终止）。([来源](https://element-plus.org/en-US/guide/design.html))→ 本仓：suggest 永不直写库、版本回滚冻结、删除二次确认。

## 2. 本仓主题落地

- tokens：`--suli-bg/surface/border/text/primary/accent/radius/shadow/font` 全在 `theme.css`；主色靛紫、圆角 14、柔阴影；窄屏 820px 三栏堆叠。
- 三态：空 `el-empty`、加载 `skeleton`、报错 toast + 文案，不裸奔；表格（版本/服装/分镜/工具）一律分页。
- 导航：`vue-router` 真地址（`/story /character /board /director /art`）+ 顶栏面包屑 + Episode 输入；左栏 `router` 模式。

## 3. 生产与性能（Vue 原文映射）

- 生产构建去开发分支、预编译模板省 14kb、配 `NODE_ENV=production`；错误用 `app.config.errorHandler` 上报（Sentry/Bugsnag）。([来源](https://vuejs.org/guide/best-practices/production-deployment))
- 包体积：tree-shaking（不用 Transition 就不进包）、ESM 优先（如 `lodash-es`）、`bundlejs.com` 估重。([来源](https://vuejs.org/guide/best-practices/performance))
- 路由懒加载：`defineAsyncComponent(() => import('./Foo.vue'))`，路由组件强烈建议懒加载。([来源](https://vuejs.org/guide/best-practices/performance))→ 本仓下一步：views 改动态 import 压 1.1M 包。
- 更新：props 保持稳定（`active` 下沉而非 `activeId` 全刷）、`v-once/v-memo`、computed 返回旧引用、长列表虚拟化（`vue-virtual-scroller` 等）、大不可变结构用 `shallowRef`、少造无意义中间组件。([来源](https://vuejs.org/guide/best-practices/performance))

## 4. Nielsen Norman 十启发式在本仓的映射（2026-10-11 补）

> 原文：[10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)；H3 深文：[User Control and Freedom](https://www.nngroup.com/articles/user-control-and-freedom/)（Back/Cancel/Close/Undo，还必须可发现）。

- H1 状态可见：顶栏管线 steps（故事→角色→分镜→导演）+ Episode + 镜数 + 后端tag，操作即时 toast/skeleton/engine 回执。
- H2 贴合现实：用创作语言（发散/确认/拆镜/组装）不用技术黑话；顺序=真实创作顺序。
- H3 控制与自由：浏览器 Back 天然可用（真路由）；回滚用 popconfirm 二次确认；破坏性操作可撤销（版本回滚/冻结）；退出清晰可发现。([来源](https://www.nngroup.com/articles/user-control-and-freedom/))
- H4 一致：tokens/卡片/表格/分页同一套；外部遵 Element/Router 惯例（Jakob 定律：用户时间多花在别家产品）。
- H5 防错：空剧本禁拆镜、空指令禁迭代、0镜禁组装、LLM 默认关；先禁错再报错。
- H6 识别优于回忆：顶栏常驻 Episode/镜数/后端态；面包屑+管线标当前位置；当前角色跨页签可见。
- H7 灵活高效：新手一步一钮，专家走整集组装/批量；分页 sizes 可调。
- H8 极简：高级项收小（LLM 复选小字）；帮助只放 Agent 面板与 docs，工作区 chrome 不加解释段（与本项目零解释规则一致）。
- H9 错误恢复：报错说清+给恢复命令（后端未起→`python run.py` + `npm run dev`），失败注明回退（LLM 失败→规则拆+engine 标注）。
- H10 帮助文档：docs/FILE_LAYOUT.md + skills/README.md 为真源，UI 内只在 Agent 面板给入口。
