---
name: aesthetic-fashion-design
description: Use when designing garments, costumes, hosiery, accessories or any fashion item. Covers silhouette, proportion, color system, material contrast, pattern density, construction annotations and A-F zoning before any drawing begins.
---

# Aesthetic Fashion Design（画前方向锁定+通用检查器）

> 归属：身份/配色三层/选型归 `character-design`；服装个性层方案归 `costume-design`；代码落盘+门禁归 `garment-flat`。本文件只做**动笔前的通用检查**：品类几何对号、纹样四层、工艺标注、zoning、反模式。配色只定比例 HEX，不重定三色理论。

## 0. Never draw before locking direction
Establish first: wearer/scene, silhouette word (e.g. 缠绕/建筑感/流动), base vs motif vs accent colors with hex, material hierarchy (which is matte / glossy / metallic, brightest last), pattern density rule (dense where, fade where, never full-cover without reason), construction (seams, bands, rings, closures).

## 1. Fashion checklist（配色理论引用 character-design，此处只做画前登记）
1. 廓形: one sentence silhouette + front/side/back consistency;廓形必须符合品类版型库（§5），不许用梯形+圆圈糊弄
2. 色彩: base 60% / motif 30% / accent 10% 登记 HEX（理论见 `character-design` 配色三层，不复述），no muddy blends
3. 材质对比: 按品类写三套各自高光逻辑（如 缎面锐光 / 雪纺雾感 / 金属镜面），never one gradient for all
4. 纹样节奏: 见§6 四层分级，大小渐变+疏密渐变+留白≥40%，禁同尺寸图章满铺
5. 工艺: band widths in mm, seam type, closures, stitch notes（针脚虚线画出来）
6. 体量: 按品类写锥度/长短/宽窄数；画 garment flat（服装平铺图），禁火柴人偶/无脸模特

## 2. Reference first
Before V2 of any design: search real products of THE SAME category and note its construction codes.
- hosiery/snake: snake hosiery, BV/PH5/Burberry snake knits, Mariemur/Uye Surana bands, mimi snake skin scans（backseam contrast, band-as-anchor, scale size transition, belly-panel sheerness）
- lolita OP: Baby, the Stars Shine Bright / Angelic Pretty / Axes Femme OP（X-line bell skirt, shirring, pintucks, lace hem, headdress+wig set, ruffled socks, Mary Jane shoes）

## 3. Zoning
Split into named zones (A garter/head, B main motif, C fade, D sheer panel, E tail/toe, F seam). Each zone: color hex, material, density, layer order (motif always above base, metal topmost). Changes stay inside one zone.

## 4. Anti-patterns
- Green tape around white pole (no head/tail turn, no dorsal/ventral split)
- Full-cover scales with no breathing space
- One flat fill for silk + scales + metal
- Annotations drawn into the artwork (keep spec text out of the art layer)
- 梯形+圆圈冒充裙子（无褶、无边、无厚度）
- 同尺寸碎花图章满铺（无主次、无枝线连接）
- 无脸人偶 + 整圈粗描边（sticker 感，地摊货来源）

## 5. Category silhouette library（画前先对号入座，几何必须长成该品类的样子）
- **lolita OP**: X-line 钟形裙摆（腰收、摆开，裙长膝盖上下）；灯笼/泡泡袖 + 袖口抽褶松紧；立领或圆领 + 盘扣/蝴蝶结；腰封或腰带收腰；下摆蕾丝花边（扇贝边 ≥2 层）；必须配头饰（发箍/边帽+假发感弧度）；裙撑感（裙摆有厚度线，禁单层梯形）；不对称燕尾=左右摆长差 ≥30cm 且摆角形状不同
- **hosiery**: 锚定带 + 跟随腿部锥度（大腿→脚踝 28→18mm 级收分），禁直筒
- （新品类在此追加：先写 3 条以上几何铁律再画）

## 6. Motif layering（纹样四层，缺一层就平）
1. 主花/主纹（大，胸前/裙摆视觉中心，带瓣片前后遮挡，最多 3-5 朵）
2. 副花/花苞（中，环绕主花，半遮挡表前后关系）
3. 枝叶线（细线条连接主副花，有起笔收笔，不许悬空散点）
4. 底纹/雪点/暗纹（淡色小，填充呼吸感，留白≥40%）
- 蕾丝边：扇贝/网眼单独起一层，不许拿碎花代替蕾丝
- 绣线：花瓣边缘金线勾边 + 针脚虚线（stroke-dasharray），这是"贵感"来源

## 7. Craft floor（精美底线，少一条就是地摊货）
- garment flat 平铺画法：前片/侧片/背片 + 细节局部，禁人偶头/无脸模特（画不好的人体不如不画）
- 细线：装饰线 0.5-1px，轮廓线才用 2-3px；全图 ≥3px 粗线 = sticker 感
- 荷叶边/褶皱：≥3 层前后遮挡波浪 path，单层梯形摆 = 布片不是裙子
- 褶皱阴影：省布但显贵——裙摆 ≥5 组放射褶线 + 底边阴影带
- 渐变节制：缎面只用两端柔和渐变，禁霓虹高饱和整圈描边

## 8. Garment layering（服装层次：每件单品必须有前后遮挡，禁一片式）
- 裙摆三层：面摆（短，半透明边）+ 里摆（长 8-12cm，下沿露出）+ 裙撑厚度线；层与层之间 3-8px 阴影带（20-30% 黑）
- 腰封压住衣身下摆与裙摆上沿，衔接处阴影带；泡袖根压住衣身肩部，衔接处阴影带
- 蝴蝶结 = 双环 + 结 + 双尾 + 褶皱线，环与结之间阴影；缎带加纵向折光带（高光/阴影成对）
- 判定：整图找不见 3 处以上"上压下+阴影带"，就是一片式，打回
