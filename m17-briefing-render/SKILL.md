---
name: m17-briefing-render
agent_created: true
description: 将 legal-briefing 产出的简报 JSON 转换为 M17 墨水风（Editorial Magazine × E-ink）社交卡片 PNG。
trigger_words:
  - 生成 M17 墨水风图片
  - 生成8张M17墨水风图片
  - M17 卡片
  - M17 墨水风
  - 法律简报配图
  - 小红书图文
  - 从 briefing.json 出图
  - 从 full.json 出图
---

# M17 法律简报图片渲染

## 触发条件

用户要求：
- 生成 M17 墨水风图片
- 生成 8 张 M17 墨水风图片
- 将今日/某日法律简报转为 M17 卡片
- 生成法律简报配图 / 小红书图文
- 从 `YYYY-MM-DD-full.json` 或 `YYYY-MM-DD-briefing.json` 出图

## 前置依赖

1. **技能已同步**：`guizang-social-card-skill` 必须存在于当前设备的 `~/.workbuddy/skills/`。
   - 仓库源：`https://github.com/op7418/guizang-social-card-skill`（用户已 fork 并同步）
   - 关键文件：
     - `assets/template-legal-briefing.html`（M17 种子模板）
     - `scripts/render_m17.py`（Playwright 渲染脚本）

2. **渲染环境**：Python + Playwright + Chromium
   - 默认 venv：`C:\Users\Daniel Xue\.workbuddy\binaries\python\envs\default\`
   - 安装命令：
     ```bash
     "C:/Users/Daniel Xue/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" install playwright
     "C:/Users/Daniel Xue/.workbuddy/binaries/python/envs/default/Scripts/python.exe" -m playwright install chromium
     ```

3. **源数据**（按优先级）：
   - **主路径**：`D:\workbuddy\briefings\YYYY-MM-DD-full.json` 中的 `m17.cases`
   - **备用路径**：`D:\workbuddy\briefings\YYYY-MM-DD-briefing.json` 中的 `articles`

## 执行步骤

### 1. 读取源数据

优先读取 `{DATE}-full.json`：
- 若存在且包含 `m17.cases`（8 条），直接用于渲染。
- 若不存在或缺少 `m17` 段，回退到 `{DATE}-briefing.json`，从 `articles` 中精选 7 篇并人工压缩为 M17 三段式。

### 2. 精选 7 篇内容卡（仅备用路径需要）

从 `articles` 中精选 7 篇，优先覆盖六大执业方向：
- 婚姻家事与财富长青
- 司法强制执行与资产调处
- 企业反舞弊与白领刑事防御
- 公司治理与股权投资争议
- 商事仲裁与复杂争议解决
- 现代农业与异宠特种贸易

封面不含具体案例，仅列目录。

### 3. 内容压缩为 M17 三段式（仅备用路径需要）

每篇内容卡压缩为：
- `kicker`：`案例 0X · 领域`
- `title`：短标题，4-10 字，可换行
- `steps[0..2]`：
  - `step-title`：核心定性 / 法理审视 / 实务要点 / 风险提示 / 程序路径
  - `step-desc`：一句话概括
- `body`：以“应对建议：”开头的实务建议

### 4. 生成 index.html

基于 `assets/template-legal-briefing.html`，替换 `<body>...</body>` 内的 8 个 section：
- 1 个封面 section（`id="xhs-01"`）
- 7 个内容 section（`id="xhs-02"` ~ `id="xhs-08"`）

输出到：`D:\workbuddy\briefings\YYYY-MM-DD-m17\index.html`

### 5. 渲染 PNG

```bash
"C:/Users/Daniel Xue/.workbuddy/binaries/python/envs/default/Scripts/python.exe" \
  "C:/Users/Daniel Xue/.workbuddy/skills/guizang-social-card-skill/scripts/render_m17.py" \
  "D:/workbuddy/briefings/YYYY-MM-DD-m17"
```

输出 8 张 PNG：`xhs-01.png` ~ `xhs-08.png`。

### 6. 写入元数据

创建 `YYYY-MM-DD-m17.json`，记录：
- date
- style
- source_briefing
- cards 列表（id / type / title / direction / output）
- output_dir
- generated_at

## 输出规范

- 风格：`Editorial Magazine × E-ink`，主题 `Ink Classic`
- 宽度：固定 1080px
- 高度：按 M17 规范为 content-driven（auto），实际输出约 968~1150px
- 字体：Noto Serif SC / IBM Plex Mono
- 格式：PNG

## 注意事项

1. **NODE_OPTIONS 冲突**：执行 node 前必须 `unset NODE_OPTIONS`，否则会出现 `--use-system-ca is not allowed in NODE_OPTIONS` 错误。
2. **小红书 3:4**：M17 规范为 height auto；若平台强制要求 1080×1440，需手动调整 `.poster.xhs` 高度或增加内容留白。
3. **内容版权**：引用的文章信息来自微信搜索，卡片本身为原创整理，发布时需标注信息来源。
4. **Token 优化**：主路径直接读取 `full.json` 的 `m17.cases`，避免重复压缩文章；只有在处理历史遗留 `briefing.json` 时才需要 AI 压缩。
