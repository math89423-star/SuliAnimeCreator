# Doublecheck spec

## Goal
删除导演页顶部的切换清理刷新一排按钮。

## Scope
范围内：DirectorView.vue顶部栏与switchEpisode/handleClear等死代码；范围外：其他页面与后端不动。

## Acceptance criteria
导演页顶不再有集号输入/切换/清理/刷新按钮，只留标题与集号；集号切换走全局顶栏，清空走各页签内按钮，刷新逻辑函数保留；构建通过。

## Failure modes
误删标题集号tag则回退；内部refresh/load函数保留仅删顶栏入口。

## Priorities
只删顶栏入口与其专属死代码。

## Non-goals
不动各页签内清空/生成/导出逻辑、不动后端。
