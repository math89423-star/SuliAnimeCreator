---
name: svg-illustration-craft
description: Use when drawing any SVG illustration, technical fashion flat, zone map or control image. Covers layer hierarchy, path discipline, render-check loop with resvg, text discipline and seg-map export.
---

# SVG Illustration Craft（通用SVG插画 canonical）

> 归属：通用SVG图层/渲染回看/文字纪律/seg导出以本文件为准；服饰flat代码落盘归 `garment-flat`（params→generate.py），时尚画前检查归 `aesthetic-fashion-design`。画服饰flat时先过那两家，本文件只做通用SVG执行。

## 1. File discipline
- Groups: `art > base / motif / accents / shading / annotations`. Art and annotations are separate top-level groups; seg export hides annotations.
- No giant merged path for a character/garment. Separate group per zone (A/B/C…).
- Gradients per material (silk soft, scale glossy layered, metal sharp). Vary stroke width: outer silhouette 3, inner folds 1.5-2, micro 1.
- Symbols/patterns (`<pattern>`) for repeating scales; density via opacity mask, not hand-placed hundreds.

## 2. Draw order
1. Block-in masses only (no lashes/strands/text). Thumbnail must read.
2. Construction (anatomy/volume, taper, joints).
3. Design masses + secondary folds/seams/rings.
4. Face/material split (skin matte, fabric soft, metal sharp, glass translucent).
5. Light: single key/fill/rim logic, rim in segments not full neon outline.
6. Depth: haze, dim far detail, ground reflection, foreground bokeh.
7. Micro only on focal zones.

## 3. Render-check loop (mandatory, resvg available here)
Render: `node -e "{Resvg}=require('@resvg/resvg-js');svg=fs.readFileSync(IN);fs.writeFileSync(OUT,new Resvg(svg,{fitTo:{mode:'width',value:630}}).render().asPng())"` in `C:/Users/ADMINI~1/AppData/Local/Temp/opencode` (module preinstalled). Read PNG back with Read tool. Critique top-3: anatomy, silhouette symmetry, tangencies, text overlap, neon-everything. Fix only those regions, re-render, keep iff better.

## 4. Text discipline
- Spec/notes live in `annotations` group, 15px+, 20px line spacing, never overlapping art.
- Seg/control export (`*_seg.svg`): white bg, flat zone fills only (gray/green/pale/gold), NO text, NO arrows, NO swatches, NO dashed seams. Cloud image models copy pixels literally — any annotation in the pad image will be reproduced in output.
- Cairo/resvg bugs: no `<tspan>` multicolor per line, no emoji, no unicode arrows in text; use separate `<text>` + SVG markers.

## 5. Quality bar
Face/hands/hair/clothing focal get max density; far field simplified. If it still reads as icon doodle: add structural layering + line-weight variance + material separation, not random tiny shapes.
