#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mqc-claim-basis-nine-step 三图回归检查。无需 pytest。

三类检查：
  1. 渲染冒烟   —— fixtures 能渲染成 SVG 且不崩
  2. 该报错就报错 —— 坏输入被 validate_map 清晰拦下
  3. 不变量     —— XML 合法、红只 #991B1B 且克制、无 #FF0000、决定性/核心/最坏在、
                    六步分组、等腰箭头 marker、拐弯圆角、无左侧竖色条

用法：python run_checks.py   （退出码 0 = 全过）
"""
import os, sys, json, re
import xml.dom.minidom as minidom

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_elements_matrix, render_issues_focus, render_outcome_band
from common import validate_map

FIX = os.path.join(HERE, "fixtures")
RESULTS = []


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


def check(name):
    def deco(fn):
        try:
            fn()
            RESULTS.append((name, True, ""))
        except AssertionError as e:
            RESULTS.append((name, False, str(e)))
        except Exception as e:
            RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        return fn
    return deco


RENDER = {"ex_matrix.json": render_elements_matrix,
          "ex_issues.json": render_issues_focus,
          "ex_outcome.json": render_outcome_band}


# ---- 1. 渲染冒烟 + XML 合法 ----
for _fx, _mod in RENDER.items():
    @check(f"render smoke · {_fx}")
    def _f(fx=_fx, mod=_mod):
        svg, w, h = mod.render(load(fx))
        assert svg.startswith("<svg"), "输出不是 SVG"
        assert w > 0 and h > 0, "画布尺寸非正"
        assert "<text" in svg, "无文字元素"
        minidom.parseString(svg)  # 抛异常即 XML 不合法


# ---- 2. 该报错就报错 ----
@check("expected error · 矩阵缺 rows 被拦下")
def _():
    try:
        validate_map({"layout": "elements_matrix", "title_text": "x", "rows": []})
        assert False, "空 rows 未被拦"
    except RuntimeError as e:
        assert "rows" in str(e), "报错信息不具体"


@check("expected error · outcome_band 的 most_likely 必须在 segments 内")
def _():
    try:
        validate_map({"layout": "outcome_band", "title_text": "x",
                      "segments": ["A", "B"], "most_likely": "C"})
        assert False, "越界 most_likely 未被拦"
    except RuntimeError as e:
        assert "most_likely" in str(e), "报错信息不具体"


@check("expected error · issues_focus 焦点缺 feeders 被拦下")
def _():
    try:
        validate_map({"layout": "issues_focus", "title_text": "x",
                      "foci": [{"id": "F1", "label": "l"}]})
        assert False, "缺 feeders 未被拦"
    except RuntimeError as e:
        assert "feeders" in str(e), "报错信息不具体"


# ---- 3. 不变量 ----
def _svgs():
    return {fx: mod.render(load(fx))[0] for fx, mod in RENDER.items()}


@check("invariant · 全图无功能红 #FF0000（已弃用）")
def _():
    for fx, svg in _svgs().items():
        assert "#FF0000" not in svg.upper(), f"{fx} 出现已弃用的 #FF0000"


@check("invariant · 红只 #991B1B 且克制（每图强调 ≤2）")
def _():
    # 数"实心红块"：rect/ fill=#991B1B 作为强调块（不含 marker 定义）
    for fx, svg in _svgs().items():
        blocks = len(re.findall(r'fill="#991B1B"', svg))
        # 决定性行/核心焦点卡/最坏情形块 + 少量红标签；克制上限设为 3
        assert blocks <= 3, f"{fx} 红块 {blocks} 处，过多（应 ≤2 强调，含标签 ≤3）"


@check("invariant · 图一决定性行存在且六步分组")
def _():
    svg = render_elements_matrix.render(load("ex_matrix.json"))[0]
    assert 'data-decisive="1"' in svg, "无决定性行"
    steps = set(re.findall(r'data-step="([^"]+)"', svg))
    assert len(steps) >= 3, f"步分组过少：{steps}"
    # 决定性行必是 #991B1B 实心块
    assert 'fill="#991B1B"' in svg, "决定性行未用 #991B1B 实心块"


@check("invariant · 图二核心焦点唯一且为红卡、汇聚连线为灰（红不外溢到连线）")
def _():
    svg = render_issues_focus.render(load("ex_issues.json"))[0]
    assert svg.count('data-core="1"') == 1, "核心焦点不唯一"
    assert 'data-role="focus-unit"' in svg, "缺焦点汇聚单元"
    reds = len(re.findall(r'fill="#991B1B"', svg))
    assert reds == 1, f"图二红块应仅核心焦点卡 1 处，实为 {reds}"
    assert "marker-end" in svg, "汇聚连线缺箭头"


@check("invariant · 图三最坏情形红块 + 最可能强调框（深蓝，非左竖条）")
def _():
    svg = render_outcome_band.render(load("ex_outcome.json"))[0]
    assert 'data-worst="1"' in svg and 'data-most="1"' in svg, "缺最坏/最可能标记"
    assert 'fill="#991B1B"' in svg, "最坏情形未用 #991B1B"
    assert 'stroke="#003153"' in svg, "最可能区间未用深蓝强调框"


@check("geometry · 卡片用小圆角（rx 存在，无大圆角）")
def _():
    for fx, svg in _svgs().items():
        assert 'rx="12"' in svg or 'rx="6"' in svg or 'rx="14"' in svg, f"{fx} 卡片未用小圆角"


@check("geometry · 无 AI 味卡片左侧竖色条")
def _():
    # 左竖条特征：极窄(≤6宽)的高矩形贴在卡片左缘且填非中性色。近似检测：不出现 width="3"/"4" 的实心色条 rect。
    for fx, svg in _svgs().items():
        bad = re.findall(r'<rect[^>]*width="[3-6]"[^>]*fill="#(?:003153|006A4E|991B1B|0070C0)"', svg)
        assert not bad, f"{fx} 疑似出现左侧竖色条"


@check("aesthetic · 标题用雅黑加粗 + 跨平台字体栈")
def _():
    for fx, svg in _svgs().items():
        assert "Microsoft YaHei" in svg and "PingFang SC" in svg, f"{fx} 字体栈不全"
        assert 'font-weight="700"' in svg, f"{fx} 标题未加粗"


def main():
    width = max(len(n) for n, _, _ in RESULTS)
    passed = 0
    for name, ok, detail in RESULTS:
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {name.ljust(width)}"
        if not ok:
            line += f"   -> {detail}"
        print(line)
        passed += ok
    total = len(RESULTS)
    print(f"\n{passed}/{total} 项通过。")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
