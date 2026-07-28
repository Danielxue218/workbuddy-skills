---
name: dx-correction-logger
description: 修正反馈循环 v2.0（被动自动模式）——每次 Agent 生成法律文书后，自动检测用户是否对输出文件进行了修改，无需用户主动触发。发现修改后自动对比、分类、学习，静默更新三份蒸馏配置文件。用户完全无需感知此技能的存在。月度综合报告每月1日自动触发。触发词（兼容旧版）：修正日志、修正反馈、修改记录、correction log、学习我的修改。
version: "2.0.0"
mode: passive-auto
author: DX
last_updated: 2026-07-27
source: DX原创
original_name: dx-correction-logger
tags:
  - DX改造
  - 技能管理
  - 反馈循环
  - 蒸馏工程
agent_created: true
disabled: false
---

# 修正反馈循环技能（Correction Feedback Loop）

## 目的

本技能建立一个闭环系统：用户每次修改 AI 生成的文书 → 自动捕获修正 → 聚类分析修正模式 → 更新三份个人化配置文件。目标是让 WorkBuddy **从用户的每一次修改中学习**，逐步减少需要人工修正的频次和幅度。

## 三份受管理配置文件

| 文件 | 运行时路径 | 技能库路径（权威源） |
|------|-----------|---------------------|
| USER.md | `~/.workbuddy/USER.md` | `E:\workbuddy\Skill管理\个人配置\USER.md` |
| PERSONAL-LEGAL-MINDSET.md | `~/.workbuddy/PERSONAL-LEGAL-MINDSET.md` | `E:\workbuddy\Skill管理\个人配置\PERSONAL-LEGAL-MINDSET.md` |
| writing-style-profile SKILL.md | `~/.workbuddy/skills/writing-style-profile/SKILL.md` | `E:\workbuddy\Skill管理\技能库\16-通用工具\writing-style-profile\SKILL.md` |

> 修正日志存储目录：`~/.workbuddy/correction-log/`（运行时数据，不归档到技能库）

## 触发条件（v2.0 被动自动模式）

本技能不再依赖用户主动触发。Agent 在以下场景自动静默激活：

1. **自动触发（被动）**：每次 Agent 生成法律文书并保存到文件后，自动检查用户是否对文件进行了后续修改
2. **会话结束触发**：每次法律任务会话结束时，自动扫描本次会话中生成的所有文书文件，对比最初生成版本和当前版本
3. **月度综合**：每月 1 日自动触发（automation-1785142043600）
4. **兼容旧版**：用户仍可说"记录这次修改"手动触发（保留向后兼容）

**被动检测机制**：Agent 在每次生成法律文书文件后，记录文件 hash。下次涉及该文件时，对比 hash 判断是否需要分析修正。

## 工作流

### 阶段一：捕获修正（Correction Capture）

**触发**：用户表明已经对 AI 生成的文书做了人工修改。

**步骤**：

1. 确认获取修改前后两个版本：
   - 如果修改前版本是 AI 刚才生成的 → 从对话历史中提取
   - 如果修改前版本是文件 → 读取文件
   - 修改后版本 → 读取用户修改后的文件

2. 提取元数据：
   ```
   - 文书类型：起诉状/答辩状/代理词/法律意见书/证据目录/质证意见/法律备忘录/开庭准备/其他
   - 案件名称/案号
   - 修改日期
   - 修改范围：全文重写/段落级修改/措辞微调/结构调整/补充论证
   ```

3. 存储修正记录到 `~/.workbuddy/correction-log/` 目录：
   - 文件名格式：`YYYY-MM-DD_{文书类型}_{案件简称}.json`
   - 文件结构见 `references/log-schema.md`

4. 执行快速差异分析（调用 `scripts/correction_diff.py`），输出初步修改摘要。

### 阶段二：单次即时学习（Instant Learning）

在捕获修正后，立即执行轻量级学习：

1. 识别本次修改的高置信度模式：
   - **删除类**：AI 写的某些表达被删 → 加入"禁止表达"清单
   - **替换类**：AI 用的词被换成另一个词 → 更新术语偏好
   - **补充类**：AI 漏了某段论证 → 提示该文书类型需要补充的模块
   - **结构调整类**：段落顺序被调整 → 更新该文书类型的结构模板

2. 如果模式置信度 > 80%（同一类型修改出现 ≥ 2 次），直接更新对应配置文件：
   - 表达/术语类 → `writing-style-profile`
   - 论证结构/策略类 → `PERSONAL-LEGAL-MINDSET.md`
   - 执业偏好类 → `USER.md`

3. 向用户报告本次学习成果：学到了什么，更新了哪个文件。

### 阶段三：月度综合分析（Monthly Synthesis）

**触发**：用户要求"分析本月修改"或每月 1 日自动触发。

**步骤**：

1. 扫描 `~/.workbuddy/correction-log/` 中本月所有修正记录
2. 调用 `scripts/monthly_synthesis.py` 执行全量分析：
   - 按文书类型聚类
   - 按修改类型聚类
   - 识别高频修正模式（同一类型修正出现 ≥ 3 次）
   - 识别新出现的修正模式（之前未见过）
3. 生成月度学习报告（Markdown），保存到 `~/.workbuddy/correction-log/reports/YYYY-MM_learning-report.md`
4. 对高置信度模式（出现 ≥ 3 次），自动更新三份配置文件
5. 向用户呈现报告摘要和已应用的更新清单

### 阶段四：配置文件更新（Config Update）

更新配置文件时，遵循以下原则：

1. **增量更新**：不在现有内容上直接改写，而是在对应章节末尾添加 `<!-- correction: YYYY-MM-DD -->` 标记的新条目
2. **可追溯**：每次更新标注来源（哪份修正记录的哪次修正）
3. **不覆盖用户手动写入的内容**
4. **冲突检测**：如果自动提取的规则与现有规则冲突，标记为 `⚠️ 待确认` 并报告用户

## 修正分类体系

所有修正归入以下 8 类：

| 代码 | 类别 | 说明 | 示例 |
|------|------|------|------|
| `EXPR` | 表达修正 | 措辞、用语、句式调整 | "综上所述" → 删除 |
| `STRU` | 结构调整 | 段落顺序、标题层级、篇幅分配 | 把诉讼请求提前到事实之前 |
| `LOGIC` | 逻辑补强 | 补充论证环节、修复逻辑漏洞 | 补充因果关系分析 |
| `LEGAL` | 法律论证 | 法条引用、案例补充、法律分析深化 | 补充民法典第X条分析 |
| `FACT` | 事实修正 | 事实描述调整、证据引用修正 | 修正金额数字、补充时间线 |
| `TONE` | 语气调整 | 攻击性/防御性/中性调整 | "显然违约" → "存在违约情形" |
| `FORMAT` | 格式修正 | 编号、标点、排版 | 调整标题编号格式 |
| `STRAT` | 策略调整 | 诉讼策略层面的修改 | 增加管辖权异议论点 |

## 使用脚本

### correction_diff.py

对比两个文本文件，输出结构化差异报告。

```bash
python scripts/correction_diff.py <before_file> <after_file> --output <json_output>
```

输出 JSON 包含：删除的行、新增的行、修改的行（old → new），以及初步分类建议。

### monthly_synthesis.py

扫描月度修正日志目录，生成综合学习报告。

```bash
python scripts/monthly_synthesis.py --month YYYY-MM --log-dir ~/.workbuddy/correction-log/ --output <report_path>
```

## 存储结构

```
~/.workbuddy/
├── correction-log/
│   ├── 2026-07-27_起诉状_赵晓薇继承.json    # 单条修正记录
│   ├── 2026-07-28_代理词_魏金燕借贷.json
│   ├── ...
│   └── reports/
│       ├── 2026-07_learning-report.md        # 月度报告
│       └── 2026-08_learning-report.md
├── USER.md                                    # 受管理
├── PERSONAL-LEGAL-MINDSET.md                   # 受管理
└── skills/writing-style-profile/SKILL.md       # 受管理
```

## 安全规则

1. 修正日志仅存储文书的结构化差异，不复制完整文书内容（避免泄露当事人信息）
2. 月度报告中的示例使用匿名化片段
3. 不得在未确认的情况下删除用户手动写入的规则
4. PII 数据不入日志——金额、身份证号、具体地址在存储前脱敏
