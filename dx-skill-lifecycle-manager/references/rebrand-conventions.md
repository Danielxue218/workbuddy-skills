# 改名换姓规范（Rebrand Conventions）

## 1. 文件夹重命名规则

### 1.1 前缀统一

所有通过本管理器引入的技能，文件夹名统一使用 `dx-` 前缀。

| 原名模式 | 新名模式 | 示例 |
|----------|----------|------|
| 无前缀 | `dx-` 前缀 | `case-retrieval` -> `dx-case-retrieval` |
| `mqc-` 前缀 | `dx-` 前缀 | `mqc-claim-basis-nine-step` -> `dx-claim-basis-nine-step` |
| `m17-` 前缀 | `dx-` 前缀 | `m17-briefing-render` -> `dx-wechat-briefings-render` |
| 其他前缀 | `dx-` 前缀 | `legal-card-rules` -> `dx-wechat-briefings-rules` |
| 已有 `dx-` 前缀 | 保持不变 | `dx-evidence-evaluation` -> 不变 |

### 1.2 例外清单

以下技能保留原名，不加 `dx-` 前缀（由用户明确指定）：

| 技能名 | 原因 |
|--------|------|
| `guizang-social-card-skill` | 第三方品牌技能，保留原名 |
| `nano-banana-pro-image-gen` | 第三方品牌技能，保留原名 |
| `humanizer` | 通用工具，名称简洁 |
| `wechat-article-search` | 通用工具，名称明确 |
| `writing-style-profile` | 配置文件类，名称明确 |

> 新的例外需用户明确指定，并在此清单中登记。

---

## 2. SKILL.md 元数据改造规则

### 2.1 必改字段

| 字段 | 原值示例 | 新值示例 | 规则 |
|------|----------|----------|------|
| `name` | `case-retrieval` | `dx-case-retrieval` | 与文件夹名一致，加 `dx-` 前缀 |
| `author` | `CSlawyer1985` / `Daniel Xue` | `DX` | 统一为 `DX` |
| `version` | `1.0.0` | `1.0.0-dx` | 首次改造附加 `-dx` 后缀；后续改造递增小版本号 |
| `last_updated` | 任意 | 当天日期 | 改为当天 `YYYY-MM-DD` |

### 2.2 新增字段

| 字段 | 值 | 说明 |
|------|-----|------|
| `source` | 原始来源 URL 或描述 | 如 `github.com/CSlawyer1985/claude-for-legal-ZH` |
| `original_name` | 原始技能名 | 如 `case-retrieval` |
| `displayName` | 中文显示名 | 如 `案例检索`（如原文已有则保留） |

### 2.3 保留字段

以下字段保持原值不动：

| 字段 | 说明 |
|------|------|
| `license` | 原始许可证，尊重开源协议 |
| `description` | 触发描述，仅在 Phase 7 边用边改时优化 |
| `tags` | 保留原有标签，追加 `DX改造` |
| 正文内容 | 核心逻辑方法论不改，仅追加来源声明 |

---

## 3. 正文微调规则

### 3.1 来源声明

在概述段落（第一个 `##` 之后的内容）末尾追加：

```markdown
> 本技能由 DX 基于开源版本改造，适配个人工作流。原始来源：{source}
```

### 3.2 改进日志

在 SKILL.md 末尾追加 `## 改进日志` 章节（如无则新增）：

```markdown
## 改进日志

- 2026-07-27 首次引入并 DX 改造（来源：{source}）
```

后续每次边用边改时在此追加记录。

---

## 4. 改名确认表格式

向用户展示的 before/after 对比表：

```
┌──────────────────────────────────────────────────┐
│  Rebrand 确认                                     │
├──────────────────────────────────────────────────┤
│  文件夹：{old_folder} -> {new_folder}             │
│  name：  {old_name}    -> {new_name}              │
│  author：{old_author}   -> DX                     │
│  version：{old_version} -> {old_version}-dx       │
│  +source: {source}                               │
│  +original_name: {old_name}                      │
│  +tags: DX改造                                    │
│  +正文末尾: 来源声明                               │
├──────────────────────────────────────────────────┤
│  确认后执行？(Y/n)                                │
└──────────────────────────────────────────────────┘
```

---

## 5. 特殊情况处理

### 5.1 技能包含子目录/子技能

如技能包含 `skills/` 子目录（如 legal-builder-hub），需递归处理所有子技能的 SKILL.md。

### 5.2 技能包含可执行脚本

如技能包含 `.py` / `.ps1` / `.sh` 脚本：
- 不修改脚本内容（除非路径引用需要更新）
- 在 SKILL.md 中记录脚本列表
- 执行安全审查后再部署

### 5.3 技能已被 DX 改造过

如 SKILL.md 中已有 `author: DX`：
- 不重复改造
- 仅更新 `last_updated` 和 `version`
- 追加改进日志记录
