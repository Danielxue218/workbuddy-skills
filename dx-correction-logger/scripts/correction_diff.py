#!/usr/bin/env python3
"""
修正差异分析器 —— 对比 AI 生成版本与人工修改版本，
输出结构化差异报告，自动分类修改类型。

用法:
    python correction_diff.py <before_file> <after_file> --output <json_output>
    python correction_diff.py <before_file> <after_file> --output <json_output> --case "赵晓薇继承"

可选参数:
    --case      案件简称
    --doc-type  文书类型（起诉状/答辩状/代理词/法律意见书/证据目录/质证意见/法律备忘录/开庭准备/其他）
    --author    修改人（默认从 USER.md 读取）
"""

import argparse
import difflib
import json
import os
import re
import sys
from datetime import datetime


# ── 修正分类规则 ──────────────────────────────────────────────

TONE_ADJUSTMENTS = [
    (r'显然', '低置信度表述'),
    (r'毫无疑问', '低置信度表述'),
    (r'理应', '低置信度表述'),
    (r'必然', '低置信度表述'),
    (r'明显', '低置信度表述'),
    (r'毫无疑问地', '低置信度表述'),
    (r'众所周知', '低置信度表述'),
]

EXPR_DELETIONS = [
    r'综上所述[,，]',
    r'总之[,，]',
    r'值得注意的是[,，]',
    r'需要指出的是[,，]',
    r'不容忽视的是[,，]',
    r'显而易见[,，]',
]

EXPR_ADDITIONS = [
    r'穿透式',
    r'实质重于形式',
    r'证据闭环',
    r'内心确信',
]

STRUCT_PATTERNS = [
    (r'^[一二三四五六七八九十]、', '一级标题'),
    (r'^（[一二三四五六七八九十]）', '二级标题'),
    (r'^\d+[\.、]', '数字编号'),
]

LEGAL_PATTERNS = [
    r'《[^》]+》第\d+条',
    r'民法典第\d+条',
    r'公司法第\d+条',
    r'最高人民法院',
    r'指导案例.*第\d+号',
    r'公报案例',
]


def classify_line_change(old_line, new_line):
    """对单行修改进行分类"""
    categories = []

    # 检查是否是单纯删除
    if old_line and not new_line.strip():
        for pattern, label in EXPR_DELETIONS:
            if re.search(pattern, old_line):
                categories.append(('EXPR', f'删除套话: {label}'))
                break
        else:
            categories.append(('EXPR', '删除内容'))
        return categories

    # 检查是否是单纯新增
    if not old_line.strip() and new_line:
        for pattern in EXPR_ADDITIONS:
            if re.search(pattern, new_line):
                categories.append(('EXPR', f'增加专业表达: {pattern}'))
                break
        for pattern in LEGAL_PATTERNS:
            if re.search(pattern, new_line):
                categories.append(('LEGAL', f'补充法律依据: {pattern}'))
                break
        else:
            categories.append(('LOGIC', '补充论证内容'))
        return categories

    # 检查语气调整
    for pattern, label in TONE_ADJUSTMENTS:
        if re.search(pattern, old_line) and not re.search(pattern, new_line):
            categories.append(('TONE', f'降低语气强度: {label}'))
            break

    # 检查法律论证变更
    old_legal = any(re.search(p, old_line) for p in LEGAL_PATTERNS)
    new_legal = any(re.search(p, new_line) for p in LEGAL_PATTERNS)
    if old_legal or new_legal:
        categories.append(('LEGAL', '法律论证调整'))

    # 检查结构变更
    for pattern, label in STRUCT_PATTERNS:
        old_has = bool(re.search(pattern, old_line))
        new_has = bool(re.search(pattern, new_line))
        if old_has != new_has:
            categories.append(('STRU', f'结构调整: {label}'))

    # 检查措辞替换
    if not categories:
        old_words = set(old_line.split())
        new_words = set(new_line.split())
        if old_words != new_words:
            categories.append(('EXPR', '措辞替换'))

    # 默认
    if not categories:
        categories.append(('EXPR', '行内容修改'))

    return categories


def classify_block_change(old_block, new_block):
    """对段落级修改进行整体分类"""
    categories = set()

    if len(old_block) > len(new_block) * 2:
        categories.add(('EXPR', '大幅精简'))

    if len(new_block) > len(old_block) * 2:
        categories.add(('LOGIC', '大幅扩充论证'))

    for old_line in old_block:
        for pattern, _ in TONE_ADJUSTMENTS:
            if re.search(pattern, old_line):
                categories.add(('TONE', '语气调整'))

    for new_line in new_block:
        for pattern in LEGAL_PATTERNS:
            if re.search(pattern, new_line):
                categories.add(('LEGAL', '补充法律依据'))

    return list(categories) if categories else [('EXPR', '内容修改')]


def compute_diff(before_text, after_text):
    """计算两个文本的结构化差异"""
    before_lines = before_text.splitlines(keepends=False)
    after_lines = after_text.splitlines(keepends=False)

    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
    opcodes = matcher.get_opcodes()

    changes = []
    stats = {
        'equal_lines': 0,
        'deleted_lines': 0,
        'inserted_lines': 0,
        'replaced_lines': 0,
        'total_before_lines': len(before_lines),
        'total_after_lines': len(after_lines),
        'categories': {},
    }

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            stats['equal_lines'] += (i2 - i1)
            continue

        old_block = before_lines[i1:i2]
        new_block = after_lines[j1:j2]

        change_entry = {
            'type': tag,  # 'delete', 'insert', 'replace'
            'before_lines': (i1, i2),
            'after_lines': (j1, j2),
            'before_text': '\n'.join(old_block),
            'after_text': '\n'.join(new_block),
        }

        if tag == 'delete':
            stats['deleted_lines'] += len(old_block)
            # 逐行分类
            line_categories = []
            for line in old_block:
                cats = classify_line_change(line, '')
                line_categories.extend(cats)
            # 取最高频类别
            if line_categories:
                from collections import Counter
                cat_counter = Counter(c[0] for c in line_categories)
                top_cat = cat_counter.most_common(1)[0][0]
                change_entry['category'] = top_cat
                change_entry['category_detail'] = line_categories[0][1]
        elif tag == 'insert':
            stats['inserted_lines'] += len(new_block)
            line_categories = []
            for line in new_block:
                cats = classify_line_change('', line)
                line_categories.extend(cats)
            if line_categories:
                from collections import Counter
                cat_counter = Counter(c[0] for c in line_categories)
                top_cat = cat_counter.most_common(1)[0][0]
                change_entry['category'] = top_cat
                change_entry['category_detail'] = line_categories[0][1]
        else:  # replace
            stats['replaced_lines'] += max(len(old_block), len(new_block))
            categories = classify_block_change(old_block, new_block)
            change_entry['category'] = categories[0][0]
            change_entry['category_detail'] = categories[0][1]

        # 统计分类
        cat = change_entry.get('category', 'UNKNOWN')
        stats['categories'][cat] = stats['categories'].get(cat, 0) + 1

        changes.append(change_entry)

    return changes, stats


def compute_high_confidence_patterns(changes):
    """提取高置信度修正模式"""
    patterns = []

    # 模式1: 重复出现的删除
    deleted_lines = []
    for c in changes:
        if c['type'] == 'delete':
            deleted_lines.append(c['before_text'])
    
    if deleted_lines:
        from collections import Counter
        common_deletions = Counter(deleted_lines).most_common(5)
        for text, count in common_deletions:
            if count >= 2 and len(text) > 10:
                patterns.append({
                    'type': 'DELETION',
                    'text': text[:100] + ('...' if len(text) > 100 else ''),
                    'count': count,
                    'description': f'重复删除的文本（出现{count}次）'
                })

    # 模式2: 重复出现的新增
    inserted_lines = []
    for c in changes:
        if c['type'] == 'insert':
            inserted_lines.append(c['after_text'])
    
    if inserted_lines:
        from collections import Counter
        common_insertions = Counter(inserted_lines).most_common(5)
        for text, count in common_insertions:
            if count >= 2 and len(text) > 10:
                patterns.append({
                    'type': 'INSERTION',
                    'text': text[:100] + ('...' if len(text) > 100 else ''),
                    'count': count,
                    'description': f'重复新增的文本（出现{count}次）'
                })

    return patterns


def main():
    parser = argparse.ArgumentParser(description='修正差异分析器')
    parser.add_argument('before_file', help='修改前文件路径（AI 生成版本）')
    parser.add_argument('after_file', help='修改后文件路径（人工修改版本）')
    parser.add_argument('--output', '-o', required=True, help='输出 JSON 文件路径')
    parser.add_argument('--case', help='案件简称')
    parser.add_argument('--doc-type', help='文书类型')
    parser.add_argument('--author', default='DX', help='修改人')

    args = parser.parse_args()

    # 读取文件
    for fpath in [args.before_file, args.after_file]:
        if not os.path.exists(fpath):
            print(f'[ERROR] 文件不存在: {fpath}', file=sys.stderr)
            sys.exit(1)

    with open(args.before_file, 'r', encoding='utf-8') as f:
        before_text = f.read()

    with open(args.after_file, 'r', encoding='utf-8') as f:
        after_text = f.read()

    if before_text == after_text:
        print('[INFO] 两个文件内容完全相同，无修正需要记录。')
        result = {
            'status': 'identical',
            'message': '两个文件内容完全相同',
        }
    else:
        changes, stats = compute_diff(before_text, after_text)
        patterns = compute_high_confidence_patterns(changes)

        similarity = difflib.SequenceMatcher(None, before_text, after_text).ratio()

        result = {
            'status': 'analyzed',
            'metadata': {
                'case': args.case or '未指定',
                'doc_type': args.doc_type or '未指定',
                'author': args.author,
                'analysis_date': datetime.now().isoformat(),
                'before_file': os.path.basename(args.before_file),
                'after_file': os.path.basename(args.after_file),
                'similarity_ratio': round(similarity, 4),
                'change_level': (
                    '全文重写' if similarity < 0.3 else
                    '大幅修改' if similarity < 0.6 else
                    '段落级修改' if similarity < 0.85 else
                    '措辞微调'
                ),
            },
            'stats': stats,
            'changes': changes,
            'patterns': patterns,
            'summary': {
                'total_changes': len(changes),
                'category_distribution': stats['categories'],
                'change_level': (
                    '全文重写' if similarity < 0.3 else
                    '大幅修改' if similarity < 0.6 else
                    '段落级修改' if similarity < 0.85 else
                    '措辞微调'
                ),
            },
        }

        # 生成人类可读摘要
        cat_names = {
            'EXPR': '表达修正',
            'STRU': '结构调整',
            'LOGIC': '逻辑补强',
            'LEGAL': '法律论证',
            'FACT': '事实修正',
            'TONE': '语气调整',
            'FORMAT': '格式修正',
            'STRAT': '策略调整',
        }
        print(f'\n📊 修正分析报告')
        print(f'   相似度: {similarity:.1%}')
        print(f'   修改级别: {result["metadata"]["change_level"]}')
        print(f'   变更块数: {len(changes)}')
        print(f'   分类分布:')
        for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            name = cat_names.get(cat, cat)
            print(f'     {name}: {count}')

    # 保存结果
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 分析结果已保存到: {args.output}')


if __name__ == '__main__':
    main()
