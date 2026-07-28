#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图一 · 要件-证据对照矩阵 / "逻辑序列主义表" (layout: elements_matrix).

三源合流：吴香香三层四步 + 实务逻辑序列主义表 + 02 两层五站。
纵向 = 请求→成立抗辩→消灭抗辩→行使抗辩→反抗辩→再抗辩（只①是要件，②③④…是抗辩）；
横向 = 原被告就每个检视项的攻防（规范类型/责任方/证明标准/前景/争议）。

审计轨迹：每行带前景(功能■)、置信度、【待核验】；决定性要件红标=三条件命中。
红只 #991B1B（决定性行实心块白字）；功能色仅绿(高)/橙(中)，无功能红。

Usage: python render_elements_matrix.py <semantic-map.json> <out.svg>
"""
import sys
from common import C, FS, RADIUS, TITLE_FONT, esc, wrap, svg_open, load_map

FS_TITLE = FS["doc_title"]
FS_SUB, FS_HEAD, FS_CELL, FS_TAG = FS["subtitle"], 13, FS["cell"], 11

WIDTH = 1240
LEFT = RIGHT = 60
STEP_ORDER = ["①成立积极要件", "②未发生抗辩", "③已消灭抗辩",
              "④行使抗辩(抗辩权)", "反抗辩", "再抗辩"]

# column key, header, width, align
COLS = [
    ("检视项", "检视项", 372, "start"),
    ("规范类型", "规范", 96, "middle"),
    ("责任方", "责任方", 92, "middle"),
    ("证明标准", "证明标准", 176, "middle"),
    ("前景", "证明前景", 108, "middle"),
    ("争议状态", "争议", 92, "middle"),
    ("_annot", "修正因素 / 核验", 204, "start"),
]
FUNC = {"高": C["func_high"], "中": C["func_mid"]}
STANCE_TXT = {"原告": C["navy"], "被告": C["green"]}

HEAD_Y = 118
ROW_H = 46
GRP_H = 34


def _col_x():
    xs, x = [], LEFT
    for _, _, w, _ in COLS:
        xs.append(x)
        x += w
    return xs


def render(m):
    rows = m["rows"]
    stance = m.get("stance", "")
    closing = m.get("收官层", "")
    xs = _col_x()
    plot_w = sum(c[2] for c in COLS)

    # group rows by 步 (STEP_ORDER); decisive first within a group
    groups = []
    for step in STEP_ORDER:
        g = [r for r in rows if r.get("步") == step]
        if g:
            g.sort(key=lambda r: (not r.get("决定性"),))
            groups.append((step, g))

    # height: header + sum(group header + rows)
    y = HEAD_Y + 30
    for _, g in groups:
        y += GRP_H + len(g) * ROW_H
    height = y + 96   # legend + footer

    S = [svg_open(WIDTH, height)]

    # ---- title + subtitle ----
    S.append(f'<text data-role="title" x="{WIDTH/2}" y="46" font-size="{FS_TITLE}" font-weight="700" '
             f'font-family="{TITLE_FONT}" fill="{C["ink"]}" text-anchor="middle">{esc(m["title_text"])}</text>')
    sub = "  ·  ".join([x for x in [stance, (f"收官于{closing}" if closing else ""),
                                     "要件-证据对照（逻辑序列主义表）"] if x])
    S.append(f'<text x="{WIDTH/2}" y="80" font-size="{FS_SUB}" fill="{C["ink2"]}" text-anchor="middle">{esc(sub)}</text>')

    # ---- header row ----
    S.append('<g data-role="header">')
    S.append(f'<rect x="{LEFT}" y="{HEAD_Y}" width="{plot_w}" height="30" rx="6" ry="6" fill="{C["cream"]}"/>')
    for (key, head, w, align), x in zip(COLS, xs):
        tx = x + (10 if align == "start" else w/2)
        S.append(f'<text x="{tx:.1f}" y="{HEAD_Y+20}" font-size="{FS_HEAD}" font-weight="700" '
                 f'fill="{C["ink"]}" text-anchor="{align}">{esc(head)}</text>')
    S.append('</g>')

    # ---- groups + rows ----
    y = HEAD_Y + 30
    for step, g in groups:
        # group header (navy text, hairline — no color block堆砌)
        S.append(f'<g data-role="group" data-step="{esc(step)}">')
        S.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{LEFT+plot_w}" y2="{y:.1f}" stroke="{C["navy"]}" stroke-width="1.4"/>')
        badge = "要件 · 原告本证" if step.startswith("①") else "抗辩 · 被告举证"
        S.append(f'<text x="{LEFT+6}" y="{y+23:.1f}" font-size="{FS_HEAD}" font-weight="700" fill="{C["navy"]}">{esc(step)}</text>')
        S.append(f'<text x="{LEFT+plot_w-6}" y="{y+23:.1f}" font-size="{FS_TAG}" fill="{C["ink2"]}" text-anchor="end">{esc(badge)}</text>')
        S.append('</g>')
        y += GRP_H

        for r in g:
            decisive = bool(r.get("决定性"))
            row_y = y
            S.append(f'<g data-role="row" data-id="{esc(str(r.get("id","")))}"'
                     + (' data-decisive="1"' if decisive else '') + '>')
            if decisive:  # #991B1B solid block, white text — the single emphasis
                S.append(f'<rect x="{LEFT}" y="{row_y+3:.1f}" width="{plot_w}" height="{ROW_H-6}" '
                         f'rx="{RADIUS["card"]}" ry="{RADIUS["card"]}" fill="{C["red"]}"/>')
            else:
                S.append(f'<line x1="{LEFT}" y1="{row_y+ROW_H:.1f}" x2="{LEFT+plot_w}" y2="{row_y+ROW_H:.1f}" '
                         f'stroke="{C["grid"]}" stroke-width="1"/>')
            base = C["white"] if decisive else C["ink"]
            cy = row_y + ROW_H/2 + FS_CELL*0.34

            # 检视项 (may wrap to 2 lines)
            x0 = xs[0]
            lines = wrap(str(r.get("检视项", "")), FS_CELL, COLS[0][2] - 20)[:2]
            y0 = row_y + ROW_H/2 - (len(lines)-1)*(FS_CELL+3)/2 + FS_CELL*0.34
            for j, ln in enumerate(lines):
                tag = "" 
                if j == 0 and r.get("id"):
                    tag = f'{r["id"]}｜'
                S.append(f'<text x="{x0+10:.1f}" y="{y0+j*(FS_CELL+3):.1f}" font-size="{FS_CELL}" '
                         f'font-weight="{"700" if decisive else "400"}" fill="{base}">{esc(tag+ln)}</text>')

            # 规范类型
            S.append(f'<text x="{xs[1]+COLS[1][2]/2:.1f}" y="{cy:.1f}" font-size="{FS_CELL}" '
                     f'fill="{base}" text-anchor="middle">{esc(str(r.get("规范类型","")))}</text>')

            # 责任方 (stance-colored on white rows; white on red rows)
            duty = str(r.get("责任方", ""))
            dcol = base if decisive else STANCE_TXT.get(duty, C["ink"])
            S.append(f'<text x="{xs[2]+COLS[2][2]/2:.1f}" y="{cy:.1f}" font-size="{FS_CELL}" '
                     f'font-weight="600" fill="{dcol}" text-anchor="middle">{esc(duty)}</text>')

            # 证明标准
            std = str(r.get("证明标准", ""))
            stdlines = wrap(std, FS_TAG, COLS[3][2]-14)[:2]
            sy = row_y + ROW_H/2 - (len(stdlines)-1)*(FS_TAG+2)/2 + FS_TAG*0.34
            for j, ln in enumerate(stdlines):
                S.append(f'<text x="{xs[3]+COLS[3][2]/2:.1f}" y="{sy+j*(FS_TAG+2):.1f}" font-size="{FS_TAG}" '
                         f'fill="{base}" text-anchor="middle">{esc(ln)}</text>')

            # 前景: functional ■ (高绿/中橙); 低/待第二层 -> text only
            pj = str(r.get("前景", ""))
            px = xs[4] + COLS[4][2]/2
            if pj in FUNC and not decisive:
                S.append(f'<rect x="{px-30:.1f}" y="{row_y+ROW_H/2-6:.1f}" width="12" height="12" rx="2" fill="{FUNC[pj]}"/>')
                S.append(f'<text x="{px-12:.1f}" y="{cy:.1f}" font-size="{FS_CELL}" fill="{base}" text-anchor="start">{esc(pj)}</text>')
            else:
                shown = pj if pj else "—"
                S.append(f'<text x="{px:.1f}" y="{cy:.1f}" font-size="{FS_CELL}" fill="{base}" text-anchor="middle">{esc(shown)}</text>')

            # 争议
            S.append(f'<text x="{xs[5]+COLS[5][2]/2:.1f}" y="{cy:.1f}" font-size="{FS_CELL}" '
                     f'fill="{base}" text-anchor="middle">{esc(str(r.get("争议状态","")))}</text>')

            # 修正因素 / 核验 / 命中三条件
            annot = list(r.get("修正因素", []) or [])
            if r.get("核验") and "核验" not in "".join(annot):
                annot.append(str(r.get("核验")))
            if decisive and r.get("命中"):
                annot.append("命中：" + "×".join(r["命中"]))
            atxt = " · ".join(annot)
            acol = C["white"] if decisive else C["ink2"]
            alines = wrap(atxt, FS_TAG, COLS[6][2]-8)[:2]
            ay = row_y + ROW_H/2 - (len(alines)-1)*(FS_TAG+2)/2 + FS_TAG*0.34
            for j, ln in enumerate(alines):
                S.append(f'<text x="{xs[6]+6:.1f}" y="{ay+j*(FS_TAG+2):.1f}" font-size="{FS_TAG}" '
                         f'fill="{acol}" text-anchor="start">{esc(ln)}</text>')
            S.append('</g>')
            y += ROW_H

    # ---- legend ----
    ly = y + 34
    S.append('<g data-role="legend">')
    items = [(C["func_high"], "前景高"), (C["func_mid"], "前景中"), (C["red"], "决定性要件（三条件命中）")]
    lx = LEFT
    for col, lab in items:
        S.append(f'<rect x="{lx}" y="{ly-11}" width="13" height="13" rx="2" fill="{col}"/>')
        S.append(f'<text x="{lx+19}" y="{ly}" font-size="{FS_TAG}" fill="{C["ink2"]}">{esc(lab)}</text>')
        lx += 40 + (len(lab)*13)
    S.append(f'<text x="{LEFT}" y="{ly+24}" font-size="{FS_TAG}" fill="{C["ink2"]}">'
             f'【待核验】=条号/要件尚未确认；前景"低/待第二层"由决定性红标承担，不另上功能红。</text>')
    S.append('</g></svg>')
    return "\n".join(S), WIDTH, height


def main(mapfile, out):
    svg, w, h = render(load_map(mapfile))
    open(out, "w", encoding="utf-8").write(svg)
    print(f"[elements_matrix] wrote {out}  {w}x{h}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out.svg")
