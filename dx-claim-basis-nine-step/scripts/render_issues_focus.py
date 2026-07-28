#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图二 · 争议焦点汇聚 (layout: issues_focus).

坐邹碧华九步法第⑥步"争点整理"。每个争议焦点是三条流的交汇：
决定性要件(02) × 对手主攻线(03·危险度) × 法官视角(03·类案)。

【设计 · 逐焦点汇聚单元】旧版把三源全堆左、多焦点全堆右、彼此多对多连线，
线密如麻、谁连谁看不清。现改为：**一个焦点 = 一个自足单元**——该焦点的
三条来源小卡在左，短箭头就近汇入右侧焦点卡；单元之间无任何跨线。
核心焦点=红卡（唯一强调）；来源按流着色（要件/对手/法官），底部图例。

Usage: python render_issues_focus.py <semantic-map.json> <out.svg>
"""
import sys, math
from common import C, FS, RADIUS, TITLE_FONT, esc, wrap, svg_open, load_map, arrow_marker


def _rounded(pts, r=6):
    """正交折线 + 拐角近直角小圆角（stroke-linejoin 之外再打小圆弧，效果更稳）。"""
    clean = []
    for p in pts:
        if not clean or abs(p[0]-clean[-1][0]) > 0.5 or abs(p[1]-clean[-1][1]) > 0.5:
            clean.append(p)
    pts = clean
    if len(pts) < 2:
        return ""
    d = [f'M {pts[0][0]:.1f},{pts[0][1]:.1f}']
    for i in range(1, len(pts)-1):
        p0, p1, p2 = pts[i-1], pts[i], pts[i+1]
        v1 = (p1[0]-p0[0], p1[1]-p0[1]); l1 = math.hypot(*v1) or 1
        v2 = (p2[0]-p1[0], p2[1]-p1[1]); l2 = math.hypot(*v2) or 1
        rr = min(r, l1/2, l2/2)
        a = (p1[0]-v1[0]/l1*rr, p1[1]-v1[1]/l1*rr)
        b = (p1[0]+v2[0]/l2*rr, p1[1]+v2[1]/l2*rr)
        d.append(f'L {a[0]:.1f},{a[1]:.1f} Q {p1[0]:.1f},{p1[1]:.1f} {b[0]:.1f},{b[1]:.1f}')
    d.append(f'L {pts[-1][0]:.1f},{pts[-1][1]:.1f}')
    return " ".join(d)

FS_TITLE = FS["doc_title"]
FS_SUB, FS_FOC, FS_CHIP, FS_TAG = FS["subtitle"], 15, 12, 11

WIDTH = 1240
LEFT = RIGHT = 60
FEED_W = 392
FOC_W = 388
TOP = 108
CHIP_H = 40
CHIP_GAP = 12
UNIT_GAP = 30
GAP = 12          # arrow tip clearance before the focus card
PADY = 22

SRC_ORDER = ["决定性要件", "对手主攻线", "法官视角"]
SRC_ABBR = {"决定性要件": "要件", "对手主攻线": "对手", "法官视角": "法官"}
SRC_COL = {"决定性要件": C["navy"], "对手主攻线": C["ink2"], "法官视角": C["green"]}
CLS_TXT = {"实体": C["navy"], "程序": C["ink2"], "事实": C["green"]}


def _foc_lines(f):
    return wrap(f["label"], FS_FOC, FOC_W - 28)


def _unit_h(f):
    nf = max(1, len(f.get("feeders", [])))
    feed_h = nf * CHIP_H + (nf - 1) * CHIP_GAP
    foc_h = len(_foc_lines(f)) * (FS_FOC + 6) + 2 * PADY
    return max(feed_h, foc_h)


def render(m):
    foci = m["foci"]
    stance = m.get("stance", "")

    feed_x = LEFT
    foc_x = WIDTH - RIGHT - FOC_W

    units_h = [_unit_h(f) for f in foci]
    total = sum(units_h) + UNIT_GAP * (len(foci) - 1)
    height = TOP + total + 96

    S = [svg_open(WIDTH, height)]
    S.append('<defs>' + arrow_marker("arrGray", C["line"], size=10) + '</defs>')

    S.append(f'<text data-role="title" x="{WIDTH/2}" y="46" font-size="{FS_TITLE}" font-weight="700" '
             f'font-family="{TITLE_FONT}" fill="{C["ink"]}" text-anchor="middle">{esc(m["title_text"])}</text>')
    sub = "  ·  ".join([x for x in [stance, "争议焦点汇聚（争点整理）· 每个焦点由三条来源交汇而成"] if x])
    S.append(f'<text x="{WIDTH/2}" y="80" font-size="{FS_SUB}" fill="{C["ink2"]}" text-anchor="middle">{esc(sub)}</text>')

    y = TOP
    for f, uh in zip(foci, units_h):
        core = bool(f.get("core"))
        feeders = f.get("feeders", [])
        nf = max(1, len(feeders))
        feed_h = nf * CHIP_H + (nf - 1) * CHIP_GAP
        foc_lines = _foc_lines(f)
        foc_h = len(foc_lines) * (FS_FOC + 6) + 2 * PADY

        feed_top = y + (uh - feed_h) / 2
        foc_top = y + (uh - foc_h) / 2
        foc_cy = foc_top + foc_h / 2

        S.append(f'<g data-role="focus-unit" data-id="{esc(str(f.get("id","")))}"' + (' data-core="1"' if core else '') + '>')

        # ---- connectors: comb-convergence — aligned turn at the horizontal
        #      MIDPOINT bus, unified single entry into the focus card, rounded corners ----
        busx = (feed_x + FEED_W + foc_x) / 2
        entry_x = foc_x - GAP
        for i, fd in enumerate(feeders):
            cy = feed_top + i * (CHIP_H + CHIP_GAP) + CHIP_H / 2
            x0 = feed_x + FEED_W
            pts = [(x0, cy), (busx, cy), (busx, foc_cy), (entry_x, foc_cy)]
            S.append(f'<path d="{_rounded(pts, 3)}" fill="none" stroke="{C["line"]}" '
                     f'stroke-width="1.6" stroke-linejoin="round" marker-end="url(#arrGray)"/>')

        # ---- feeder chips ----
        for i, fd in enumerate(feeders):
            src = fd.get("源", "")
            item = fd.get("项", "")
            cy = feed_top + i * (CHIP_H + CHIP_GAP)
            scol = SRC_COL.get(src, C["ink2"])
            S.append(f'<g data-role="feeder" data-src="{esc(src)}">')
            S.append(f'<rect x="{feed_x}" y="{cy:.1f}" width="{FEED_W}" height="{CHIP_H}" rx="8" ry="8" '
                     f'fill="{C["cream"]}"/>')
            # source tag (colored, left) + item text
            S.append(f'<text x="{feed_x+14}" y="{cy+CHIP_H/2+FS_CHIP*0.35:.1f}" font-size="{FS_CHIP}" '
                     f'font-weight="700" fill="{scol}">〔{esc(SRC_ABBR.get(src,src))}〕</text>')
            itlines = wrap(item, FS_CHIP, FEED_W - 78)[:2]
            iy = cy + CHIP_H/2 - (len(itlines)-1)*(FS_CHIP+2)/2 + FS_CHIP*0.35
            for j, ln in enumerate(itlines):
                S.append(f'<text x="{feed_x+62}" y="{iy+j*(FS_CHIP+2):.1f}" font-size="{FS_CHIP}" '
                         f'fill="{C["ink"]}">{esc(ln)}</text>')
            S.append('</g>')

        # ---- focus card ----
        fill = C["red"] if core else C["cream"]
        tcol = C["white"] if core else C["ink"]
        S.append(f'<rect x="{foc_x}" y="{foc_top:.1f}" width="{FOC_W}" height="{foc_h:.1f}" '
                 f'rx="{RADIUS["card"]}" ry="{RADIUS["card"]}" fill="{fill}"/>')
        cls = f.get("类", "")
        if cls:
            ccol = C["white"] if core else CLS_TXT.get(cls, C["ink2"])
            S.append(f'<text x="{foc_x+FOC_W-14}" y="{foc_top+22:.1f}" font-size="{FS_TAG}" font-weight="700" '
                     f'fill="{ccol}" text-anchor="end">{esc(cls+"争点")}</text>')
        if core:
            S.append(f'<text x="{foc_x+16}" y="{foc_top+22:.1f}" font-size="{FS_TAG}" font-weight="700" '
                     f'fill="{C["white"]}">核心焦点</text>')
        y0 = foc_cy - (len(foc_lines)-1)*(FS_FOC+6)/2 + FS_FOC*0.34 + (6 if core or cls else 0)
        for j, ln in enumerate(foc_lines):
            S.append(f'<text x="{foc_x+16:.1f}" y="{y0+j*(FS_FOC+6):.1f}" font-size="{FS_FOC}" '
                     f'font-weight="700" fill="{tcol}">{esc(ln)}</text>')
        S.append('</g>')
        y += uh + UNIT_GAP

    # ---- legend: the three sources ----
    ly = height - 54
    S.append('<g data-role="legend">')
    S.append(f'<text x="{LEFT}" y="{ly-6}" font-size="{FS_TAG}" fill="{C["ink2"]}">每个焦点由以下三条来源交汇而成：</text>')
    lx = LEFT
    for src in SRC_ORDER:
        S.append(f'<rect x="{lx}" y="{ly+4}" width="13" height="13" rx="2" fill="{SRC_COL[src]}"/>')
        S.append(f'<text x="{lx+19}" y="{ly+15}" font-size="{FS_TAG}" fill="{C["ink2"]}">{esc(src)}</text>')
        lx += 150
    S.append('</g></svg>')
    return "\n".join(S), WIDTH, height


def main(mapfile, out):
    svg, w, h = render(load_map(mapfile))
    open(out, "w", encoding="utf-8").write(svg)
    print(f"[issues_focus] wrote {out}  {w}x{h}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out.svg")
