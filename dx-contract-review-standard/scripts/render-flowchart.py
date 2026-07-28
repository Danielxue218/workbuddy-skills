#!/usr/bin/env python3
"""
render-flowchart.py · v1.0.0

业务流程图双方案架构:
- 方案 A(SVG 精美版 · 默认):AI 生成的完整 SVG 源码,脚本直接输出 .svg 文件
- 方案 B(Mermaid 自动版 · 降级):Mermaid 源码,脚本通过 mmdc 渲染为 PNG

核心特性:
- 自动检测输入文件类型(.svg → 直通;.mmd → Mermaid 渲染)
- Mermaid 主题色板:与方案 A 对齐(#003153 终端 · #0070C0 甲方 · #006A4E 乙方)
- 7 类 classDef(default/partyA/partyB/bothParties/decision/exception/terminal)

用法:
    # 方案 A · SVG 精美版(推荐)
    python3 scripts/render-flowchart.py \\
        --input "<输出目录>/业务流程图.svg" \\
        --output "<输出目录>/业务流程图.svg"

    # 方案 B · Mermaid 降级
    python3 scripts/render-flowchart.py \\
        --input "<输出目录>/业务流程图.mmd" \\
        --output "<输出目录>/业务流程图.png" \\
        --inject-theme

如输入是 .mmd 且环境未安装 mmdc,会仅保存 .mmd 并提示使用在线渲染。

作者:缪奇川(Miao Qichuan)
"""

import subprocess
import sys
import argparse
import shutil
from pathlib import Path


# ============================================================
# 标准主题配置(中性底色,节点色由 classDef 控制)
# ============================================================

STANDARD_THEME_BLOCK = """%%{init: {
  'theme': 'base',
  'themeVariables': {
    'fontFamily': '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", "Helvetica Neue", Arial, sans-serif',
    'fontSize': '14px',
    'primaryColor': '#F8FAFC',
    'primaryTextColor': '#000000',
    'primaryBorderColor': '#475569',
    'lineColor': '#64748B',
    'tertiaryColor': '#FFFFFF',
    'background': '#FFFFFF',
    'mainBkg': '#F8FAFC',
    'secondBkg': '#FFFFFF'
  },
  'flowchart': {
    'nodeSpacing': 50,
    'rankSpacing': 60,
    'curve': 'basis',
    'htmlLabels': true
  }
}}%%
"""

# 色板:与方案 A(generate-flowchart.py)对齐
# - partyA  甲方节点:浅蓝填充 #D6EBF5 + 甲方蓝 #0070C0 边框
# - partyB  乙方节点:浅绿填充 #D4EDDA(与甲方区分)
# - bothParties 双方共同:浅黄 #FEF3C7
# - decision 判断菱形:纯白 + 深灰边
# - exception 异常:浅红 #FFE4E6
# - terminal 起点/终点:主色填充 + 白字
# v2.0.0:色板与方案 A(generate-flowchart.py)及 02-flowchart-sample.svg 完全对齐
# 终端 #003153 · 甲方 #0070C0 · 乙方 #006A4E · 双方 #F6C12C · 判断 #F5F0E1 · 异常 #C92C2C
STANDARD_CLASSDEF_BLOCK = """
classDef default fill:#F8FAFC,stroke:#475569,stroke-width:1.5px,color:#000000
classDef partyA fill:#D6EBF5,stroke:#0070C0,stroke-width:1.5px,color:#0C3E5E
classDef partyB fill:#D4EDDA,stroke:#006A4E,stroke-width:1.5px,color:#0F3A1A
classDef bothParties fill:#FEF3C7,stroke:#F6C12C,stroke-width:1.5px,color:#78350F
classDef decision fill:#F5F0E1,stroke:#334155,stroke-width:2px,color:#000000
classDef exception fill:#FFE4E6,stroke:#C92C2C,stroke-width:1.5px,color:#881337
classDef terminal fill:#003153,stroke:#003153,stroke-width:1.5px,color:#FFFFFF
"""


def check_mmdc():
    return shutil.which("mmdc") is not None


def inject_theme_and_classdef(mermaid_source):
    """向 Mermaid 源码注入标准主题配置和 classDef。"""
    lines = mermaid_source.strip().split("\n")

    has_init = any("%%{init" in ln for ln in lines)
    has_classdef_default = any("classDef default" in ln for ln in lines)

    graph_line_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("graph ") or stripped.startswith("flowchart "):
            graph_line_idx = i
            break

    if graph_line_idx is None:
        return mermaid_source

    result = []

    if not has_init:
        result.append(STANDARD_THEME_BLOCK.strip())

    for i in range(graph_line_idx + 1):
        result.append(lines[i])

    if not has_classdef_default:
        result.append(STANDARD_CLASSDEF_BLOCK.strip())

    for i in range(graph_line_idx + 1, len(lines)):
        result.append(lines[i])

    return "\n".join(result) + "\n"


def render_mermaid(input_path, output_path, inject_theme=False,
                   width=1600, height=1200, scale=2):
    """渲染 Mermaid 源码为 PNG。"""
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"错误:输入文件不存在:{input_file}")
        return False

    output_file.parent.mkdir(parents=True, exist_ok=True)

    render_source_path = input_file
    if inject_theme:
        original_source = input_file.read_text(encoding="utf-8")
        injected_source = inject_theme_and_classdef(original_source)
        input_file.write_text(injected_source, encoding="utf-8")
        print(f"已注入标准主题和 classDef:{input_file}")

    if not check_mmdc():
        print("提示:mmdc (Mermaid CLI) 未安装。")
        print(f"Mermaid 源码已保存:{input_file}")
        print("你可以:")
        print("  1. 安装 mmdc:npm install -g @mermaid-js/mermaid-cli")
        print(f"  2. 将 {input_file} 的内容粘贴到 https://mermaid.live 在线渲染")
        return False

    try:
        # root 环境自动添加 --no-sandbox(避免 Chrome 拒绝 root 运行)
        import os
        puppeteer_config = None
        if os.geteuid() == 0:
            import tempfile
            import json
            pc = {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
            tf = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            )
            json.dump(pc, tf)
            tf.close()
            puppeteer_config = tf.name

        cmd = [
            "mmdc",
            "-i", str(render_source_path),
            "-o", str(output_file),
            "-b", "white",
            "-w", str(width),
            "-H", str(height),
            "-s", str(scale),
        ]
        if puppeteer_config:
            cmd.extend(["-p", puppeteer_config])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"流程图已渲染({width}x{height}, scale={scale}):{output_file}")
            return True
        else:
            print(f"渲染失败:{result.stderr}")
            print(f"Mermaid 源码已保存:{input_file}")
            print("请将内容粘贴到 https://mermaid.live 在线渲染")
            return False

    except subprocess.TimeoutExpired:
        print("渲染超时(60 秒)")
        print(f"Mermaid 源码已保存:{input_file}")
        return False
    except Exception as e:
        print(f"渲染出错:{e}")
        print(f"Mermaid 源码已保存:{input_file}")
        return False


def save_mermaid_source(mermaid_code, output_path, inject_theme=True):
    """将 Mermaid 源码保存为 .mmd 文件"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if inject_theme:
        mermaid_code = inject_theme_and_classdef(mermaid_code)

    output.write_text(mermaid_code, encoding="utf-8")
    print(f"Mermaid 源码已保存:{output}")


def copy_svg_passthrough(input_path, output_path):
    """SVG 直通:输入是 AI 生成的完整 SVG 源码,直接复制到输出目录。

    这是方案 A(SVG 精美版)的核心机制。脚本不做任何视觉修改,
    只负责文件复制和路径管理。

    参数:
        input_path: 输入 .svg 文件
        output_path: 输出 .svg 文件

    返回:
        True 成功 / False 失败
    """
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"错误:输入 SVG 文件不存在:{input_file}")
        return False

    # 简单校验是否为 SVG
    try:
        content = input_file.read_text(encoding="utf-8")
        if "<svg" not in content[:500]:
            print(f"警告:输入文件看起来不是 SVG:{input_file}")
            return False
    except Exception as e:
        print(f"读取 SVG 失败:{e}")
        return False

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 强制输出扩展名为 .svg
    if output_file.suffix.lower() != ".svg":
        output_file = output_file.with_suffix(".svg")
        print(f"调整输出扩展名为 .svg:{output_file}")

    shutil.copy2(str(input_file), str(output_file))
    print(f"SVG 流程图已输出(方案 A · 精美版):{output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="渲染业务流程图(双方案:SVG 精美版 / Mermaid 自动版)"
    )
    parser.add_argument("--input", required=True,
                        help="输入文件路径(.svg 或 .mmd,自动识别方案)")
    parser.add_argument("--output", required=True,
                        help="输出文件路径(.svg / .png)")
    parser.add_argument("--inject-theme", action="store_true",
                        help="(仅 Mermaid)自动注入标准主题配置和 classDef")
    parser.add_argument("--width", type=int, default=1600,
                        help="(仅 Mermaid)图片宽度 px")
    parser.add_argument("--height", type=int, default=1200,
                        help="(仅 Mermaid)图片高度 px")
    parser.add_argument("--scale", type=int, default=2,
                        help="(仅 Mermaid)HiDPI 缩放因子")

    args = parser.parse_args()

    # ========== 输出扩展名校验(防止 AI 传错扩展名导致损坏文件) ==========
    output_ext = Path(args.output).suffix.lower()
    if output_ext not in (".svg", ".png", ".mmd"):
        print(
            f"\n❌ 错误:--output 扩展名必须是 .svg / .png / .mmd,当前收到的是 '{output_ext}'\n"
            f"\n  传入的完整路径: {args.output}\n"
            f"\n【说明】业务流程图是矢量图/图像,不是 Word 文档。\n"
            f"       - SVG 方案(默认):传 .svg 扩展名\n"
            f"       - Mermaid 渲染:传 .png 扩展名\n"
            f"       - 保存 Mermaid 源码:传 .mmd 扩展名\n"
            f"       - 绝对不能传 .docx / .pdf / .doc 扩展名(这会生成无法打开的损坏文件)\n",
            file=sys.stderr
        )
        sys.exit(1)
    # ================================================================================

    # 根据输入文件扩展名自动选择方案
    input_ext = Path(args.input).suffix.lower()
    if input_ext == ".svg":
        # 方案 A · SVG 直通
        copy_svg_passthrough(args.input, args.output)
    elif input_ext == ".mmd":
        # 方案 B · Mermaid 渲染
        render_mermaid(
            args.input,
            args.output,
            inject_theme=args.inject_theme,
            width=args.width,
            height=args.height,
            scale=args.scale,
        )
    else:
        print(f"错误:不支持的输入文件类型 {input_ext}")
        print("支持的格式:.svg(方案 A · 精美版) / .mmd(方案 B · 自动版)")
        sys.exit(1)


if __name__ == "__main__":
    main()
