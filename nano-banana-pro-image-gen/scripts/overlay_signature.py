#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朋友圈卡片落款/段标方块叠加器
作用：在 Gemini 生成的图上，强制覆盖
  1. 段标前的红方块（纯色矩形，无任何文字）
  2. 落款区「薛龙 96px + 合伙人 律师 · 北京观韬（上海）律师事务所 48px」同一行
输入：--input <Gemini 生成的 PNG> --output <最终 PNG> --source <公众号名>
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

# 颜色
GOLD = (229, 229, 229)        # 香槟金
RED = (210, 93, 56)           # 砖红
RED_DARK = (180, 70, 40)
BG_DARK = (10, 10, 10)

# 字号（按 1080x1920 画布）
SIZE_XUELONG = 96
SIZE_SUBSIG = 48
SIZE_SOURCE = 48
SIZE_SQUARE = 36             # 段前方块边长

# y 坐标
Y_SQUARE_TOP = 470           # 第一段方块顶部 y
Y_SQUARE_GAP = 350           # 段间距
SQUARE_LEFT = 80             # 方块左边 x

# 落款
Y_HRULE = 1600
Y_SOURCE = 1670
Y_SIG = 1750
SIG_LEFT = 80
SOURCE_LEFT = 80
SUBSIG_LEFT_PAD = 30         # 「薛龙」右边的间距


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    if bold:
        path = "C:/Windows/Fonts/msyhbd.ttc"
    else:
        path = "C:/Windows/Fonts/msyh.ttc"
    return ImageFont.truetype(path, size)


def get_text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def overlay(input_path: str, output_path: str, source: str):
    img = Image.open(input_path).convert("RGB")
    W, H = img.size
    # 校验画布 9:16
    assert abs(W / H - 9 / 16) < 0.02, f"画布比例异常: {W}x{H}"

    draw = ImageDraw.Draw(img, "RGBA")

    # ===== 1. 段前红方块（覆盖掉 Gemini 可能画错的「红方块」文字）=====
    for i in range(3):
        y = Y_SQUARE_TOP + i * Y_SQUARE_GAP
        # 画 36x36 砖红实心方块
        draw.rectangle(
            [SQUARE_LEFT, y, SQUARE_LEFT + SIZE_SQUARE, y + SIZE_SQUARE],
            fill=RED,
        )

    # ===== 2. 落款区 =====
    # 2.0 擦除底部 y=1450 以下所有内容
    # Gemini 已被 prompt 约束「y=1400 以下严禁画任何文字」
    draw.rectangle(
        [0, 1450, W, H],
        fill=BG_DARK,
    )
    # 渐变过渡
    for y_off in range(0, 30):
        alpha = int(255 * (1 - y_off / 30))
        draw.line(
            [(0, 1450 - y_off), (W, 1450 - y_off)],
            fill=(*BG_DARK, alpha),
        )

    # 2.1 香槟金横线
    draw.line(
        [(60, Y_HRULE), (W - 60, Y_HRULE)],
        fill=GOLD,
        width=1,
    )

    # 2.2 「摘自：xxx」48px
    font_source = get_font(SIZE_SOURCE, bold=False)
    source_text = f"摘自：{source}"
    draw.text((SOURCE_LEFT, Y_SOURCE), source_text, fill=GOLD, font=font_source)

    # 2.3 「薛龙」96px + 「合伙人 律师 · 北京观韬（上海）律师事务所」48px
    font_xl = get_font(SIZE_XUELONG, bold=True)
    font_sub = get_font(SIZE_SUBSIG, bold=True)

    # 测量「薛龙」宽度
    xl_w = get_text_width(draw, "薛龙", font_xl)
    # 「薛龙」y 坐标微调（96px 文字基线对齐）
    draw.text((SIG_LEFT, Y_SIG), "薛龙", fill=GOLD, font=font_xl)

    # 落款副紧贴「薛龙」右侧
    sub_text = "合伙人 律师 · 北京观韬（上海）律师事务所"
    # 落款副与「薛龙」基线对齐：96px 和 48px 同时画在 y=Y_SIG 时，
    # 96px 文字的视觉中心会偏低，所以把 48px 文字下移约 (96-48)/2 = 24px
    sub_y = Y_SIG + (SIZE_XUELONG - SIZE_SUBSIG) // 2
    sub_x = SIG_LEFT + xl_w + SUBSIG_LEFT_PAD
    draw.text((sub_x, sub_y), sub_text, fill=GOLD, font=font_sub)

    img.save(output_path, "PNG", optimize=True)
    # GBK-safe output
    import sys
    sys.stdout.buffer.write(f"OK overlay: {output_path}\n".encode("utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--source", required=True)
    args = p.parse_args()
    overlay(args.input, args.output, args.source)


if __name__ == "__main__":
    main()
