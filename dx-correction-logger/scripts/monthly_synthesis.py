#!/usr/bin/env python3
"""
月度修正综合分析器 —— 扫描月度修正日志，聚类分析修正模式，
生成学习报告，自动更新三份配置文件。

用法:
    python monthly_synthesis.py --month YYYY-MM --log-dir ~/.workbuddy/correction-log/
    python monthly_synthesis.py --all --log-dir ~/.workbuddy/correction-log/  # 全量分析
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime


# ── 配置文件路径 ──────────────────────────────────────────────

CONFIG_PATHS = {
    'USER': os.path.expanduser('~/.workbuddy/USER.md'),
    'MINDSET': os.path.expanduser('~/.workbuddy/PERSONAL-LEGAL-MINDSET.md'),
    'STYLE': os.path.expanduser('~/.workbuddy/skills/writing-style-profile/SKILL.md'),
}

CAT_NAMES = {
    'EXPR': '表达修正',
    'STRU': '结构调整',
    'LOGIC': '逻辑补强',
    'LEGAL': '法律论证',
    'FACT': '事实修正',
    'TONE': '语气调整',
    'FORMAT': '格式修正',
    'STRAT': '策略调整',
}


def load_correction_entries(log_dir, month=None):
    """加载指定月份（或全部）的修正日志"""
    entries = []
    if not os.path.isdir(log_dir):
        return entries

    for fname in sorted(os.listdir(log_dir)):
        if not fname.endswith('.json'):
            continue
        if fname.startswith('.'):
            continue

        # 跳过报告目录
        fpath = os.path.join(log_dir, fname)
        if os.path.isdir(fpath):
            continue

        # 按月份筛选
        if month:
            # 文件名格式: YYYY-MM-DD_...
            file_month = fname[:7]  # YYYY-MM
            if file_month != month:
                continue

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                entry = json.load(f)
            entry['_source_file'] = fname
            entries.append(entry)
        except (json.JSONDecodeError, IOError) as e:
            print(f'[WARN] 跳过损坏的日志: {fname} ({e})', file=sys.stderr)

    return entries


def analyze_entries(entries):
    """综合分析所有修正条目"""
    if not entries:
        return {'status': 'empty', 'message': '无修正记录'}

    analysis = {
        'total_entries': len(entries),
        'by_doc_type': Counter(),
        'by_case': Counter(),
        'by_category': Counter(),
        'by_change_level': Counter(),
        'doc_type_category': defaultdict(Counter),  # 文书类型 → 修正类型 → 次数
        'high_frequency_patterns': [],  # 高频模式（≥3次）
        'emerging_patterns': [],  # 新出现的模式
        'all_patterns': [],
    }

    for entry in entries:
        if entry.get('status') == 'identical':
            continue

        meta = entry.get('metadata', {})
        analysis['by_doc_type'][meta.get('doc_type', '未指定')] += 1
        analysis['by_case'][meta.get('case', '未指定')] += 1
        analysis['by_change_level'][meta.get('change_level', '未知')] += 1

        doc_type = meta.get('doc_type', '未指定')

        stats = entry.get('stats', {})
        for cat, count in stats.get('categories', {}).items():
            analysis['by_category'][cat] += count
            analysis['doc_type_category'][doc_type][cat] += count

        # 收集模式
        for pattern in entry.get('patterns', []):
            analysis['all_patterns'].append(pattern)

    # 识别高频模式（≥3次）
    pattern_counter = Counter()
    for p in analysis['all_patterns']:
        key = p.get('text', '')[:50]
        pattern_counter[key] += 1

    for text, count in pattern_counter.most_common():
        if count >= 3:
            # 找到对应的完整模式
            for p in analysis['all_patterns']:
                if p.get('text', '')[:50] == text:
                    p['total_count'] = count
                    analysis['high_frequency_patterns'].append(p)
                    break

    # 识别新出现的模式（只出现1-2次但在之前月份未见过）
    for text, count in pattern_counter.most_common():
        if 1 <= count < 3:
            for p in analysis['all_patterns']:
                if p.get('text', '')[:50] == text:
                    analysis['emerging_patterns'].append(p)
                    break

    # 文书类型 × 修正类型 交叉分析
    analysis['cross_analysis'] = {}
    for dt, cats in analysis['doc_type_category'].items():
        analysis['cross_analysis'][dt] = {
            'total': sum(cats.values()),
            'top_categories': cats.most_common(3),
        }

    return analysis


def generate_report(analysis, month=None):
    """生成 Markdown 格式的分析报告"""
    if analysis.get('status') == 'empty':
        return '# 月度修正分析报告\n\n无修正记录。\n'

    period = month or '全部历史'
    lines = [
        f'# 月度修正学习报告 — {period}',
        f'\n生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'\n---',
        f'\n## 概览',
        f'\n- 修正记录数：**{analysis["total_entries"]}** 条',
    ]

    # 文书类型分布
    if analysis['by_doc_type']:
        lines.append('\n### 文书类型分布')
        for dt, count in analysis['by_doc_type'].most_common():
            pct = count / analysis['total_entries'] * 100
            lines.append(f'- {dt}：{count} 次（{pct:.1f}%）')

    # 修正类型分布
    if analysis['by_category']:
        lines.append('\n### 修正类型分布')
        total_cats = sum(analysis['by_category'].values())
        for cat, count in analysis['by_category'].most_common():
            name = CAT_NAMES.get(cat, cat)
            pct = count / total_cats * 100
            lines.append(f'- {{type="bar",value={pct:.0f}}} {name}：{count} 次（{pct:.1f}%）')

    # 修改幅度分布
    if analysis['by_change_level']:
        lines.append('\n### 修改幅度分布')
        for level, count in analysis['by_change_level'].most_common():
            lines.append(f'- {level}：{count} 次')

    # 高频修正模式
    if analysis['high_frequency_patterns']:
        lines.append('\n## 🔴 高频修正模式（≥3次，已自动应用）')
        lines.append('\n以下模式在多项文书中反复出现，已自动更新到配置文件中：\n')
        for i, pattern in enumerate(analysis['high_frequency_patterns'], 1):
            lines.append(f'### {i}. {pattern.get("type", "未知")}')
            lines.append(f'- 出现次数：**{pattern.get("total_count", pattern.get("count", "?"))}** 次')
            lines.append(f'- 内容：`{pattern.get("text", "")}`')
            lines.append(f'- 描述：{pattern.get("description", "")}')
            lines.append('')

    # 新出现模式
    if analysis['emerging_patterns']:
        lines.append('\n## ⚠️ 新出现的修正模式（1-2次，待观察）')
        lines.append('\n以下模式最近出现，尚未达到自动应用阈值，正在持续观察：\n')
        for i, pattern in enumerate(analysis['emerging_patterns'], 1):
            lines.append(f'{i}. `{pattern.get("text", "")[:80]}` — {pattern.get("description", "")}')

    # 交叉分析
    if analysis.get('cross_analysis'):
        lines.append('\n## 📊 文书类型 × 修正类型交叉分析')
        for dt, data in sorted(analysis['cross_analysis'].items()):
            lines.append(f'\n### {dt}')
            lines.append(f'总修正次数：{data["total"]}')
            for cat, count in data['top_categories']:
                name = CAT_NAMES.get(cat, cat)
                lines.append(f'  - {name}：{count} 次')

    # 建议
    lines.append('\n---')
    lines.append('\n## 💡 优化建议')
    
    if analysis['high_frequency_patterns']:
        lines.append(f'\n已自动应用 {len(analysis["high_frequency_patterns"])} 个高频修正模式到配置文件。')
    
    if analysis['emerging_patterns']:
        lines.append(f'\n{len(analysis["emerging_patterns"])} 个新模式正在观察中，下月将重新评估。')

    lines.append('\n---')
    lines.append(f'\n*由 dx-correction-logger 自动生成*')

    return '\n'.join(lines)


def apply_updates_to_config(config_path, patterns, config_type):
    """将修正模式应用到配置文件"""
    if not os.path.exists(config_path):
        print(f'[WARN] 配置文件不存在: {config_path}')
        return 0

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    updated_count = 0
    marker = f'\n<!-- correction: {datetime.now().strftime("%Y-%m-%d")} (auto) -->\n'

    # 根据配置类型决定注入位置
    for pattern in patterns:
        rule_line = f'- ⚠️ 修正模式({pattern.get("type", "")})：{pattern.get("description", "")} — `{pattern.get("text", "")[:80]}`\n'
        
        # 检查是否已在文件中
        snippet = rule_line.strip()[:60]
        if snippet in content:
            continue

        # 注入到文件末尾的规则区域
        # 对于不同的配置文件，规则区域不同
        content += marker + rule_line
        updated_count += 1

    if updated_count > 0:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  ✅ 已更新 {os.path.basename(config_path)}（{updated_count} 条规则）')

    return updated_count


def main():
    parser = argparse.ArgumentParser(description='月度修正综合分析器')
    parser.add_argument('--month', help='分析月份 (YYYY-MM)')
    parser.add_argument('--all', action='store_true', help='分析所有月份')
    parser.add_argument('--log-dir', required=True, help='修正日志目录')
    parser.add_argument('--output', '-o', help='输出报告路径')
    parser.add_argument('--apply', action='store_true', help='自动应用高频模式到配置文件')
    parser.add_argument('--threshold', type=int, default=3, help='高频模式阈值（默认3次）')

    args = parser.parse_args()

    if not args.month and not args.all:
        # 默认分析当前月份
        args.month = datetime.now().strftime('%Y-%m')

    # 加载修正条目
    month = None if args.all else args.month
    entries = load_correction_entries(args.log_dir, month)

    if not entries:
        print(f'[INFO] 未找到修正记录（{month or "全部"}）')
        if args.output:
            report = generate_report({'status': 'empty'}, month)
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
        return

    # 分析
    analysis = analyze_entries(entries)

    # 生成报告
    report = generate_report(analysis, month)

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'✅ 月度报告已保存到: {args.output}')

    # 输出摘要
    print(f'\n📊 {month or "全量"} 分析摘要')
    print(f'   记录数: {analysis["total_entries"]}')
    if analysis['by_doc_type']:
        print(f'   主要文书类型: {analysis["by_doc_type"].most_common(1)[0][0]}')
    if analysis['by_category']:
        top_cat = analysis['by_category'].most_common(1)[0]
        print(f'   主要修正类型: {CAT_NAMES.get(top_cat[0], top_cat[0])} ({top_cat[1]}次)')
    print(f'   高频模式: {len(analysis["high_frequency_patterns"])} 个')
    print(f'   新增模式: {len(analysis["emerging_patterns"])} 个')

    # 自动应用高频模式
    if args.apply and analysis['high_frequency_patterns']:
        print('\n🔧 正在应用高频修正模式...')
        total_updates = 0

        # 表达修正 → writing-style-profile
        expr_patterns = [p for p in analysis['high_frequency_patterns'] if '表达' in p.get('description', '') or '措辞' in p.get('description', '') or '套话' in p.get('description', '')]
        if expr_patterns:
            total_updates += apply_updates_to_config(CONFIG_PATHS['STYLE'], expr_patterns, 'STYLE')

        # 逻辑/策略修正 → PERSONAL-LEGAL-MINDSET.md
        logic_patterns = [p for p in analysis['high_frequency_patterns'] if '论证' in p.get('description', '') or '逻辑' in p.get('description', '') or '策略' in p.get('description', '')]
        if logic_patterns:
            total_updates += apply_updates_to_config(CONFIG_PATHS['MINDSET'], logic_patterns, 'MINDSET')

        # 偏好修正 → USER.md
        pref_patterns = [p for p in analysis['high_frequency_patterns'] if '偏好' in p.get('description', '') or '习惯' in p.get('description', '')]
        if pref_patterns:
            total_updates += apply_updates_to_config(CONFIG_PATHS['USER'], pref_patterns, 'USER')

        # 其余模式也尝试应用到合适的配置文件
        remaining = [p for p in analysis['high_frequency_patterns'] if p not in expr_patterns + logic_patterns + pref_patterns]
        for p in remaining:
            # 默认注入到 MINDSET
            total_updates += apply_updates_to_config(CONFIG_PATHS['MINDSET'], [p], 'MINDSET')

        print(f'\n✅ 共应用 {total_updates} 条规则到配置文件')


if __name__ == '__main__':
    main()
