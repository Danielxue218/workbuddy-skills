---
name: legal-briefing
description: >
  薛龙律师专属·每日民商事法律要闻简报。
  围绕六大执业方向（婚姻家事与财富长青、司法强制执行与资产调处、
  企业反舞弊与白领刑事防御、公司治理与股权投资争议、商事仲裁与复杂争议解决、
  现代农业与异宠特种贸易），从 36 个白名单公众号自动抓取文章，
  经两步法筛选后生成高信息密度的结构化法律简报。
version: "2.3"
trigger_words:
  - 法律简报
  - 今日法律要闻
  - 生成法律简报
  - 今日简报
  - 每天法律要闻
  - 民商事简报
  - 生成今天的法律简报
  - 今天有什么新案子
  - legal briefing
---

# 技能：每日民商事法律要闻简报 v2.1

## 功能说明

每日自动监测白名单公众号，基于薛龙律师六大执业方向关键词过滤，经法务思维二步筛选后，生成**高信息密度、专业深度**的结构化民商事法律要闻简报。

**本技能唯一责任：抓文章 → 筛选 → 生成结构化简报文本**

---

## 六大执业方向（关键词体系）

以下关键词同时用于：①文章抓取补充搜索，②法务筛选白名单，③简报选题聚焦。

### 一、婚姻家事与财富长青
**核心关键词**：婚姻、家事、继承、财产分割、子女抚养、跨境继承、资产隐匿、遗赠、抚养权、婚前协议、意定监护、涉外婚姻、外销房、公证认证、夫妻债务、离婚、抚养费、探视权、家族信托、财富传承
**补充关键词**：隐匿股权、大额保单、虚拟货币、人格权侵害禁令、少分重罚、涉外继承、跨国婚姻、资产隔离

### 二、司法强制执行与资产调处
**核心关键词**：执行、强制执行、隐匿资产、法人人格否认、执行异议、拒执罪、资产处置、查封、冻结、拍卖、以物抵债、执行和解、追加被执行人、穿透执行、跨境资产、限高、失信、执行转破产
**补充关键词**：代位权、撤销权、应收账款执行、股权执行、到期债权

### 三、企业反舞弊与白领刑事防御
**核心关键词**：职务侵占、挪用资金、反舞弊、商业贿赂、取保候审、合同诈骗、白领犯罪、自首、刑民交叉、刑事合规、非法集资、骗取贷款、虚开、逃税、内幕交易、操纵市场、违法发放贷款
**补充关键词**：黄金37天、高管刑事风险、金融从业者、积极退赃、合规不起诉

### 四、公司治理与股权投资争议
**核心关键词**：股权、股东、代持、对赌、VAM、回购、控制权、公司治理、股东会、董事会、增资、减资、出资、担保、损害公司利益、公司僵局、名股实债、让与担保、一致行动、优先购买权、股东代表诉讼、解散清算、实际控制人
**补充关键词**：股权激励、股权转让、公司决议、关联交易、竞业限制

### 五、商事仲裁与复杂争议解决
**核心关键词**：仲裁、供应链、无名合同、买卖合同、建设工程、新能源、EPC、总承包、涉外、跨境、国际贸易、争议解决、质量缺陷、工期延误、情势变更、不可抗力、违约金、可得利益、定作合同、承揽合同
**补充关键词**：风电、光伏、储能、碳交易、碳排放、电池、原材料、组件、供应链金融

### 六、现代农业与异宠特种贸易
**核心关键词**：异宠、宠物、繁育、养殖、特种养殖、野生动物、合规、濒危、龟、蛇、鹦鹉、交易纠纷、动物防疫、检疫、来源证明、许可证、CITES
**补充关键词**：宠物企业、异宠交易、动物保护、畜牧、水产、种业

---

## 白名单公众号（36个）

### 法院/仲裁委/检察院（13 个）
上海高院、上海浦东法院、最高人民法院、上海静安法院、上海虹口法院、上海普陀法院、上海徐汇法院、上海金融法院、上海二中院、上海杨浦法院、上海一中法院、上海宝山法院、上海长宁法院

### 律所/法律媒体（14 个）
君合法律评述、金杜研究、天同诉讼圈、诉讼攻略、京师德禾律所、宜律无忧、牛津律师团队、至正研究、第一法商、新则、诉讼艺术、审判研究、上海法治报、仲裁圈

### 专业机构/行业协会（9 个）
中国贸促、上海国际仲裁中心、上海律协、上海检察、婚姻家庭与资本市场、中国执行、执行实务与诉讼实务、中国宠物保护协会、中国野生动物保护协会

---

## 使用方式

### 手动触发

直接对 WorkBuddy 说：
> "生成今天的法律简报"

WorkBuddy 会执行：
1. 运行 `legal_briefing.js` 搜索白名单公众号 + 六大方向补充关键词
2. 获取文章列表（含标题、摘要、来源、链接、发布时间）
3. AI 以法务思维逐条审读筛选，生成高信息密度结构化简报

### 自动化触发（推荐，每天 10:00）

自动化 ID：`automation-1782099308244`（本机 Daniel Xue）；另一台电脑（longx）需单独创建

---

## 法务筛选规则（两步筛选法）

### 第一步：行业相关度过滤
**必须通过**（命中六大方向中任一核心/补充关键词）

**一票否决**（命中任一即过滤）：
党建、党委、调研、表彰、慰问、参观、学习贯彻、扫黑除恶、精准扶贫、乡村振兴、行政会议、机关党委、政治教育、廉政、纪检、法官荣誉、先进典型、刑事、行政诉讼、毒品、诈骗、抢劫、盗窃、故意伤害、节日祝福、放假通知、招聘公告

### 第二步：价值评估（任一命中则入选）
- 是否有创新的裁判口径或裁判规则变化？
- 是否涉及六大执业方向的重大行业风险？
- 是否能作为向企业主/高净值客户开拓案源的切入点？
- 是否对在办案件有直接参考价值？

---

## 简报输出格式（高信息密度版）

每条入选文章按照以下完整结构输出，**不设字数上限**，以说清为准：

```
🤖 WorkBuddy 今日法律要闻简报（YYYY-MM-DD）

━━━━━━━━━━━━━━━━━━━━━━

【序号】《文章原标题》
📂 来源：公众号名称
📅 发布日期：YYYY-MM-DD
🔗 链接：URL

🎯 争议焦点
（详细说明案件背景、双方当事人在争议什么、核心法律问题是什么，
 说清楚来龙去脉，不要一句话带过。）

⚖️ 法院/仲裁裁判
（详细说明法院或仲裁委的裁判逻辑、法律适用、关键证据认定、
 说理脉络，以及裁判结果。如有不同审级观点差异，请分组说明。）

💼 应用场景与案源价值
（分析该裁判口径对哪类客户有直接影响，可转化为何种法律服务产品，
 可与哪个已有在办案件形成关联，如何与潜在客户沟通该话题。）
```

**尾部统计**：
```
📌 今日共检索文章 X 篇，入选 Y 篇 | 六大方向覆盖：A方向·B方向·C方向
```

---

## 输出与存档（三项缺一不可）

每次生成简报必须同时产出以下三项：

| 序号 | 输出形式 | 说明 |
|------|---------|------|
| 1 | **WorkBuddy 对话框全文** | 完整简报正文必须在聊天窗口中逐条展示，不可仅推送微信而省略对话框输出 |
| 2 | **Word 文档 (.docx)** | 使用 `python-docx` 生成专业排版的 Word 文档，存档至 `D:\workbuddy\briefings\YYYY-MM-DD-法律简报.docx`（本机）或 `E:\workbuddy\briefings\YYYY-MM-DD-法律简报.docx`（另一台 longx） |
| 3 | **微信推送** | 通过 Server酱 推送完整简报至用户微信（SendKey: SCT366652TBlXQxdb1yp6txFGrPrS3xRrK） |

**Word 文档生成规范**：
- 使用简报生成脚本 `gen_docx.py`（本机：`D:\workbuddy\briefings\gen_docx.py`，另一台：`E:\workbuddy\briefings\gen_docx.py`）
- **字体**：全文宋体（中文）+ Times New Roman（英文/数字）
- **字号**：主标题小二(18pt)、文章标题四号(14pt)、正文小四(12pt)、摘要信息五号(10.5pt)
- **段落间距**：段前0.5行、段后0.5行、1.15倍行距
- **配色**：普鲁士蓝(#1A2530)标题栏 + 哑光香槟金(#C5A059)重点标注 + 深灰(#333333)正文
- **格式**：每条文章含标题（蓝底白字）、来源/日期/案号信息行、争议焦点、法院裁判、应用场景三大板块
- **底部署名**：薛龙 | 合伙人/律师 | 18016302187

**JSON 存档**：`D:\workbuddy\briefings\YYYY-MM-DD-briefing.json`（本机）或 `E:\workbuddy\briefings\YYYY-MM-DD-briefing.json`（另一台 longx）

### 万能 JSON 存档（v2.3 新增 · 统一数据出口）

> v2.3 将 briefing.json + m17.json + moments.json 合并为单个 `{TODAY}-full.json`，消除三文件间的重复数据。
> Part A 写入 briefing + m17 两段；Part B（若启用）追加 moments 段；Part C 从 full.json 直接读取。

**文件位置**：`{BASE}\briefings\YYYY-MM-DD-full.json`

**结构**：
```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "pipeline": {
    "part_a_completed": true,
    "part_b_completed": false,
    "part_c_completed": false,
    "gemini_enabled": false
  },
  "briefing": {
    "total_articles": 35,
    "selected_count": 10,
    "direction_coverage": ["公司治理", "强制执行", "婚姻家事"],
    "articles": [
      {
        "index": 1,
        "title": "...",
        "source": "公众号名称",
        "date": "YYYY-MM-DD",
        "url": "...",
        "dispute_focus": "...",
        "court_ruling": "...",
        "application_value": "...",
        "score": 5,
        "source_mapped": "宜律无忧"
      }
    ]
  },
  "m17": {
    "cases": [
      {
        "index": 1,
        "kicker": "Case · 01",
        "title": "案例主标题（≤10字）",
        "source": "公众号映射名",
        "points": [
          { "title": "要点一（≤8字）", "desc": "描述（30-40字）" },
          { "title": "要点二", "desc": "..." },
          { "title": "要点三", "desc": "..." },
          { "title": "要点四", "desc": "..." }
        ],
        "advice": "应对建议：不含推销用语"
      }
    ]
  },
  "moments": {
    "gemini_enabled": false,
    "cards_generated": 0,
    "selected": [],
    "image_paths": {}
  },
  "output_paths": {
    "briefing_docx": "...",
    "gemini_cards_dir": "...",
    "m17_cards_dir": "..."
  }
}
```

**生成时机**：
- `briefing` + `m17`：Part A 完成后写入（简报 10 条 → 共鸣度评分 → 筛 8 条 → 生成 m17.cases）
- `moments`：Part B 完成后追加（Gemini 卡片路径 + 元数据）
- `pipeline`：各 Part 完成后更新对应 flag

### M17 JSON 从简报直接生成（v2.3 新增 · 不与 moments-post 耦合）

> 此前 m17.json 必须等 moments-post 完成筛选。v2.3 改为 Part A 直接从简报 10 条中评分筛 8 条并生成 m17 数据，存入 full.json。Part C 可立即启动，与 Part B（Gemini 卡片）完全并行。

**评分规则**（与 moments-post 相同）：
| 加分项 | 分值 |
|--------|------|
| 企业主/实控人直接法律风险 | +2 |
| 高净值客户/家庭财富保护 | +2 |
| 当前热门行业 | +1 |
| 反舞弊/合规不起诉 | +1 |
| 强制执行/拒执罪 | +1 |
| 婚姻家事经济补偿 | +1 |

取前 8 条，跳过共鸣度最低的 2 条。`source_mapped` 按映射表匹配（股权代持→宜律无忧、对赌→诉讼攻略 等）。
`advice` 从 `application_value` 提取，删除「开拓XX产品」「可转化为XX法律服务产品」等推销用语。

---

## 命令行参数

```bash
# 本机（Daniel Xue）
NODE_OPTIONS="" "C:\Users\Daniel Xue\.workbuddy\binaries\node\versions\22.12.0\node.exe" \
  "C:\Users\Daniel Xue\.workbuddy\skills\legal-briefing\scripts\legal_briefing.js"

# 另一台电脑（longx）
NODE_OPTIONS="" "C:\Users\longx\.workbuddy\binaries\node\versions\22.12.0\node.exe" \
  "C:\Users\longx\.workbuddy\skills\legal-briefing\scripts\legal_briefing.js"

# 指定白名单（临时覆盖）
--whitelist "天同诉讼圈,审判研究,金杜研究"

# 每账号搜索篇数（默认8）
--max-per-account 5

# 跳过法务筛选（原始输出）
--no-filter
```

---

## 自动化提示词模板（本机 Daniel Xue）

```
运行法律简报技能，生成今日民商事法律要闻简报。必须完成以下全部步骤：

1. 执行搜索脚本：
   "C:\Users\Daniel Xue\.workbuddy\binaries\node\versions\22.12.0\node.exe" "C:\Users\Daniel Xue\.workbuddy\skills\legal-briefing\scripts\legal_briefing.js"

2. AI 生成简报：将 stdout 作为指令，严格按格式输出今日简报（每条详细展开争议焦点、裁判逻辑、案源价值，不设字数上限）。

3. 【必须】在 WorkBuddy 对话框中逐条展示完整简报全文——不可跳过！

4. 保存 JSON：D:\workbuddy\briefings\[今日日期]-briefing.json

5. 生成 Word 文档：运行 python-docx 生成 .docx，存档至 D:\workbuddy\briefings\[今日日期]-法律简报.docx

6. 推送微信：通过 Server酱推送完整简报至用户微信（SendKey: SCT366652TBlXQxdb1yp6txFGrPrS3xRrK）

7. 【可选·级联朋友圈】简报生成完毕后，提示用户：「今日简报已生成。是否需要我基于简报自动生成 8 张朋友圈卡片？」
   若用户同意，加载 moments-post 技能，
   从简报 10 条中按共鸣度筛 8 条 → 并发生成 8 张 9:16 卡片 → 逐张验收。
   卡片存档至 D:\workbuddy\朋友圈发文\[今日日期]\images\
```

## 自动化提示词模板（另一台电脑 longx · v2.3 升级版）

```
运行法律简报技能，生成今日民商事法律要闻简报。必须完成以下全部步骤：

1. 执行搜索脚本：
   "C:\Users\longx\.workbuddy\binaries\node\versions\22.12.0\node.exe" "C:\Users\longx\.workbuddy\skills\legal-briefing\scripts\legal_briefing.js"

2. AI 生成简报：将 stdout 作为指令，严格按格式输出今日简报（每条详细展开争议焦点、裁判逻辑、案源价值，不设字数上限）。

3. 【必须】在 WorkBuddy 对话框中逐条展示完整简报全文——不可跳过！

4. 保存统一 JSON：
   - 按万能 JSON 结构生成 {TODAY}-full.json
   - briefing 段：10 条简报文章（含共鸣度评分）
   - m17 段：对 10 条评分筛 8 条 → 生成 M17 JSON（points[4] + advice，删除推销用语）
   - pipeline.part_a_completed = true
   - 保存至 E:\workbuddy\briefings\[今日日期]-full.json

5. 生成 Word 文档：运行 python-docx 生成 .docx，存档至 E:\workbuddy\briefings\[今日日期]-法律简报.docx

6. 推送微信：通过 Server酱推送完整简报至用户微信（SendKey: SCT366652TBlXQxdb1yp6txFGrPrS3xRrK）

7. 【级联·M17 卡片】简报生成完毕后，加载 guizang-social-card-skill，读取 full.json 的 m17 段，
   自动渲染 8 张 M17 墨水风卡片，存档至 E:\workbuddy\朋友圈发文\[今日日期]\m17-cards\

8. 【可选·Gemini 卡片】若 GEMINI_ENABLED=1，加载 moments-post 技能，基于 full.json
   并发生成 8 张 Gemini 红黑卡，存档至 E:\workbuddy\朋友圈发文\[今日日期]\images\
```

---

## 自动化触发后三技能全自动级联（v5 升级 · 并行 + 统一 JSON）

`automation-1781840242202` 在每天 10:00 触发，全自动完成以下流水线——**不再需要任何手动操作**：

```
10:00 触发
  ├─ Part A: legal-briefing → 简报 + {TODAY}-full.json（含 briefing + m17 两段）
  │                                                ↓
  ├─ Part C: guizang-social-card-skill ────────── 并行 ──────────┐
  │          读取 full.json → 8 张 M17 E-ink 卡片                │
  │                                                              │
  └─ Part B: moments-post（GEMINI_ENABLED=0 默认跳过）           │
             若启用 → 8 张 Gemini 红黑卡 + 追加 moments 段       │
                                                                │
                                                    M17 先出 ──┘
                                                      ↓
                                          Part D: 企业微信推送 M17 图片
                                                + Server酱 完成通知
```

**关键优化（v5 vs v4）**：
- M17 JSON 在 Part A 直接生成（不再等 Part B），Part C 可与 Part B 并行
- 合并为单个 `{TODAY}-full.json`，消除 briefing.json / m17.json / moments.json 三个文件
- `GEMINI_ENABLED` 变量控制 Part B 是否执行（默认 0 跳过，节省 API 积分）
- 企业微信原生推送 M17 卡片图片到微信（替代 Server酱 纯文字路径通知）

详见：
- `C:\Users\longx\.workbuddy\skills\moments-post\SKILL.md`（v3.2，Gemini 可选 + 读 full.json）
- `C:\Users\longx\.workbuddy\skills\guizang-social-card-skill\SKILL.md`（M17 自动化读 full.json）

## 文件位置

- 技能目录：`C:\Users\Daniel Xue\.workbuddy\skills\legal-briefing\`（本机）| `C:\Users\longx\.workbuddy\skills\legal-briefing\`（另一台）
- 抓取脚本：`scripts/legal_briefing.js`
- 简报存档：`E:\workbuddy\briefings\YYYY-MM-DD-briefing.json`
- **统一 JSON**：`E:\workbuddy\briefings\YYYY-MM-DD-full.json`（v2.3 万能 JSON，含 briefing + m17 + moments）
- **级联技能**：`C:\Users\longx\.workbuddy\skills\moments-post\`（朋友圈卡片生成器 v3.2 · Gemini 可选）
- **终端输出**：`E:\workbuddy\朋友圈发文\YYYY-MM-DD\m17-cards\`（M17 E-ink 墨水风卡片）

---

## 版本历史

- **v2.3** (2026-06-24)：新增万能 JSON（`{TODAY}-full.json`）统一数据出口，消除 briefing/m17/moments 三文件重复；M17 JSON 从简报直接评分生成（不再依赖 moments-post），Part C 可与 Part B 并行；新增 `GEMINI_ENABLED` 开关
- **v2.2** (2026-06-24)：级联升级为三技能全自动流水线（legal-briefing → moments-post → guizang-social-card-skill M17），不再需要任何手动触发；更新级联说明和文件位置
- **v2.1** (2026-06-23)：白名单从 29 → 36（新增 宜律无忧、诉讼攻略、执行实务与诉讼实务、牛津律师团队、京师德禾律所、中国宠物保护协会、中国野生动物保护协会，与 moments-post v3.1 出处映射表对齐）
- v2.0 (2026-06-22)：初始版本，29 白名单 + 两步筛选法 + Word 文档 + Server酱 推送
