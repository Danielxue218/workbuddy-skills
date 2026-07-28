#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""入口：semantic-map.json -> final.svg (+ final.png)。

    python render.py <semantic-map.json> [out_basename]

按 map 的 layout 字段派发到本项目三张图：
    elements_matrix -> render_elements_matrix   （图一 · 要件-证据对照矩阵）
    issues_focus    -> render_issues_focus       （图二 · 争议焦点汇聚）
    outcome_band    -> render_outcome_band        （图三 · 结果预判区间带）

SVG 是主交付、可编辑；PNG 为派生预览（无专用渲染器时回落 soffice→PDF→pdftoppm）。
模型只吐 semantic-map.json、绝不碰坐标；几何全由确定性脚本生成。
"""
import sys, os, shutil, subprocess
from common import load_map, validate_map
import render_elements_matrix, render_issues_focus, render_outcome_band


def choose(m):
    layout = m.get("layout", "")
    if layout == "elements_matrix":
        return render_elements_matrix
    if layout == "issues_focus":
        return render_issues_focus
    if layout == "outcome_band":
        return render_outcome_band
    # heuristic fallback
    if m.get("rows"):
        return render_elements_matrix
    if m.get("foci"):
        return render_issues_focus
    return render_outcome_band


def svg_to_png(svg_path, png_path, dpi=150):
    """SVG -> PNG，优先专用渲染器，回落 soffice(LibreOffice)->PDF->pdftoppm。"""
    def has(x):
        return shutil.which(x) is not None
    if has("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-d", str(dpi), "-p", str(dpi), svg_path, "-o", png_path], check=True)
        return "rsvg-convert"
    if has("resvg"):
        subprocess.run(["resvg", "--dpi", str(dpi), svg_path, png_path], check=True)
        return "resvg"
    if has("inkscape"):
        subprocess.run(["inkscape", svg_path, "--export-type=png",
                        f"--export-dpi={dpi}", f"--export-filename={png_path}"], check=True)
        return "inkscape"
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path, dpi=dpi)
        return "cairosvg"
    except Exception:
        pass
    if has("soffice") and has("pdftoppm"):
        outdir = os.path.dirname(os.path.abspath(png_path)) or "."
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, svg_path],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pdf = os.path.join(outdir, os.path.basename(os.path.splitext(svg_path)[0] + ".pdf"))
        prefix = os.path.splitext(png_path)[0]
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, prefix], check=True)
        produced = prefix + "-1.png"
        if os.path.exists(produced):
            os.replace(produced, png_path)
        return "soffice+pdftoppm"
    raise RuntimeError("未找到 SVG->PNG 渲染器。装 rsvg-convert/resvg/inkscape/cairosvg，或 LibreOffice(soffice)+pdftoppm。")


def main(mapfile, base="final"):
    m = load_map(mapfile)
    mod = choose(m)
    svg_path = base + ".svg"
    try:
        validate_map(m)
        svg, w, h = mod.render(m)
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return 1
    open(svg_path, "w", encoding="utf-8").write(svg)
    print(f"SVG: {svg_path}  {w}x{h}")
    png_path = base + ".png"
    try:
        engine = svg_to_png(svg_path, png_path)
        print(f"PNG: {png_path}  (via {engine})")
    except Exception as e:
        print(f"PNG skipped: {e}")
    try:
        import audit
        audit.report(m)
    except Exception as e:
        print(f"(audit unavailable: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "final"))
