#!/usr/bin/env python3
"""
generate-flowchart.py · v1.0.0

从结构化 JSON 数据生成精美业务流程图 SVG。

设计原则:
- AI 负责识别合同中的业务节点,输出 flowchart-data.json
- Python 按 examples/02-flowchart-sample.svg 的铁律渲染 SVG
- 所有色值、尺寸、坐标都由代码固化,杜绝"视觉变形"问题

核心铁律(与 02-flowchart-sample.svg 严格对标):
- 所有色块无边框(只有 fill,无 stroke)
- 菱形 4 个尖角都是小圆角(Q 贝塞尔实现)
- 循环回路用多段直线 + stroke-linejoin="round",不用 Q 弧线
- 回路避开主流程和卡片(MidX 偏移到主列外,TargetY 落在菱形斜边)
- 箭头颜色与连线颜色严格一致(灰色箭头配灰色线)

用法:
    python3 scripts/generate-flowchart.py \\
        --output "<输出目录>/业务流程图.svg" \\
        --data "<路径>/flowchart-data.json"

作者:缪奇川(Miao Qichuan)
"""

import json
import argparse
from pathlib import Path


# ============================================================
# 铁律常量(从 examples/02-flowchart-sample.svg 逐行核对提取)
# ============================================================

# 画布
CANVAS_WIDTH = 1240
MAIN_X = 620  # 主列水平中心

# 色板
COLOR_TERMINAL = "#003153"      # 深蓝·终端节点
COLOR_PARTY_A = "#0070C0"        # 甲方蓝
COLOR_PARTY_B = "#006A4E"        # 乙方绿
COLOR_BOTH = "#F6C12C"            # 双方黄
COLOR_DECISION = "#F5F0E1"        # 米白·判断菱形
COLOR_EXCEPTION = "#C92C2C"       # 朱砂红·异常
# 副文字色
COLOR_SUB_TERMINAL = "#C8D4E0"
COLOR_SUB_A = "#D9EBF7"
COLOR_SUB_B = "#D4E8DE"
COLOR_SUB_BOTH_1 = "#3A3A3A"
COLOR_SUB_BOTH_2 = "#4A4A4A"
COLOR_SUB_DECISION_1 = "#5A5A5A"
COLOR_SUB_DECISION_2 = "#808080"
COLOR_SUB_EXCEPTION = "#F3D4D4"
# 文字色
COLOR_DARK = "#2A2A2A"
COLOR_DARKER = "#1A1A1A"
COLOR_GRAY_TEXT = "#4A4A4A"
COLOR_GRAY_TEXT_LIGHT = "#606060"
COLOR_GRAY_TEXT_VLIGHT = "#A0A0A0"
# 线条色
COLOR_LINE_MAIN = "#9CA3AF"        # 主流程·浅灰
COLOR_LINE_LOOP = "#707070"        # 循环回路·深灰
COLOR_LINE_EXCEPTION = "#C92C2C"   # 异常升级·朱砂红

# 节点尺寸
NODE_WIDTH = 440
NODE_HEIGHT = 92
NODE_RX = 14
NODE_X = MAIN_X - NODE_WIDTH // 2  # 400

TERMINAL_START_WIDTH = 300
TERMINAL_START_HEIGHT = 68
TERMINAL_START_RX = 34

TERMINAL_END_WIDTH = 300
TERMINAL_END_HEIGHT = 58
TERMINAL_END_RX = 29

SIDE_NODE_WIDTH_DEFAULT = 240
SIDE_NODE_X = 890  # 侧路节点 x

DIAMOND_HALF_WIDTH = 180
DIAMOND_HALF_HEIGHT = 70
DIAMOND_CORNER_RADIUS = 8

# 间距
NODE_GAP = 40  # 节点之间的间距(箭头空间)
TITLE_AREA_HEIGHT = 180  # 从顶部到第一个节点的距离

# 字体
FONT_FAMILY = "'PingFang SC','Microsoft YaHei','Noto Sans SC','Helvetica Neue',Arial,sans-serif"


# ============================================================
# SVG 组件构造函数
# ============================================================

def svg_defs():
    """箭头 marker 定义"""
    return f'''  <defs>
    <marker id="arrGray" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 12 6 L 0 12 z" fill="{COLOR_LINE_MAIN}"/>
    </marker>
    <marker id="arrGrayDark" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 12 6 L 0 12 z" fill="{COLOR_LINE_LOOP}"/>
    </marker>
    <marker id="arrRed" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M 0 0 L 12 6 L 0 12 z" fill="{COLOR_LINE_EXCEPTION}"/>
    </marker>
  </defs>

  <rect width="{CANVAS_WIDTH}" height="{{CANVAS_HEIGHT}}" fill="#FFFFFF"/>
'''


def svg_title(title, subtitle):
    """顶部标题区"""
    return f'''
  <!-- 标题区 -->
  <text x="{MAIN_X}" y="62" text-anchor="middle" font-size="28" font-weight="700" fill="{COLOR_DARKER}" letter-spacing="1px">{title}</text>
  <text x="{MAIN_X}" y="96" text-anchor="middle" font-size="13.5" fill="{COLOR_GRAY_TEXT_LIGHT}" letter-spacing="0.5px">{subtitle}</text>
'''


def svg_legend():
    """图例区(固定)"""
    return f'''
  <!-- 图例区 -->
  <g transform="translate(80, 128)">
    <text x="0" y="0" font-size="10.5" letter-spacing="4px" fill="{COLOR_GRAY_TEXT_VLIGHT}">图例</text>

    <rect x="0" y="14" width="14" height="14" rx="3" fill="{COLOR_PARTY_A}"/>
    <text x="22" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">甲方节点</text>

    <rect x="92" y="14" width="14" height="14" rx="3" fill="{COLOR_PARTY_B}"/>
    <text x="114" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">乙方节点</text>

    <rect x="184" y="14" width="14" height="14" rx="3" fill="{COLOR_BOTH}"/>
    <text x="206" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">双方节点</text>

    <rect x="266" y="14" width="14" height="14" rx="3" fill="{COLOR_DECISION}"/>
    <text x="288" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">判断节点</text>

    <rect x="348" y="14" width="14" height="14" rx="3" fill="{COLOR_EXCEPTION}"/>
    <text x="370" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">异常节点</text>

    <rect x="430" y="14" width="22" height="14" rx="7" fill="{COLOR_TERMINAL}"/>
    <text x="460" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">终端节点</text>

    <line x1="556" y1="21" x2="584" y2="21" stroke="{COLOR_LINE_MAIN}" stroke-width="2" marker-end="url(#arrGray)"/>
    <text x="594" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">主流程</text>

    <line x1="666" y1="21" x2="696" y2="21" stroke="{COLOR_LINE_LOOP}" stroke-width="1.8" marker-end="url(#arrGrayDark)"/>
    <text x="706" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">循环回路</text>

    <line x1="796" y1="21" x2="824" y2="21" stroke="{COLOR_LINE_EXCEPTION}" stroke-width="1.8" marker-end="url(#arrRed)"/>
    <text x="834" y="25" font-size="11" fill="{COLOR_GRAY_TEXT}">异常升级</text>
  </g>
'''


def svg_terminal_start(y, title, sub1="", sub2=""):
    """起点终端节点(深蓝胶囊)"""
    x = MAIN_X - TERMINAL_START_WIDTH // 2
    out = f'''
  <!-- 起点终端节点 -->
  <rect x="{x}" y="{y}" width="{TERMINAL_START_WIDTH}" height="{TERMINAL_START_HEIGHT}" rx="{TERMINAL_START_RX}" ry="{TERMINAL_START_RX}" fill="{COLOR_TERMINAL}"/>
  <text x="{MAIN_X}" y="{y + 32}" text-anchor="middle" font-size="16" font-weight="700" fill="#FFFFFF">{title}</text>'''
    if sub1:
        out += f'''
  <text x="{MAIN_X}" y="{y + 52}" text-anchor="middle" font-size="11" fill="{COLOR_SUB_TERMINAL}">{sub1}</text>'''
    return out


def svg_terminal_end(y, title):
    """终点终端节点(深蓝胶囊·略矮)"""
    x = MAIN_X - TERMINAL_END_WIDTH // 2
    return f'''
  <!-- 终点终端节点 -->
  <rect x="{x}" y="{y}" width="{TERMINAL_END_WIDTH}" height="{TERMINAL_END_HEIGHT}" rx="{TERMINAL_END_RX}" ry="{TERMINAL_END_RX}" fill="{COLOR_TERMINAL}"/>
  <text x="{MAIN_X}" y="{y + 34}" text-anchor="middle" font-size="15" font-weight="700" fill="#FFFFFF">{title}</text>'''


def svg_main_node(y, node_type, title, sub1="", sub2=""):
    """主流程节点(甲方/乙方/双方)"""
    fill_map = {
        "party_a": (COLOR_PARTY_A, "#FFFFFF", COLOR_SUB_A, COLOR_SUB_A),
        "party_b": (COLOR_PARTY_B, "#FFFFFF", COLOR_SUB_B, COLOR_SUB_B),
        "both_parties": (COLOR_BOTH, COLOR_DARK, COLOR_SUB_BOTH_1, COLOR_SUB_BOTH_2),
    }
    fill, main_color, sub1_color, sub2_color = fill_map[node_type]

    out = f'''
  <!-- 节点: {title} -->
  <rect x="{NODE_X}" y="{y}" width="{NODE_WIDTH}" height="{NODE_HEIGHT}" rx="{NODE_RX}" ry="{NODE_RX}" fill="{fill}"/>
  <text x="{MAIN_X}" y="{y + 33}" text-anchor="middle" font-size="16" font-weight="700" fill="{main_color}">{title}</text>'''
    if sub1:
        out += f'''
  <text x="{MAIN_X}" y="{y + 57}" text-anchor="middle" font-size="12" fill="{sub1_color}">{sub1}</text>'''
    if sub2:
        out += f'''
  <text x="{MAIN_X}" y="{y + 77}" text-anchor="middle" font-size="11" fill="{sub2_color}">{sub2}</text>'''
    return out


def svg_diamond(y_center, title, sub1="", sub2=""):
    """判断菱形(四尖角小圆角)

    y_center: 菱形中心 y 坐标
    菱形宽 360(±180),高 140(±70)
    """
    out = f'''
  <!-- 判断菱形: {title} -->
  <g transform="translate({MAIN_X}, {y_center})">
    <path d="M -172 -4
             L -8 -66
             Q 0 -70, 8 -66
             L 172 -4
             Q 180 0, 172 4
             L 8 66
             Q 0 70, -8 66
             L -172 4
             Q -180 0, -172 -4 Z"
          fill="{COLOR_DECISION}"/>
    <text x="0" y="-10" text-anchor="middle" font-size="15" font-weight="700" fill="{COLOR_DARK}">{title}</text>'''
    if sub1:
        out += f'''
    <text x="0" y="12" text-anchor="middle" font-size="11" fill="{COLOR_SUB_DECISION_1}">{sub1}</text>'''
    if sub2:
        out += f'''
    <text x="0" y="32" text-anchor="middle" font-size="10.5" fill="{COLOR_SUB_DECISION_2}">{sub2}</text>'''
    out += '\n  </g>'
    return out


def svg_side_node(x, y, node_type, title, sub1="", sub2="", width=SIDE_NODE_WIDTH_DEFAULT):
    """侧路节点(默认宽 240)"""
    fill_map = {
        "party_a": (COLOR_PARTY_A, "#FFFFFF", COLOR_SUB_A, COLOR_SUB_A),
        "party_b": (COLOR_PARTY_B, "#FFFFFF", COLOR_SUB_B, COLOR_SUB_B),
        "exception": (COLOR_EXCEPTION, "#FFFFFF", COLOR_SUB_EXCEPTION, COLOR_SUB_EXCEPTION),
    }
    fill, main_color, sub1_color, sub2_color = fill_map[node_type]
    x_center = x + width // 2

    out = f'''
  <!-- 侧路节点: {title} -->
  <rect x="{x}" y="{y}" width="{width}" height="{NODE_HEIGHT}" rx="{NODE_RX}" ry="{NODE_RX}" fill="{fill}"/>
  <text x="{x_center}" y="{y + 33}" text-anchor="middle" font-size="16" font-weight="700" fill="{main_color}">{title}</text>'''
    if sub1:
        out += f'''
  <text x="{x_center}" y="{y + 57}" text-anchor="middle" font-size="12" fill="{sub1_color}">{sub1}</text>'''
    if sub2:
        out += f'''
  <text x="{x_center}" y="{y + 77}" text-anchor="middle" font-size="11" fill="{sub2_color}">{sub2}</text>'''
    return out


def svg_main_arrow(from_y, to_y, x=None):
    """主流程箭头(灰色·竖直)"""
    if x is None:
        x = MAIN_X
    return f'  <line x1="{x}" y1="{from_y}" x2="{x}" y2="{to_y}" stroke="{COLOR_LINE_MAIN}" stroke-width="2" marker-end="url(#arrGray)"/>\n'


def svg_branch_pass_arrow(from_y, to_y):
    """菱形向下·合格分支(含绿底胶囊)"""
    label_y = from_y + 8
    label_text_y = label_y + 15
    return f'''
  <!-- 合格分支 -->
  <line x1="{MAIN_X}" y1="{from_y}" x2="{MAIN_X}" y2="{to_y}" stroke="{COLOR_LINE_MAIN}" stroke-width="2" marker-end="url(#arrGray)"/>
  <rect x="{MAIN_X - 27}" y="{label_y}" width="54" height="22" rx="11" ry="11" fill="{COLOR_PARTY_B}"/>
  <text x="{MAIN_X}" y="{label_text_y}" text-anchor="middle" font-size="11" font-weight="600" fill="#FFFFFF">合格</text>
'''


def svg_branch_fail_arrow(diamond_y_center, target_x):
    """菱形向右·不合格分支(含红底胶囊)

    diamond_y_center: 菱形中心 y
    target_x: 侧路节点左边 x
    """
    # 菱形右尖角 x = MAIN_X + 180 = 800,y = diamond_y_center
    arrow_start_x = MAIN_X + DIAMOND_HALF_WIDTH
    arrow_end_x = target_x - 4
    label_x = arrow_start_x + 13
    label_text_x = label_x + 27
    label_y = diamond_y_center - 11
    label_text_y = label_y + 15
    return f'''
  <!-- 不合格分支 -->
  <line x1="{arrow_start_x}" y1="{diamond_y_center}" x2="{arrow_end_x}" y2="{diamond_y_center}" stroke="{COLOR_LINE_MAIN}" stroke-width="2" marker-end="url(#arrGray)"/>
  <rect x="{label_x}" y="{label_y}" width="54" height="22" rx="11" ry="11" fill="{COLOR_EXCEPTION}"/>
  <text x="{label_text_x}" y="{label_text_y}" text-anchor="middle" font-size="11" font-weight="600" fill="#FFFFFF">不合格</text>
'''


def svg_loop_return(side_node_x, side_node_y, diamond_y_center, label_text):
    """循环回路:从侧路节点顶部回到菱形右上斜边

    关键铁律:
    - 多段直线 + stroke-linejoin="round"(不用 Q 弧线)
    - MidX = 740(主列 620 外,避让)
    - UpY 在侧路顶部上方 ~54px
    - 不进菱形顶点,落在菱形右上斜边内
    """
    side_x_center = side_node_x + SIDE_NODE_WIDTH_DEFAULT // 2  # 1010
    up_y = side_node_y - 54  # 侧路节点顶部上方
    mid_x = 740  # 主列(620) + 120,避让
    target_y = diamond_y_center - 34  # 落在菱形斜边上

    # 标签在水平回路上方
    label_rect_x = 790
    label_rect_y = up_y + 8
    label_rect_width = 170
    label_rect_height = 26
    label_text_x = label_rect_x + label_rect_width // 2
    label_text_y = label_rect_y + 17

    return f'''
  <!-- 循环回路(多段直线+转角圆角) -->
  <path d="M {side_x_center} {side_node_y}
           L {side_x_center} {up_y}
           L {mid_x} {up_y}
           L {mid_x} {target_y}"
        stroke="{COLOR_LINE_LOOP}" stroke-width="1.8" fill="none"
        stroke-linejoin="round"
        marker-end="url(#arrGrayDark)"/>
  <rect x="{label_rect_x}" y="{label_rect_y}" width="{label_rect_width}" height="{label_rect_height}" rx="13" ry="13" fill="{COLOR_BOTH}"/>
  <text x="{label_text_x}" y="{label_text_y}" text-anchor="middle" font-size="11" font-weight="600" fill="{COLOR_DARK}">{label_text}</text>
'''


def svg_escalation(side_node_x, side_node_y, escalation_data):
    """异常升级:从侧路节点底部向下,到异常节点"""
    side_x_center = side_node_x + SIDE_NODE_WIDTH_DEFAULT // 2
    arrow_from_y = side_node_y + NODE_HEIGHT  # 侧路节点底部
    # 异常节点位置
    ex_y = arrow_from_y + 52
    arrow_to_y = ex_y - 4

    # 异常升级标签(红底胶囊 116×24,在箭头中段)
    label_width = 116
    label_height = 24
    label_x = side_x_center - label_width // 2
    label_y = arrow_from_y + 8
    label_text_y = label_y + 16

    out = f'''
  <!-- 异常升级箭头 -->
  <line x1="{side_x_center}" y1="{arrow_from_y}" x2="{side_x_center}" y2="{arrow_to_y}" stroke="{COLOR_LINE_EXCEPTION}" stroke-width="1.8" marker-end="url(#arrRed)"/>
  <rect x="{label_x}" y="{label_y}" width="{label_width}" height="{label_height}" rx="12" ry="12" fill="{COLOR_EXCEPTION}"/>
  <text x="{side_x_center}" y="{label_text_y}" text-anchor="middle" font-size="11" font-weight="600" fill="#FFFFFF">{escalation_data['condition']}</text>
'''
    # 异常节点(合同解除)
    out += svg_side_node(
        side_node_x, ex_y, "exception",
        escalation_data['target_title'],
        escalation_data.get('target_sub1', ''),
        escalation_data.get('target_sub2', '')
    )
    return out


# ============================================================
# 布局计算 - 核心逻辑
# ============================================================

def calculate_layout(data):
    """计算所有节点的 y 坐标,返回 layout 列表

    每个 layout item:
    {
      "node": <原始节点数据>,
      "y": <y 坐标>(主节点和侧路用 y_top,菱形用 y_center)
    }
    """
    main_flow = data["main_flow"]
    layouts = []
    y = TITLE_AREA_HEIGHT

    for node in main_flow:
        t = node["type"]
        if t == "terminal_start":
            layouts.append({"node": node, "y": y, "bottom": y + TERMINAL_START_HEIGHT})
            y = y + TERMINAL_START_HEIGHT + NODE_GAP + 10
        elif t == "terminal_end":
            layouts.append({"node": node, "y": y, "bottom": y + TERMINAL_END_HEIGHT})
            y = y + TERMINAL_END_HEIGHT + NODE_GAP
        elif t == "decision":
            # 菱形:y 是中心点
            y_center = y + DIAMOND_HALF_HEIGHT
            layouts.append({"node": node, "y_center": y_center, "bottom": y_center + DIAMOND_HALF_HEIGHT})
            # 菱形下方有合格标签(22px)+箭头(~28px)
            y = y_center + DIAMOND_HALF_HEIGHT + 48
        else:
            # 主节点(甲方/乙方/双方)
            layouts.append({"node": node, "y": y, "bottom": y + NODE_HEIGHT})
            y = y + NODE_HEIGHT + NODE_GAP

    # 画布总高度(加底部 margin 100)
    canvas_height = y + 100
    return layouts, canvas_height


def find_main_index(layouts, node_type_or_title, index_hint=None):
    """找到某个 main_flow 节点在 layouts 里的位置"""
    # 用 index_hint(main_flow 的 index)精准查找
    if index_hint is not None and 0 <= index_hint < len(layouts):
        return index_hint
    # 否则按 type 模糊查找
    for i, item in enumerate(layouts):
        if item["node"]["type"] == node_type_or_title:
            return i
    return -1


# ============================================================
# 主流程箭头生成
# ============================================================

def build_main_arrows(layouts):
    """生成所有主流程节点之间的箭头"""
    out = ""
    for i in range(len(layouts) - 1):
        cur = layouts[i]
        nxt = layouts[i + 1]
        cur_node = cur["node"]
        nxt_node = nxt["node"]

        # 如果当前是菱形,下一个是主节点,用 branch_pass_arrow
        if cur_node["type"] == "decision":
            from_y = cur["y_center"] + DIAMOND_HALF_HEIGHT
            to_y = nxt["y"] - 4
            out += svg_branch_pass_arrow(from_y, to_y)
        else:
            from_y = cur["bottom"]
            to_y = nxt.get("y") or (nxt["y_center"] - DIAMOND_HALF_HEIGHT) - 4
            # 如果下一个是菱形
            if nxt_node["type"] == "decision":
                to_y = nxt["y_center"] - DIAMOND_HALF_HEIGHT - 4
            out += svg_main_arrow(from_y, to_y)
    return out


# ============================================================
# 主渲染函数
# ============================================================

def render_svg(data):
    layouts, canvas_height = calculate_layout(data)

    # 开头
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {canvas_height}" width="{CANVAS_WIDTH}" height="{canvas_height}" font-family="{FONT_FAMILY}">
'''
    svg += svg_defs().replace("{CANVAS_HEIGHT}", str(canvas_height))
    svg += svg_title(data["title"], data["subtitle"])
    svg += svg_legend()

    # 主流程节点
    for item in layouts:
        node = item["node"]
        t = node["type"]
        if t == "terminal_start":
            svg += svg_terminal_start(item["y"], node["title"],
                                       node.get("sub1", ""), node.get("sub2", ""))
        elif t == "terminal_end":
            svg += svg_terminal_end(item["y"], node["title"])
        elif t == "decision":
            svg += svg_diamond(item["y_center"], node["title"],
                               node.get("sub1", ""), node.get("sub2", ""))
        else:
            svg += svg_main_node(item["y"], t, node["title"],
                                 node.get("sub1", ""), node.get("sub2", ""))

    # 主流程箭头
    svg += build_main_arrows(layouts)

    # 侧路节点和回路
    side_nodes = data.get("side_nodes", [])
    for side in side_nodes:
        anchor_idx = side["anchor_index"]
        anchor_layout = layouts[anchor_idx]
        anchor_node = anchor_layout["node"]

        # 侧路节点 y = 菱形中心 y - NODE_HEIGHT/2
        if anchor_node["type"] == "decision":
            side_y = anchor_layout["y_center"] - NODE_HEIGHT // 2
            diamond_y = anchor_layout["y_center"]

            # 画不合格分支箭头
            svg += svg_branch_fail_arrow(diamond_y, SIDE_NODE_X)

            # 画侧路节点
            side_type = side["type"]
            svg += svg_side_node(SIDE_NODE_X, side_y, side_type,
                                  side["title"],
                                  side.get("sub1", ""),
                                  side.get("sub2", ""))

            # 画回路
            if "return_label" in side:
                svg += svg_loop_return(SIDE_NODE_X, side_y, diamond_y, side["return_label"])

            # 画异常升级(如果有)
            if "escalation" in side:
                svg += svg_escalation(SIDE_NODE_X, side_y, side["escalation"])

    svg += "\n</svg>\n"
    return svg


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="从 JSON 数据生成精美业务流程图 SVG(严格对标 02-flowchart-sample.svg)"
    )
    parser.add_argument("--data", required=True, help="输入 flowchart-data.json 路径")
    parser.add_argument("--output", required=True, help="输出 .svg 文件路径(必须是 .svg 扩展名)")
    args = parser.parse_args()

    # ========== 扩展名校验(防止 AI 传错扩展名导致生成损坏的 docx/pdf 等) ==========
    output = Path(args.output)
    output_ext = output.suffix.lower()
    if output_ext != ".svg":
        import sys
        print(
            f"\n❌ 错误:--output 扩展名必须是 .svg,当前收到的是 '{output_ext}'\n"
            f"\n  传入的完整路径: {args.output}\n"
            f"\n【说明】业务流程图是矢量图,不是 Word 文档。\n"
            f"       - 如果需要 SVG 文件:请用 xxx.svg 扩展名\n"
            f"       - 如果需要 PNG 图片:请改用 scripts/render-flowchart.py 并传 .png\n"
            f"       - 绝对不能传 .docx / .pdf / .doc 扩展名(这会生成无法打开的损坏文件)\n",
            file=sys.stderr
        )
        sys.exit(1)
    # ================================================================================

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    svg = render_svg(data)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"业务流程图 SVG 已生成(严格对标铁律):{output}")


if __name__ == "__main__":
    main()
