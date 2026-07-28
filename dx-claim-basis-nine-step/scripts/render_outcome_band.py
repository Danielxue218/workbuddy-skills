#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图三 · 结果预判区间带 (layout: outcome_band).

坐邹碧华第⑧步"事实认定"三出路 + 02 程序站：判决支持 / 部分支持 /
判决驳回诉请(实体) / 裁定驳回起诉(程序)。标出最可能区间与最坏情形。
"让图自己说理"——不同结果同框，读者一眼看清赢面谱系。

红只有一种 #991B1B：只标最坏情形。四段用中性美学色，不整条上交通灯。
置信度以功能 ■ 小方块附标题旁（高绿/中橙/低灰，无功能红）。

Usage: python render_outcome_band.py <semantic-map.json> <out.svg>
"""
import sys
from common import C, FS, RADIUS, TITLE_FONT, esc, text_w, wrap, svg_open, load_map

FS_TITLE = FS["doc_title"]
FS_SUB, FS_SEG, FS_TAG, FS_NOTE = FS["subtitle"], 16, 12, FS["note"]

WIDTH = 1240
LEFT = RIGHT = 60
TOP = 40
BAND_TOP = 150
BAND_H = 104
SEG_GAP = 14
BOT = 60

FUNC = {"高": C["func_high"], "中": C["func_mid"], "低": C["ink2"]}


def render(m):
    segs = m["segments"]
    most = m.get("most_likely")
    worst = m.get("worst_case")
    conf = m.get("confidence", "")
    notes = m.get("notes", [])
    stance = m.get("stance", "")
    tense = m.get("时态", "")
    why = m.get("worst_case_由来", "")

    n = len(segs)
    plot_w = WIDTH - LEFT - RIGHT
    seg_w = (plot_w - (n - 1) * SEG_GAP) / n

    notes_top = BAND_TOP + BAND_H + 56
    height = notes_top + max(0, len(notes)) * 26 + (36 if why else 0) + BOT

    S = [svg_open(WIDTH, height)]

    # ---- title + subtitle ----
    S.append(f'<text data-role="title" x="{WIDTH/2}" y="46" font-size="{FS_TITLE}" font-weight="700" '
             f'font-family="{TITLE_FONT}" fill="{C["ink"]}" text-anchor="middle">{esc(m["title_text"])}</text>')
    sub = "  ·  ".join([x for x in [stance, tense, ("结果区间预判") ] if x])
    S.append(f'<text x="{WIDTH/2}" y="78" font-size="{FS_SUB}" fill="{C["ink2"]}" text-anchor="middle">{esc(sub)}</text>')

    # confidence chip (functional square, no red)
    if conf:
        cc = FUNC.get(conf, C["ink2"])
        cx = LEFT
        S.append(f'<g data-role="confidence">')
        S.append(f'<rect x="{cx}" y="108" width="13" height="13" rx="2" fill="{cc}"/>')
        S.append(f'<text x="{cx+20}" y="119" font-size="{FS_TAG}" fill="{C["ink2"]}">置信度：{esc(conf)}</text>')
        S.append('</g>')

    # ---- segment band ----
    S.append('<g data-role="segments">')
    ty = BAND_TOP + BAND_H / 2
    for i, seg in enumerate(segs):
        x = LEFT + i * (seg_w + SEG_GAP)
        is_worst = (seg == worst)
        is_most = (seg == most)
        fill = C["red"] if is_worst else C["cream"]
        txt_col = C["white"] if is_worst else C["ink"]
        S.append(f'<g data-role="segment" data-name="{esc(seg)}"'
                 + (' data-worst="1"' if is_worst else '')
                 + (' data-most="1"' if is_most else '') + '>')
        S.append(f'<rect x="{x:.1f}" y="{BAND_TOP}" width="{seg_w:.1f}" height="{BAND_H}" '
                 f'rx="{RADIUS["card"]}" ry="{RADIUS["card"]}" fill="{fill}"/>')
        # most-likely emphasis: a navy frame (no left bar), tag above
        if is_most:
            S.append(f'<rect x="{x-3:.1f}" y="{BAND_TOP-3}" width="{seg_w+6:.1f}" height="{BAND_H+6}" '
                     f'rx="{RADIUS["card"]+2}" ry="{RADIUS["card"]+2}" fill="none" '
                     f'stroke="{C["navy"]}" stroke-width="2.5"/>')
            S.append(f'<text x="{x+seg_w/2:.1f}" y="{BAND_TOP-12}" font-size="{FS_TAG}" font-weight="700" '
                     f'fill="{C["navy"]}" text-anchor="middle">最可能区间</text>')
        # segment label (wrapped, breathing room)
        lines = wrap(seg, FS_SEG, seg_w - 24)
        y0 = ty - (len(lines) - 1) * (FS_SEG + 4) / 2 + FS_SEG * 0.35
        for j, ln in enumerate(lines):
            S.append(f'<text x="{x+seg_w/2:.1f}" y="{y0 + j*(FS_SEG+4):.1f}" font-size="{FS_SEG}" '
                     f'font-weight="700" fill="{txt_col}" text-anchor="middle">{esc(ln)}</text>')
        if is_worst:
            S.append(f'<text x="{x+seg_w/2:.1f}" y="{BAND_TOP+BAND_H+22:.1f}" font-size="{FS_TAG}" '
                     f'font-weight="700" fill="{C["red"]}" text-anchor="middle">最坏情形</text>')
        S.append('</g>')
    S.append('</g>')

    # ---- notes (关键不确定项) ----
    if notes:
        S.append('<g data-role="notes">')
        S.append(f'<text x="{LEFT}" y="{notes_top}" font-size="{FS_NOTE}" font-weight="700" '
                 f'fill="{C["ink"]}">关键不确定项</text>')
        for k, nt in enumerate(notes):
            S.append(f'<text x="{LEFT}" y="{notes_top + 24 + k*26:.1f}" font-size="{FS_NOTE}" '
                     f'fill="{C["ink2"]}">· {esc(nt)}</text>')
        S.append('</g>')

    # ---- worst-case derivation footer ----
    if why:
        fy = height - BOT + 6
        S.append(f'<text data-role="worst-why" x="{LEFT}" y="{fy:.1f}" font-size="{FS_NOTE}" '
                 f'fill="{C["ink2"]}">最坏情形由来：{esc(why)}</text>')

    S.append('</svg>')
    return "\n".join(S), WIDTH, height


def main(mapfile, out):
    svg, w, h = render(load_map(mapfile))
    open(out, "w", encoding="utf-8").write(svg)
    print(f"[outcome_band] wrote {out}  {w}x{h}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out.svg")
