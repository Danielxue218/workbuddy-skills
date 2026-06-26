#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朋友圈卡片纯背景生成器（PIL 版）
深灰径向渐变 + 极淡法槌背景纹
"""
import argparse
import math
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
# 颜色
BG_OUTER = (10, 10, 10)
BG_INNER = (28, 28, 28)
GOLD_FAINT = (60, 55, 45)


def make_gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG_OUTER)
    px = img.load()
    cx, cy = W / 2, H * 0.35
    max_r = math.hypot(W, H) / 2
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy) / max_r
            d = min(max(d, 0), 1)
            t = (1 - d) ** 2
            r = int(BG_OUTER[0] * (1 - t) + BG_INNER[0] * t)
            g = int(BG_OUTER[1] * (1 - t) + BG_INNER[1] * t)
            b = int(BG_OUTER[2] * (1 - t) + BG_INNER[2] * t)
            px[x, y] = (r, g, b)
    return img


def draw_faint_gavel(draw: ImageDraw.ImageDraw):
    # 极淡的法槌几何图标，居中略上 y=850
    cx, cy = W // 2, 850
    # 槌头
    draw.polygon(
        [
            (cx - 80, cy - 30),
            (cx + 80, cy - 30),
            (cx + 100, cy + 30),
            (cx - 100, cy + 30),
        ],
        outline=GOLD_FAINT,
        width=2,
    )
    # 槌柄
    draw.line(
        [(cx - 5, cy + 30), (cx - 30, cy + 150)],
        fill=GOLD_FAINT,
        width=4,
    )
    # 槌座
    draw.rectangle(
        [cx - 110, cy + 150, cx + 60, cy + 175],
        outline=GOLD_FAINT,
        width=2,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    img = make_gradient_bg()
    draw = ImageDraw.Draw(img)
    draw_faint_gavel(draw)
    img.save(args.output, "PNG", optimize=True)
    # GBK-safe print
    import sys
    sys.stdout.buffer.write(f"OK bg: {args.output}\n".encode("utf-8"))


if __name__ == "__main__":
    main()
