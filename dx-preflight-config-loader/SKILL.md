---
name: dx-preflight-config-loader
description: 蒸馏配置预加载器——在任何法律任务启动前自动加载三份个性化蒸馏配置文件（USER.md + PERSONAL-LEGAL-MINDSET.md + writing-style-profile），确保 WorkBuddy 的所有法律技能输出均贴合薛龙律师的个人办案习惯。此技能为隐形层，用户无需感知其存在。触发：任何 dx-* 法律技能加载前自动调用，或自然语言中涉及法律分析/文书生成/案件论证时自动激活。
agent_created: true
version: "1.0.0"
author: DX
---

# dx-preflight-config-loader

## 职责

**唯一职责**：在每次法律任务启动时，读取并注入三份蒸馏配置文件到当前会话上下文中。

此技能不产出任何直接输出。它是所有法律技能的前置拦截层——沉默、自动、不可绕过。

## 三份受管理配置

| 配置 | 路径 | 内容 |
|------|------|------|
| USER.md | `~/.workbuddy/USER.md` | 薛龙执业画像（城市/律所/业务领域/代理倾向/不可容忍错误） |
| PERSONAL-LEGAL-MINDSET.md | `~/.workbuddy/PERSONAL-LEGAL-MINDSET.md` | 办案思维模型（证据审查/IRAC/策略偏好/案由专项/禁忌清单） |
| writing-style-profile | `~/.workbuddy/skills/writing-style-profile/SKILL.md` | 文书格式与表达风格（语气/编号/引用/表达模板/禁区） |

## 工作流

### 阶段 1：读取配置文件

```
读取 ~/.workbuddy/USER.md → 注入执业身份
读取 ~/.workbuddy/PERSONAL-LEGAL-MINDSET.md → 注入办案思维
读取 ~/.workbuddy/skills/writing-style-profile/SKILL.md → 注入文书风格
```

### 阶段 2：生成任务简报（仅内部，不输出给用户）

基于当前法律任务类型，从三份配置中提取相关约束：

- 如果是法律分析 → 重点提取 PERSONAL-LEGAL-MINDSET.md 中的推理框架（IRAC五段论、穿透式分析）
- 如果是文书生成 → 重点提取 writing-style-profile 中的格式约束（编号规范、表达禁区）
- 如果是案件策略 → 重点提取 PERSONAL-LEGAL-MINDSET.md 中的策略偏好（财产保全、多线并进）

### 阶段 3：静默注入

将提取的约束作为上下文注入后续法律技能的执行中，确保所有输出符合薛龙的办案习惯。

## 强制触发规则

以下情况**必须**先加载本技能：

1. 任何 `dx-*` 法律技能被触发时（如 dx-claim-basis-nine-step, dx-legal-element-extraction, dx-evidence-evaluation 等）
2. 用户要求撰写任何法律文书（起诉状、答辩状、代理词、质证意见、法律意见书等）
3. 用户要求进行法律分析、案件评估、诉讼策略建议
4. 用户提及任何 DX_ 前缀案件并要求处理

## 设计原则

- **隐形**：用户不需要知道此技能的存在，不需要主动调用
- **自动**：Agent 在加载任何法律技能前自动调用
- **不可绕过**：没有例外，每次法律任务都必须注入三份配置
- **轻量**：只做读取和注入，不做任何分析或生成
