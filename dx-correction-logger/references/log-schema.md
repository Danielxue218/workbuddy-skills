# 修正日志 JSON 结构规范

每条修正记录存储为独立的 JSON 文件，命名格式：`YYYY-MM-DD_{文书类型}_{案件简称}.json`

## 完整结构

```json
{
  "version": "1.0",
  "status": "analyzed",
  "metadata": {
    "case": "赵晓薇法定继承",
    "doc_type": "起诉状",
    "author": "DX",
    "analysis_date": "2026-07-27T16:00:00",
    "before_file": "起诉状_AI_GENERATED.docx",
    "after_file": "起诉状_定稿_DX修改.docx",
    "similarity_ratio": 0.72,
    "change_level": "大幅修改",
    "session_id": "session-xxx",
    "notes": "用户补充了诉讼时效分析段落，调整了诉讼请求排序"
  },
  "stats": {
    "equal_lines": 85,
    "deleted_lines": 12,
    "inserted_lines": 23,
    "replaced_lines": 8,
    "total_before_lines": 120,
    "total_after_lines": 131,
    "categories": {
      "EXPR": 5,
      "STRU": 2,
      "LOGIC": 4,
      "LEGAL": 3,
      "TONE": 1
    }
  },
  "changes": [
    {
      "type": "replace",
      "before_lines": [15, 18],
      "after_lines": [15, 22],
      "before_text": "综上所述，被告的行为已经构成违约...",
      "after_text": "基于上述事实，被告未能按照合同约定履行交付义务...",
      "category": "EXPR",
      "category_detail": "删除套话: 综上所述,"
    }
  ],
  "patterns": [
    {
      "type": "DELETION",
      "text": "综上所述，根据《民法典》第XX条...",
      "count": 2,
      "description": "重复删除的文本（出现2次）"
    }
  ],
  "summary": {
    "total_changes": 43,
    "category_distribution": {
      "EXPR": 5,
      "STRU": 2,
      "LOGIC": 4
    },
    "change_level": "大幅修改"
  }
}
```

## 字段说明

### metadata
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case | string | 是 | 案件简称（已脱敏） |
| doc_type | string | 是 | 起诉状/答辩状/代理词/法律意见书/证据目录/质证意见/法律备忘录/开庭准备/其他 |
| author | string | 是 | 修改人，默认 "DX" |
| analysis_date | string | 是 | ISO 8601 格式 |
| similarity_ratio | float | 是 | 0.0-1.0，修改前后的文本相似度 |
| change_level | string | 是 | 全文重写/大幅修改/段落级修改/措辞微调 |
| notes | string | 否 | 人工备注 |

### stats
| 字段 | 说明 |
|------|------|
| equal_lines | 未修改的行数 |
| deleted_lines | 删除的行数 |
| inserted_lines | 新增的行数 |
| replaced_lines | 替换的行数 |
| categories | 修正类型→次数 映射 |

### changes
数组，每个元素描述一个修改块（"块"指连续的一段修改）。

| 字段 | 说明 |
|------|------|
| type | delete / insert / replace |
| before_lines / after_lines | 行号区间 |
| before_text / after_text | 修改前后的文本 |
| category | EXPR/STRU/LOGIC/LEGAL/FACT/TONE/FORMAT/STRAT |
| category_detail | 分类详情 |

### patterns
数组，自动提取的高置信度修正模式。threshold: 同一修改出现 ≥ 2 次。

## 隐私规则

1. **金额脱敏**：具体金额替换为 `[金额]`
2. **身份证号**：替换为 `[身份证号]`
3. **地址**：替换为 `[地址]`
4. **公司全称**：替换为 `[公司名称]`（首次出现保留简称）
5. **人名**：已有"某某"替代的保持不变，否则替换为 `[当事人]`
6. 不存储完整文书内容——只存储差异块（changes 中的 before_text/after_text）
