"""garment-flat 共享运行时（skill 之“手”）。
设计知识禁止写在这里——设计进 SKILL.md＋references，数据进各款 params.json，
本文件只放无服装语义的通用 SVG 原语：文本登记/防叠检查/线型/蕾丝/肌理。
两处 generate.py 是本文件的 dumb executor，不得各自另起一套同名机制。
"""
from __future__ import annotations

import math

TEXTS: list[dict] = []  # {x0,y0,x1,y1,tag}，文本与引线编号的占用盒
_TEXT_PAD = 4.0  # 判定间隙 px，小于此视为挤压


def est_w(s: str, size: float) -> float:
    """保守估计文本宽度：CJK/全角按 1.0×字号，ASCII 按 0.55×字号，再放 5% 余量。"""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o > 127 or ch in "，。！？；：、（）【】·×→":
            w += 1.0 * size
        elif ch == " ":
            w += 0.35 * size
        else:
            w += 0.55 * size
    return w * 1.05


def _reg(x: float, y: float, s: str, size: float, anchor: str, tag: str) -> None:
    w = est_w(s, size)
    if anchor == "middle":
        x0, x1 = x - w / 2, x + w / 2
    elif anchor == "end":
        x0, x1 = x - w, x
    else:
        x0, x1 = x, x + w
    TEXTS.append({"x0": x0, "y0": y - size * 0.9, "x1": x1, "y1": y + size * 0.3, "tag": tag})


def _reg_box(x0: float, y0: float, x1: float, y1: float, tag: str) -> None:
    TEXTS.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "tag": tag})


def check_texts(w: float, h: float) -> list[str]:
    """pairwise 文本 bbox 碰撞＋出界检查。返回违例描述（空＝通过）。"""
    bad: list[str] = []
    n = len(TEXTS)
    for i in range(n):
        a = TEXTS[i]
        if a["x0"] < -0.5 or a["y0"] < -0.5 or a["x1"] > w + 0.5 or a["y1"] > h + 0.5:
            bad.append(f'出界 {a["tag"]}: [{a["x0"]:.0f},{a["y0"]:.0f},{a["x1"]:.0f},{a["y1"]:.0f}]')
        for j in range(i + 1, n):
            b = TEXTS[j]
            if (a["x0"] - _TEXT_PAD < b["x1"] and b["x0"] - _TEXT_PAD < a["x1"]
                    and a["y0"] - _TEXT_PAD < b["y1"] and b["y0"] - _TEXT_PAD < a["y1"]):
                bad.append(f'叠压 {a["tag"]} <-> {b["tag"]}')
    return bad


def S(outline_w=2.2, color="#111"):
    return (f'stroke="{color}" stroke-width="{outline_w}" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"')


def T(x, y, s, size=17, anchor="start", fill="#111", weight=None, tag=None, halo=True):
    _reg(x, y, s, size, anchor, tag or s[:14])
    w = f' font-weight="{weight}"' if weight else ""
    hw = (f' paint-order="stroke" stroke="#fff" '
          f'stroke-width="{max(2.0, size * 0.28):.1f}" stroke-linejoin="round"') if halo else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{fill}"{w}{hw} font-family="sans-serif">{s}</text>')


def leader(x1, y1, x2, y2, n: str, color="#B91C1C"):
    _reg_box(x2 - 14, y2 - 14, x2 + 14, y2 + 14, f"引线{n}")
    return (
        f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="1.3" fill="none"/>'
        f'<circle cx="{x1}" cy="{y1}" r="4" fill="{color}"/>'
        f'<g><circle cx="{x2}" cy="{y2}" r="13" fill="{color}"/>'
        f'<text x="{x2}" y="{y2+6}" font-size="15" text-anchor="middle" fill="#fff" '
        f'font-family="sans-serif">{n}</text></g>'
    )


def stitch(d: str, w=1.2, dash="7 5", color="#555"):
    return f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none" stroke-dasharray="{dash}"/>'


def scallop(x0, y0, x1, y1, n: int) -> str:
    """两点间半圆蕾丝牙边（n 个牙）。"""
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    r = math.hypot(dx, dy) / 2
    d = f"M{x0} {y0}"
    for i in range(n):
        d += f" A{r:.1f} {r:.1f} 0 0 1 {x0 + dx * (i + 1):.1f} {y0 + dy * (i + 1):.1f}"
    return d


def scallop_poly(pts: list[tuple], per: float = 14.0) -> str:
    """折线蕾丝牙边：每段按长度自动分牙。"""
    d = f"M{pts[0][0]} {pts[0][1]}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dist = math.hypot(x1 - x0, y1 - y0)
        n = max(1, round(dist / per))
        dx, dy = (x1 - x0) / n, (y1 - y0) / n
        r = math.hypot(dx, dy) / 2
        for i in range(n):
            d += f" A{r:.1f} {r:.1f} 0 0 1 {x0 + dx * (i + 1):.1f} {y0 + dy * (i + 1):.1f}"
    return d


def twill_g(cx: float, clip_id: str, top: int = 285, bot: int = 765, half: int = 230) -> str:
    """面料斜纹肌理：细斜线组，裁剪于衣身内，透明度极低只给布面呼吸感。"""
    lines = []
    x = cx - half
    while x <= cx + half:
        lines.append(f'<line x1="{x}" y1="{top}" x2="{x - 55}" y2="{bot}" '
                     f'stroke="#000" stroke-width="1" opacity="0.05"/>')
        x += 9
    return f'<g clip-path="url(#{clip_id})">{"".join(lines)}</g>'


def ribbon(tx: float, bx: float, d: int, dark=True) -> str:
    """褶侧影（d＝褶倒向）：谷线倒向侧深影，脊线对侧淡光，随外扩加宽。"""
    if dark:
        return (f'<polygon points="{tx + d},290 {tx + d * 8},290 {bx + d * 14},756 '
                f'{bx + d * 5},756" fill="#1A1A22" opacity="0.08"/>')
    return (f'<polygon points="{tx - d * 6},292 {tx - d * 2},292 {bx - d * 3},754 '
            f'{bx - d * 7},754" fill="#D8DAE2" opacity="0.9"/>')


def lace_dots(pts: list[tuple], step: float = 26.0, r: float = 1.3) -> str:
    """蕾丝网眼点：沿折线每 step 放一网眼点（纯图形，不登记文本）。"""
    dots, acc = [], 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        t = step - acc
        while t < seg:
            px, py = x0 + (x1 - x0) * t / seg, y0 + (y1 - y0) * t / seg
            dots.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="#444"/>')
            t += step
        acc = (acc + seg) % step
    return "".join(dots)


def lace_dots_line(x0, y0, x1, y1, step=15.0, r=1.2) -> str:
    """直线段网眼点。"""
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
    return "".join(
        f'<circle cx="{x0 + (x1 - x0) * i / n:.1f}" cy="{y0 + (y1 - y0) * i / n:.1f}" '
        f'r="{r}" fill="#444"/>'
        for i in range(n + 1))
