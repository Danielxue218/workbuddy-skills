#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朋友圈卡片全量渲染器（PIL 版 · 无 Gemini 依赖）
输入：标题、3 段段标+正文、来源公众号
输出：1080x1920 PNG，9:16
完全像素级控制：方块 36×36 纯色矩形、薛龙 96px、合伙人律师 48px 同一行
"""
import argparse
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 画布
W, H = 1080, 1920
# 颜色
GOLD = (229, 229, 229)
RED = (210, 93, 56)
BG_OUTER = (10, 10, 10)
BG_INNER = (28, 28, 28)
GOLD_FAINT = (60, 55, 45)

# 字号
SIZE_PAGE_HEADER = 96     # 今日法律观察
SIZE_DATE = 48            # 2026.06.23
SIZE_TITLE = 96           # 主标题
SIZE_BODY = 48            # 段标、正文、来源
SIZE_XUELONG = 96         # 薛龙
SIZE_SUBSIG = 48          # 合伙人律师...
SIZE_SQUARE = 36          # 红方块

# 字体路径
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_width(draw, text, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def make_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), BG_OUTER)
    px = img.load()
    cx, cy = W / 2, H * 0.30
    max_r = math.hypot(W, H) / 2
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy) / max_r
            d = min(max(d, 0), 1)
            t = (1 - d) ** 2.2
            r = int(BG_OUTER[0] * (1 - t) + BG_INNER[0] * t)
            g = int(BG_OUTER[1] * (1 - t) + BG_INNER[1] * t)
            b = int(BG_OUTER[2] * (1 - t) + BG_INNER[2] * t)
            px[x, y] = (r, g, b)
    return img


def draw_gavel(draw, cx, cy, color, alpha=255):
    # 用 RGBA overlay 画
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    c = (*color, alpha)
    # 槌头：平行四边形
    od.polygon(
        [(cx - 60, cy - 25), (cx + 60, cy - 25), (cx + 75, cy + 25), (cx - 75, cy + 25)],
        outline=c,
        width=3,
    )
    # 槌头顶部小斜线
    od.line([(cx - 60, cy - 25), (cx - 30, cy - 40)], fill=c, width=3)
    od.line([(cx + 60, cy - 25), (cx + 30, cy - 40)], fill=c, width=3)
    # 槌柄
    od.line([(cx - 5, cy + 25), (cx - 30, cy + 100)], fill=c, width=4)
    # 槌座
    od.rectangle(
        [cx - 90, cy + 100, cx + 50, cy + 120],
        outline=c,
        width=3,
    )
    return overlay


def wrap_text(draw, text, font, max_width):
    """简单字符级换行"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if text_width(draw, test, font) > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def render_card(
    output_path: str,
    title: str,
    date_str: str,
    segments: list,  # [{"label": "核心定性", "body": "..."}, ...]
    source: str,
):
    img = make_bg()
    draw = ImageDraw.Draw(img, "RGBA")

    # === [1] 页眉 y=40-130 ===
    f_page = get_font(SIZE_PAGE_HEADER, bold=True)
    f_date = get_font(SIZE_DATE, bold=True)
    # 左侧「今日法律观察」
    page_text = "今日法律观察"
    draw.text((60, 60 - 12), page_text, fill=GOLD, font=f_page)  # 视觉居中微调
    # 右侧日期戳
    date_w = text_width(draw, date_str, f_date)
    draw.text((W - 60 - date_w, 90 - 8), date_str, fill=RED, font=f_date)
    # 居中法槌图标 y=200
    gavel_overlay = draw_gavel(draw, W // 2, 200, GOLD_FAINT, alpha=140)
    img = Image.alpha_composite(img.convert("RGBA"), gavel_overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    # === [2] 主标题 y=400-580 ===
    f_title = get_font(SIZE_TITLE, bold=True)
    title_w = text_width(draw, title, f_title)
    draw.text(((W - title_w) // 2, 460), title, fill=GOLD, font=f_title)
    # 1px 砖红短横线
    line_w = int(title_w * 0.5)
    draw.line(
        [((W - line_w) // 2, 600), ((W + line_w) // 2, 600)],
        fill=RED,
        width=2,
    )

    # === [3] 三段正文 y=700-1500（硬约束：3 段 + 段标 + 2 行/段） ===
    f_label = get_font(SIZE_BODY, bold=True)
    f_body = get_font(SIZE_BODY, bold=False)
    max_text_w = W - 80 - SIZE_SQUARE - 30 - 80  # 文字最大宽度

    y_cursor = 720
    line_h = 58
    label_h = 60
    max_lines_per_seg = 2  # 硬约束：每段最多 2 行
    seg_total_h = label_h + max_lines_per_seg * line_h + 30  # 段标 + 2行 + 段尾间距
    for i, seg in enumerate(segments):
        # 红方块（始终在段标左侧）
        sq_x, sq_y = 80, y_cursor + 8
        draw.rectangle([sq_x, sq_y, sq_x + SIZE_SQUARE, sq_y + SIZE_SQUARE], fill=RED)
        # 段标
        label = seg["label"] + "："
        draw.text((sq_x + SIZE_SQUARE + 20, y_cursor), label, fill=RED, font=f_label)
        # 正文（最多 max_lines_per_seg 行）
        body_lines = wrap_text(draw, seg["body"], f_body, max_text_w)
        body_lines = body_lines[:max_lines_per_seg]
        body_y = y_cursor + label_h
        for line in body_lines:
            draw.text((sq_x + SIZE_SQUARE + 20, body_y), line, fill=GOLD, font=f_body)
            body_y += line_h
        y_cursor += seg_total_h
        # 三段间分隔线
        if i < len(segments) - 1:
            draw.line([(80, y_cursor - 12), (W - 80, y_cursor - 12)], fill=RED, width=1)

    # === [4] 落款 y=1600-1900 ===
    # 香槟金横线
    draw.line([(60, 1620), (W - 60, 1620)], fill=GOLD, width=1)
    # 摘自：xxx
    f_source = get_font(SIZE_BODY, bold=False)
    source_text = f"摘自：{source}"
    draw.text((80, 1660), source_text, fill=GOLD, font=f_source)
    # 薛龙 96px
    f_xl = get_font(SIZE_XUELONG, bold=True)
    f_sub = get_font(SIZE_SUBSIG, bold=True)
    draw.text((80, 1740), "薛龙", fill=GOLD, font=f_xl)
    # 落款副紧贴右侧 48px
    xl_w = text_width(draw, "薛龙", f_xl)
    sub_text = "合伙人 · 律师 · 北京观韬（上海）"
    sub_x = 80 + xl_w + 30
    sub_y = 1740 + (SIZE_XUELONG - SIZE_SUBSIG) // 2 + 8
    draw.text((sub_x, sub_y), sub_text, fill=GOLD, font=f_sub)

    # 保存
    img.convert("RGB").save(output_path, "PNG", optimize=True)
    sys.stdout.buffer.write(f"OK card: {output_path}\n".encode("utf-8"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True, help="JSON 路径")
    p.add_argument("--out-dir", required=True, help="输出目录")
    args = p.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    date_str = data["date"].replace("-", ".")

    for item in data["selected"]:
        idx = int(item["card"])
        title = item["title"]
        source = item["source"]
        segments = item["segments"]  # 3 段
        out_path = os.path.join(args.out_dir, f"{data['date']}-{idx:02d}-{title}.png")
        render_card(out_path, title, date_str, segments, source)


if __name__ == "__main__":
    main()
