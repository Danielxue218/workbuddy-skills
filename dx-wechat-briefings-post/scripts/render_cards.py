#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薛龙律师朋友圈卡片渲染器 v3
- 9:16 竖版，2K 分辨率
- 配色：#121212(80%) / #E5E5E5(15%) / #D25D38(5%)
- 单卡结构：页眉(无顶横线) → 中心标题(粗大) → 1px红线 → 3段(核心定性/法理审视/应对建议) → 1px金线 → 出处 → 「薛龙」粗大 + 落款(加粗小)
- 用 PIL 直接画，100% 文字控制
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ===== 字体路径（思源/微软雅黑系列）=====
FONT_DIR = r"C:\Windows\Fonts"
FONT_REGULAR = os.path.join(FONT_DIR, "msyh.ttc")       # 微软雅黑 Regular
FONT_BOLD = os.path.join(FONT_DIR, "msyhbd.ttc")        # 微软雅黑 Bold
FONT_LIGHT = os.path.join(FONT_DIR, "msyhl.ttc")        # 微软雅黑 Light

# ===== 配色 =====
BG = (18, 18, 18)            # #121212
GOLD = (229, 229, 229)       # #E5E5E5
RED = (210, 93, 56)          # #D25D38
WHITE = (255, 255, 255)

# ===== 画布尺寸（9:16，2K 标准 1440x2560）=====
W, H = 1440, 2560
SCALE = 2  # 内部用 2 倍像素密度提升清晰度
CW, CH = W * SCALE, H * SCALE

# ===== 字号档位（v3 硬约束）=====
# 标题号 = 中心标题/「今日法律观察」/「薛龙」
# 正文字号 = 段标/正文/日期戳/落款副
SIZE_TITLE = 96 * SCALE      # 中心标题 + 今日法律观察 + 薛龙
SIZE_BODY = 50 * SCALE       # 正文 + 段标 + 日期戳 + 落款副 + 出处
SIZE_SUB = 44 * SCALE        # 副标题（如果需要）
SIZE_FOOT = 48 * SCALE       # 出处


def get_font(path, size, index=0):
    """加载字体"""
    return ImageFont.truetype(path, size, index=index)


def measure_text(draw, text, font):
    """测量文本尺寸"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_dashed_line_h(draw, x1, y, x2, dash=8*SCALE, gap=4*SCALE, color=RED, width=2*SCALE):
    """画虚线"""
    x = x1
    while x < x2:
        draw.line([(x, y), (min(x + dash, x2), y)], fill=color, width=width)
        x += dash + gap


def render_card(out_path, title, body1, body2, body3, source):
    """渲染单张卡片"""
    img = Image.new("RGB", (CW, CH), BG)
    draw = ImageDraw.Draw(img)

    # 加载字体
    f_title_bold = get_font(FONT_BOLD, SIZE_TITLE)
    f_body_reg = get_font(FONT_REGULAR, SIZE_BODY)
    f_body_bold = get_font(FONT_BOLD, SIZE_BODY)

    # 边距
    M = 120 * SCALE  # 左右边距

    # === 顶部页眉区（无横线）===
    # 左：今日法律观察（粗·大）
    header_text = "今日法律观察"
    draw.text((M, 100 * SCALE), header_text, font=f_title_bold, fill=GOLD)
    # 右：日期戳 2026.06.22（加粗·正文字号·红色）
    date_text = "2026.06.22"
    dw, dh = measure_text(draw, date_text, f_body_bold)
    draw.text((CW - M - dw, 130 * SCALE), date_text, font=f_body_bold, fill=RED)

    # 中央装饰图标（极简金线矩形+短竖线，模拟法槌抽象），位置在页眉与主标题之间居中
    icon_cx = CW // 2
    icon_y = 280 * SCALE
    # 槌头（空心方框）
    box_w, box_h = 70 * SCALE, 30 * SCALE
    draw.rectangle(
        [(icon_cx - box_w // 2, icon_y - box_h // 2),
         (icon_cx + box_w // 2, icon_y + box_h // 2)],
        outline=GOLD, width=3 * SCALE
    )
    # 锤柄（短竖线）
    draw.line(
        [(icon_cx, icon_y + box_h // 2 + 5 * SCALE),
         (icon_cx, icon_y + box_h // 2 + 25 * SCALE)],
        fill=GOLD, width=3 * SCALE
    )
    # 底座（短横线）
    base_w = 40 * SCALE
    draw.line(
        [(icon_cx - base_w // 2, icon_y + box_h // 2 + 30 * SCALE),
         (icon_cx + base_w // 2, icon_y + box_h // 2 + 30 * SCALE)],
        fill=GOLD, width=3 * SCALE
    )

    # === 中心主标题（粗·大）===
    title_y = 380 * SCALE
    tw, th = measure_text(draw, title, f_title_bold)
    title_x = (CW - tw) / 2
    draw.text((title_x, title_y), title, font=f_title_bold, fill=GOLD)

    # 主标题下方 1px 砖红短横线（居中，宽度不超过标题 60%）
    line_y = title_y + th + 30 * SCALE
    line_w = min(tw * 0.6, 600 * SCALE)
    line_x1 = (CW - line_w) / 2
    line_x2 = line_x1 + line_w
    draw.line([(line_x1, line_y), (line_x2, line_y)], fill=RED, width=2 * SCALE)

    # === 3 段正文区 ===
    body_start_y = line_y + 100 * SCALE
    body_h = 90 * SCALE  # 每段高度（含间距）
    section_gap = 60 * SCALE

    sections = [
        ("■", "核心定性", body1, RED),
        ("■", "法理审视", body2, RED),
        ("■", "应对建议", body3, RED),
    ]

    for i, (marker, label, text, color) in enumerate(sections):
        y = body_start_y + i * (body_h + section_gap)

        # 砖红实心方块（8-10px 见方）
        square_size = 28 * SCALE
        square_x = M
        square_y = y + 10 * SCALE
        draw.rectangle(
            [(square_x, square_y), (square_x + square_size, square_y + square_size)],
            fill=RED
        )

        # 段标「核心定性：」砖红加粗
        label_text = f"{label}："
        lw, lh = measure_text(draw, label_text, f_body_bold)
        draw.text((square_x + square_size + 16 * SCALE, y), label_text, font=f_body_bold, fill=RED)

        # 正文（香槟金，自动换行）
        text_x = square_x + square_size + 16 * SCALE + lw + 12 * SCALE
        text_w = CW - text_x - M
        wrapped = wrap_text(text, f_body_reg, text_w, draw)
        line_y_text = y
        for line in wrapped:
            draw.text((text_x, line_y_text), line, font=f_body_reg, fill=GOLD)
            _, lh_line = measure_text(draw, line, f_body_reg)
            line_y_text += lh_line + 8 * SCALE

        # 段间 1px 砖红细线
        if i < len(sections) - 1:
            sep_y = y + body_h + section_gap / 2
            draw.line([(M, sep_y), (CW - M, sep_y)], fill=RED, width=1 * SCALE)

    # === 底部出处区 ===
    foot_y = CH - 400 * SCALE

    # 1px 香槟金贯穿横线
    draw.line([(M, foot_y), (CW - M, foot_y)], fill=GOLD, width=2 * SCALE)

    # 出处「摘自：XXX」（正文字号·不加粗）
    source_text = f"摘自：{source}"
    draw.text((M, foot_y + 40 * SCALE), source_text, font=f_body_reg, fill=GOLD)

    # 「薛龙」（粗·大·香槟金）
    name_y = foot_y + 140 * SCALE
    draw.text((M, name_y), "薛龙", font=f_title_bold, fill=GOLD)

    # 落款副「合伙人/律师 · 北京观韬（上海）律师事务所」（加粗·正文字号）
    sub_text = "合伙人/律师 · 北京观韬（上海）律师事务所"
    sw, sh = measure_text(draw, sub_text, f_body_bold)
    draw.text((CW - M - sw, name_y + 30 * SCALE), sub_text, font=f_body_bold, fill=GOLD)

    # 保存（缩到目标尺寸，保持清晰度）
    final = img.resize((W, H), Image.LANCZOS)
    final.save(out_path, "PNG", optimize=True)
    print(f"✓ {os.path.basename(out_path)}")


def wrap_text(text, font, max_width, draw):
    """自动换行"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        w, _ = measure_text(draw, test, font)
        if w > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ===== 8 张卡片内容 =====
CARDS = [
    {
        "title": "股权代持的显名化路径",
        "body1": "上海二中院白皮书定调，实际出资人不得直接向公司主张股东权利。",
        "body2": "隐名股东须先走确权之诉再走显名程序，其他股东仍享有优先购买权。",
        "body3": "拟IPO企业应提前清理代持，家族企业应审慎设计代持架构与退出机制。",
        "source": "宜律无忧",
    },
    {
        "title": "对赌回购义务的边界",
        "body1": "上海虹口法院判决，投资方回购权不因其他股东优先购买权受阻。",
        "body2": "对赌协议中股权回购条款独立有效，回购义务人不得以优先购买权抗辩。",
        "body3": "投资方应在对赌协议中明确回购价格公式与通知 SOP，锁定回购义务主体。",
        "source": "诉讼攻略",
    },
    {
        "title": "股东个人卡走账的连带责任",
        "body1": "最高法提级管辖典型案例，股东以个人卡收取公司款项构成财产混同。",
        "body2": "人格混同情形下，债权人可主张实施混同的股东对公司债务承担连带责任。",
        "body3": "民营企业应建立独立财务制度，债权人可在执行阶段追加混同股东。",
        "source": "执行实务与诉讼实务",
    },
    {
        "title": "拒执罪前置转移的认定",
        "body1": "拒执罪的时点前移，民事裁判前转移财产亦可构成拒执罪。",
        "body2": "打击\"诉前转移+诉中规避\"组合打法，刑民交叉惩戒力度显著加强。",
        "body3": "被执行人应避免任何形式规避执行，债权人可主动提交转移线索触发刑责。",
        "source": "牛津律师团队",
    },
    {
        "title": "反商业贿赂的合规不起诉",
        "body1": "合规不起诉制度落地，企业反舞弊体系可换取不起诉决定。",
        "body2": "合规激励与刑事惩戒并举，倒逼企业建立嵌入式合规闭环。",
        "body3": "大中型企业应建立反贿赂合规体系，主动申报可换取合规不起诉。",
        "source": "金诚同达",
    },
    {
        "title": "股东代表诉讼的启动门槛",
        "body1": "股东代表诉讼的前置程序与原告资格边界，决定诉权能否实质启动。",
        "body2": "穷尽内部救济仍是主流裁判口径，董事催告与监事会请求缺一不可。",
        "body3": "拟启动股东代表诉讼的股东应前置固定催告证据与董事会决议瑕疵。",
        "source": "法言法语谈法理",
    },
    {
        "title": "爱宠精神损害赔偿的认定",
        "body1": "宠物受害引发精神损害赔偿请求，法院支持路径正在拓宽。",
        "body2": "宠物作为\"特定物\"具有人格利益投射属性，精神损害赔偿有据可循。",
        "body3": "宠物遭受侵害应同步主张财产损失与精神损害，留存饲养与情感证据。",
        "source": "上海普陀法院",
    },
    {
        "title": "异宠交易的合规闭环",
        "body1": "异宠交易从野蛮生长进入合规收紧，4350 只异宠查获释放监管信号。",
        "body2": "交易资质、检疫证明、动物福利三重门槛共同构成合规闭环。",
        "body3": "从业者应取得专项资质并留痕全链路，消费者应核验卖家合法来源。",
        "source": "宠物行业白皮书",
    },
]


def main():
    out_dir = r"E:\workbuddy\朋友圈发文\2026-06-22\images"
    os.makedirs(out_dir, exist_ok=True)

    for i, card in enumerate(CARDS, 1):
        filename = f"2026-06-22-{i:02d}-{card['title']}.png"
        out_path = os.path.join(out_dir, filename)
        render_card(
            out_path,
            card["title"],
            card["body1"],
            card["body2"],
            card["body3"],
            card["source"],
        )
    print(f"\n✅ 全部 {len(CARDS)} 张渲染完成")


if __name__ == "__main__":
    main()
