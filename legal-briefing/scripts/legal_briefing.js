#!/usr/bin/env node

/**
 * 民商事法律简报生成器 v2.4
 *
 * 围绕薛龙律师六大执业方向，从白名单公众号自动抓取文章，
 * 经来源优先级排序、一账号一篇去重、关键词筛选后，
 * 输出高信息密度结构化简报 Prompt。
 *
 * v2.4 变更：来源优先级重构 + 日期窗口放宽 + 关键词筛选放宽
 *   1. 来源优先级：白名单法院/仲裁（1）> 白名单外法院公众号（2）
 *                       > 头部红圈律所（天同/金杜/君合）（3）
 *                       > 白名单其他律所/机构（4）> 法律类非白名单（5）
 *   2. 日期窗口：默认今日，不足 10 条时自动放宽到最近 3 天
 *   3. 关键词筛选放宽：白名单池不足时，降低关键词门槛（仅标题命中即通过）
 *   4. 六大方向筛选放宽：删除刑事/行政诉讼等实务词排除，仅过滤宣传稿
 *   5. 一账号一篇规则：法院/仲裁账号允许一天最多 2 篇，其他仍限制 1 篇
 *
 * v2.3 变更：白名单优先模式（默认开启）
 *   --strict-whitelist（默认）：仅采纳白名单公众号来源的文章
 *     · 白名单账号搜索（Tier 1）结果：全部保留（来源为白名单）
 *     · 补充关键词搜索（Tier 2）结果：仅保留来源为白名单公众号的
 *     · 兜底：若白名单池 < 10 条，才放宽至关键词命中的法律类来源
 *   --no-strict-whitelist：沿用 v2.0 逻辑（白名单+关键词全网搜索，来源不限）
 *
 * 用法：
 *   node legal_briefing.js [--no-strict-whitelist] [--whitelist "上海高院,..."] [--output result.json]
 */

const https = require('https');
const zlib = require('zlib');
const fs = require('fs');
const path = require('path');

// ─────────────────────────────────────────────
// 白名单账号（36个 · v2.1 扩充）
// ─────────────────────────────────────────────
const WHITELIST_ACCOUNTS = [
  '上海高院', '第一法商', '中国贸促', '上海浦东法院', '最高人民法院',
  '君合法律评述', '上海静安法院', '上海国际仲裁中心', '上海虹口法院',
  '上海普陀法院', '上海徐汇法院', '上海律协', '上海金融法院', '新则',
  '上海二中院', '至正研究', '上海杨浦法院', '上海一中法院', '诉讼艺术',
  '天同诉讼圈', '审判研究', '上海检察', '上海宝山法院', '金杜研究',
  '上海法治报', '仲裁圈', '上海长宁法院', '婚姻家庭与资本市场', '中国执行',
  // v2.1 新增（7 个，与 moments-post 出处映射表对齐）
  '宜律无忧', '诉讼攻略', '执行实务与诉讼实务', '牛津律师团队',
  '京师德禾律所', '中国宠物保护协会', '中国野生动物保护协会',
];

// 备用账号列表
const DEFAULT_ACCOUNTS = [
  '北京仲裁委员会', '广东省高级人民法院', '中国国际经济贸易仲裁委员会',
  '深圳国际仲裁院', '武汉仲裁委员会',
];

// ─────────────────────────────────────────────
// 来源优先级分层（用于最终排序）
// ─────────────────────────────────────────────

// 法院/审判/检察/执行等官方司法来源（优先级最高）
const COURT_SOURCES = [
  '上海高院', '上海浦东法院', '最高人民法院', '上海静安法院',
  '上海虹口法院', '上海普陀法院', '上海徐汇法院', '上海二中院',
  '上海杨浦法院', '上海一中法院', '上海检察', '上海宝山法院',
  '上海长宁法院', '审判研究', '上海金融法院', '中国执行',
  '广东省高级人民法院', '上海法治报', '第一法商',
];

// 仲裁机构（优先级次之）
const ARBITRATION_SOURCES = [
  '上海国际仲裁中心', '北京仲裁委员会', '中国国际经济贸易仲裁委员会',
  '深圳国际仲裁院', '武汉仲裁委员会', '仲裁圈',
];

// 头部红圈/精品律所（优先级高于其他白名单律所）
const TOP_TIER_LAW_FIRMS = [
  '天同诉讼圈', '金杜研究', '君合法律评述',
];

// ─────────────────────────────────────────────
// 六大执业方向 · 补充关键词搜索（宽口径捕捞）
// ─────────────────────────────────────────────
const SUPPLEMENT_KEYWORDS = [
  // 一、婚姻家事与财富长青
  '跨境继承 资产隐匿 判决',
  '夫妻共同债务 强制执行 房产',
  '意定监护 涉外婚姻 协议',
  '离婚 股权分割 抚养权 判决',
  // 二、司法强制执行与资产调处
  '法人人格否认 追加被执行人 判决',
  '拒执罪 隐匿资产 执行异议',
  '股权执行 应收账款执行 案例',
  // 三、企业反舞弊与白领刑事防御
  '职务侵占 挪用资金 取保候审',
  '反舞弊 商业贿赂 合规不起诉',
  '刑民交叉 合同诈骗 辩护',
  // 四、公司治理与股权投资争议
  '对赌协议 股权回购 裁判',
  '股权代持 确权 纠纷 判决',
  '股东代表诉讼 损害公司利益',
  // 五、商事仲裁与复杂争议解决
  '新能源 供应链 合同纠纷 裁判',
  '建设工程 EPC 总承包 质量 仲裁',
  '买卖合同 违约金 调减 判决',
  '国际贸易 跨境 仲裁 裁决',
  // 六、现代农业与异宠特种贸易
  '异宠 合规 交易纠纷',
  '特种养殖 野生动物 许可证',
  '宠物 繁育 合同 纠纷',
];

// ─────────────────────────────────────────────
// 法务筛选规则
// ─────────────────────────────────────────────

// 六大执业方向关键词白名单（命中任一即通过第一步）
const INCLUDE_KEYWORDS = [
  // 一、婚姻家事与财富长青
  '婚姻', '家事', '继承', '财产分割', '子女抚养', '跨境继承', '资产隐匿',
  '遗赠', '抚养权', '婚前协议', '意定监护', '涉外婚姻', '外销房',
  '公证认证', '夫妻债务', '离婚', '抚养费', '探视权', '家族信托', '财富传承',
  '隐匿股权', '大额保单', '虚拟货币', '人格权侵害禁令', '少分重罚',
  '涉外继承', '跨国婚姻', '资产隔离', '夫妻共同财产',

  // 二、司法强制执行与资产调处
  '执行', '强制执行', '法人人格否认', '执行异议', '拒执罪', '资产处置',
  '查封', '冻结', '拍卖', '以物抵债', '执行和解', '追加被执行人',
  '穿透执行', '跨境资产', '限高', '失信', '执行转破产',
  '代位权', '撤销权', '应收账款', '股权执行', '到期债权', '执行不能',

  // 三、企业反舞弊与白领刑事防御
  '职务侵占', '挪用资金', '反舞弊', '商业贿赂', '取保候审', '合同诈骗',
  '白领犯罪', '自首', '刑民交叉', '刑事合规', '非法集资', '骗取贷款',
  '虚开', '逃税', '内幕交易', '操纵市场', '违法发放贷款',
  '高管刑事风险', '积极退赃', '合规不起诉', '认罪认罚',

  // 四、公司治理与股权投资争议
  '股权', '股东', '代持', '对赌', 'VAM', '回购', '控制权',
  '公司治理', '股东会', '董事会', '增资', '减资', '出资', '担保',
  '损害公司利益', '公司僵局', '名股实债', '让与担保', '一致行动',
  '优先购买权', '股东代表诉讼', '解散清算', '实际控制人',
  '股权激励', '股权转让', '公司决议', '关联交易', '竞业限制',

  // 五、商事仲裁与复杂争议解决
  '仲裁', '供应链', '无名合同', '买卖合同', '建设工程', '新能源',
  'EPC', '总承包', '涉外', '跨境', '国际贸易', '质量缺陷', '工期延误',
  '情势变更', '不可抗力', '违约金', '可得利益', '定作合同', '承揽合同',
  '风电', '光伏', '储能', '碳交易', '碳排放', '电池', '原材料', '组件',
  '供应链金融', '争议解决',

  // 六、现代农业与异宠特种贸易
  '异宠', '宠物', '繁育', '养殖', '特种养殖', '濒危', '龟',
  '蛇', '鹦鹉', '交易纠纷', '动物防疫', '检疫', '来源证明',
  '许可证', 'CITES', '动物保护', '畜牧', '水产', '种业',
];

// 一票否决黑名单（仅过滤宣传稿/非实务内容，法律实务类文章均放开）
const EXCLUDE_KEYWORDS = [
  '党建', '党委', '调研', '表彰', '慰问', '参观', '学习贯彻', '政法',
  '扫黑除恶', '扫黑', '黑恶势力', '精准扶贫', '乡村振兴', '援藏', '援疆',
  '行政会议', '机关党委', '政治教育', '廉政', '纪检', '监察', '法官荣誉',
  '先进典型', '优秀法官', '道德讲堂', '演讲比赛', '征文', '知识竞赛',
  '节日祝福', '温馨提示', '放假通知', '招聘公告', '人员调整',
];

// ─────────────────────────────────────────────
// 网络工具
// ─────────────────────────────────────────────

const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
];

function randomUA() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function decompressBody(buffer, encoding) {
  if (!encoding) return buffer;
  const enc = String(encoding).toLowerCase();
  try {
    if (enc.includes('gzip')) return zlib.gunzipSync(buffer);
    if (enc.includes('deflate')) return zlib.inflateSync(buffer);
    if (enc.includes('br')) return zlib.brotliDecompressSync(buffer);
  } catch {}
  return buffer;
}

async function httpGet(url, cookieStr = '', timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const headers = {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Encoding': 'identity',
      'Accept-Language': 'zh-CN,zh;q=0.9',
      'User-Agent': randomUA(),
      'Host': urlObj.hostname,
      'Referer': 'https://weixin.sogou.com/',
    };
    if (cookieStr) headers['Cookie'] = cookieStr;

    const req = https.request({
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers,
    }, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks);
        const body = decompressBody(raw, res.headers['content-encoding']);
        resolve({ statusCode: res.statusCode, headers: res.headers, text: body.toString('utf-8') });
      });
    });
    req.on('error', reject);
    req.setTimeout(timeoutMs, () => { req.destroy(); reject(new Error('timeout')); });
    req.end();
  });
}

async function getSogouCookie() {
  try {
    const res = await httpGet('https://v.sogou.com/v?ie=utf8&query=&p=40030600', '', 8000);
    const setCookie = res.headers['set-cookie'] || [];
    return setCookie.map(c => c.split(';')[0]).join('; ');
  } catch {
    return '';
  }
}

// ─────────────────────────────────────────────
// 解析搜狗微信搜索结果
// ─────────────────────────────────────────────

function parseDate(text) {
  let m = text.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (m) {
    const d = new Date(`${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}T00:00:00+08:00`);
    return d.toISOString().slice(0, 10);
  }
  m = text.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) {
    return `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
  }
  m = text.match(/(\d+)天前/);
  if (m) {
    const d = new Date(Date.now() - parseInt(m[1]) * 86400000);
    return d.toISOString().slice(0, 10);
  }
  if (text.includes('昨天')) {
    const d = new Date(Date.now() - 86400000);
    return d.toISOString().slice(0, 10);
  }
  if (text.includes('今天')) {
    return new Date().toISOString().slice(0, 10);
  }
  return '';
}

function parseSearchHtml(html, maxN) {
  const articles = [];
  const liBlocks = html.match(/<li[^>]*>[\s\S]*?<\/li>/g) || [];

  for (const li of liBlocks) {
    if (articles.length >= maxN) break;

    const titleMatch = li.match(/<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/);
    if (!titleMatch) continue;
    let url = titleMatch[1];
    const title = titleMatch[2].replace(/<[^>]+>/g, '').trim();
    if (!title || !url) continue;
    if (url.startsWith('/')) url = 'https://weixin.sogou.com' + url;

    const summaryMatch = li.match(/class="txt-info"[^>]*>([\s\S]*?)<\/p>/);
    const summary = summaryMatch
      ? summaryMatch[1].replace(/<[^>]+>/g, '').trim()
      : '';

    const sourceMatch = li.match(/class="all-time-y2"[^>]*>([\s\S]*?)<\/span>/) ||
      li.match(/class="account"[^>]*>([\s\S]*?)<\/a>/) ||
      li.match(/<span[^>]*class="[^"]*account[^"]*"[^>]*>([^<]+)/);
    const source = sourceMatch ? sourceMatch[1].replace(/<[^>]+>/g, '').trim() : '';

    let datetime = '';
    const tsMatch = li.match(/var\s+ts\s*=\s*(\d+)/);
    if (tsMatch) {
      const ts = parseInt(tsMatch[1]) * 1000;
      const d = new Date(ts);
      if (d.getFullYear() >= 2020 && d.getFullYear() <= 2030) {
        datetime = d.toISOString().slice(0, 10);
      }
    }
    if (!datetime) {
      datetime = parseDate(li);
    }

    articles.push({ title, url, summary, source, datetime });
  }

  return articles;
}

// ─────────────────────────────────────────────
// 搜索函数
// ─────────────────────────────────────────────

async function searchWechat(query, maxN = 8) {
  const articles = [];
  let page = 1;
  const cookie = await getSogouCookie();
  const maxPages = Math.ceil(maxN / 10);

  while (articles.length < maxN && page <= maxPages) {
    try {
      const url = `https://weixin.sogou.com/weixin?query=${encodeURIComponent(query)}&type=2&page=${page}&ie=utf8`;
      const res = await httpGet(url, cookie, 25000);
      const parsed = parseSearchHtml(res.text, maxN - articles.length);
      if (parsed.length === 0) break;
      articles.push(...parsed);
      page++;
      if (page <= maxPages) await sleep(600 + Math.random() * 800);
    } catch (err) {
      process.stderr.write(`Search "${query}" p${page} failed: ${err.message}\n`);
      break;
    }
  }

  return articles.slice(0, maxN);
}

// ─────────────────────────────────────────────
// 法务筛选
// ─────────────────────────────────────────────

function legalFilter(article) {
  const text = `${article.title} ${article.summary}`;

  // 黑名单过滤
  for (const kw of EXCLUDE_KEYWORDS) {
    if (text.includes(kw)) return false;
  }

  // 白名单命中
  for (const kw of INCLUDE_KEYWORDS) {
    if (text.includes(kw)) return true;
  }

  return false;
}

// 白名单来源校验（精确匹配 + 双向子串匹配，处理"上海高级人民法院"↔"上海高院"等缩写差异）
function isWhitelistSource(source) {
  if (!source) return false;
  const s = source.trim();
  for (const wl of WHITELIST_ACCOUNTS) {
    if (s === wl || s.includes(wl) || wl.includes(s)) return true;
  }
  return false;
}

// 法律类来源启发式判断（用于兜底放宽时的质量门槛）
// 来源名含：律师/律所/法院/仲裁/法学/研究/检察/司法/诉讼/合规/审判 等法律标识词
function looksLikeLegalSource(source) {
  if (!source) return false;
  const markers = ['律师', '律所', '法院', '仲裁', '法学', '研究', '检察',
                   '司法', '诉讼', '合规', '审判', '法', '法律', '法务', '法商'];
  const s = source.trim();
  return markers.some(m => s.includes(m));
}

// 法院/审判/检察来源校验（精确+双向子串匹配）
function isCourtSource(source) {
  if (!source) return false;
  const s = source.trim();
  for (const cs of COURT_SOURCES) {
    if (s === cs || s.includes(cs) || cs.includes(s)) return true;
  }
  return false;
}

// 仲裁机构来源校验（精确+双向子串匹配）
function isArbitrationSource(source) {
  if (!source) return false;
  const s = source.trim();
  for (const ar of ARBITRATION_SOURCES) {
    if (s === ar || s.includes(ar) || ar.includes(s)) return true;
  }
  return false;
}

// 白名单外法院/审判来源识别（来源含法院/检察/执行等词，但不在 WHITELIST_ACCOUNTS 中）
function isNonWhitelistCourtSource(source) {
  if (!source) return false;
  const s = source.trim();
  // 先排除白名单内已有账号
  if (isWhitelistSource(s)) return false;
  // 识别法院/审判/检察/执行相关来源
  const courtMarkers = ['法院', '中院', '高院', '检察', '执行', '审判', '法庭', ' Judicial', '仲裁'];
  return courtMarkers.some(m => s.includes(m));
}

// 头部红圈/精品律所识别
function isTopTierLawFirm(source) {
  if (!source) return false;
  const s = source.trim();
  return TOP_TIER_LAW_FIRMS.some(t => s === t || s.includes(t) || t.includes(s));
}

// 来源优先级评分：数字越小优先级越高（v2.4 重构）
function getSourcePriority(source) {
  if (!source) return 99;
  const s = source.trim();
  // 1. 白名单法院/仲裁/审判/检察来源（最高优先级）
  if (isCourtSource(s) || isArbitrationSource(s)) return 1;
  // 2. 白名单外法院/审判/检察公众号（通过关键词搜索捕捞）
  if (isNonWhitelistCourtSource(s)) return 2;
  // 3. 头部红圈/精品律所（天同/金杜/君合）
  if (isTopTierLawFirm(s)) return 3;
  // 4. 白名单其他律所/机构
  if (isWhitelistSource(s)) return 4;
  // 5. 法律类非白名单公众号（兜底）
  if (looksLikeLegalSource(s)) return 5;
  // 99. 其他来源（仅关键词筛选放宽时才会进入）
  return 99;
}

function dedup(articles) {
  const seen = new Set();
  return articles.filter(a => {
    const key = a.title.replace(/\s/g, '').slice(0, 20);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ─────────────────────────────────────────────
// 简报 Prompt 生成（v2.0：高信息密度版）
// ─────────────────────────────────────────────

function buildBriefingPrompt(articles, date, targetDate) {
  const articleList = articles.map((a, i) => {
    return `[${i + 1}] 标题：${a.title}
来源：${a.source || '未知公众号'}
发布时间：${a.datetime || '未知'}
摘要：${a.summary || '（无摘要）'}
链接：${a.url}`;
  }).join('\n\n');

  const dateInstruction = targetDate
    ? `⚠️ 重要：本次简报仅包含发布日期为 ${targetDate} 的文章。请先核对每篇文章的"发布时间"字段，只处理该日期的文章，其他日期的文章直接忽略。`
    : `请综合判断文章时效，优先处理近24小时内发布的文章。`;

  return `# 民商事法律要闻简报任务 v2.4

今日简报日期：${targetDate || date}
${dateInstruction}

待处理文章数量：${articles.length}

## 薛龙律师 · 六大执业方向

本简报聚焦以下六大方向：
1. 婚姻家事与财富长青（跨境继承、夫妻债务、资产隐匿、意定监护等）
2. 司法强制执行与资产调处（法人人格穿透、拒执罪、执行异议、跨境资产查控等）
3. 企业反舞弊与白领刑事防御（职务侵占、商业贿赂、刑民交叉、合规不起诉等）
4. 公司治理与股权投资争议（对赌回购、股权代持、控制权争夺、股东代表诉讼等）
5. 商事仲裁与复杂争议解决（新能源供应链、建设工程EPC、跨境贸易、情势变更等）
6. 现代农业与异宠特种贸易（异宠繁育合规、濒危物种许可、特种养殖交易纠纷等）

## 筛选与提炼规则

### 第一步：行业相关度过滤
- 必须是上述六大方向相关的民商事典型案例或合规指引
- 必须过滤：领导调研、党建活动、行政会议、法官表彰、通知通告、刑事/行政诉讼类宣传稿

### 第二步：价值评估（以下任一命中则入选）
- 是否有创新的裁判口径或裁判规则变化？
- 是否涉及六大执业方向的重大行业风险？
- 是否能作为向企业主/高净值客户开拓案源的切入点？
- 是否对在办案件有直接参考价值？

## 输出格式（每条入选文章 · 高信息密度版）

每条入选文章必须按照以下完整结构输出，**不设字数上限，以说清为准**：

【序号】《文章原标题》
📂 来源：公众号名称
📅 发布日期：YYYY-MM-DD
🔗 链接：URL

🎯 争议焦点
（请详细说明：案件背景事实是什么、双方当事人各自的立场和诉求、
 争议的核心法律问题是什么、实务中常见的分歧点在哪里。
 请充分展开，不要一句话带过。）

⚖️ 法院/仲裁裁判
（请详细说明：法院或仲裁委的裁判逻辑链条、关键法律适用、
 对争议焦点的逐一回应、证据认定标准、说理脉络。
 如有不同审级观点差异，请分组说明。
 如有创新裁判口径，请重点标出。）

💼 应用场景与案源价值
（请详细分析：该裁判口径对薛龙律师六大执业方向中哪类客户有直接影响，
 可转化为何种具体的法律服务产品或专项服务方案，
 可与哪个已有在办案件形成关联参照，
 如何向潜在客户沟通该话题并开拓案源。）

### 最终输出结构
1. 用中文输出简报正文，格式如下：
---
🤖 WorkBuddy 今日法律要闻简报（${targetDate || date}）

[逐条列出入选文章，每条按上述详细格式展开]

📌 今日共检索文章 ${articles.length} 篇，入选 X 篇 | 六大方向覆盖：方向1·方向2·方向3
---
2. 然后另起一行，输出一个 JSON 代码块：
\`\`\`json
{
  "date": "${targetDate || date}",
  "total_fetched": ${articles.length},
  "selected": [
    {
      "index": 1,
      "title": "...",
      "source": "...",
      "url": "...",
      "focus": "争议焦点详细说明",
      "ruling": "法院/仲裁裁判详细说明",
      "opportunity": "应用场景与案源价值详细说明"
    }
  ],
  "directions_covered": ["方向1", "方向2"]
}
\`\`\`

## 待处理文章列表

${articleList}`;
}

// ─────────────────────────────────────────────
// 命令行参数解析
// ─────────────────────────────────────────────

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--accounts' && argv[i + 1]) {
      args.accounts = argv[i + 1].split(',').map(s => s.trim()).filter(Boolean);
      i++;
    } else if (argv[i] === '--whitelist' && argv[i + 1]) {
      args.whitelist = argv[i + 1].split(',').map(s => s.trim()).filter(Boolean);
      i++;
    } else if (argv[i] === '--date' && argv[i + 1]) {
      args.date = argv[i + 1];
      i++;
    } else if (argv[i] === '--days' && argv[i + 1]) {
      args.days = parseInt(argv[i + 1]) || 1;
      i++;
    } else if (argv[i] === '--output' && argv[i + 1]) {
      args.output = argv[i + 1];
      i++;
    } else if (argv[i] === '--no-filter') {
      args.noFilter = true;
    } else if (argv[i] === '--no-strict-whitelist') {
      args.noStrictWhitelist = true;
    } else if (argv[i] === '--mode' && argv[i + 1]) {
      args.mode = argv[i + 1];
      i++;
    } else if (argv[i] === '--max-per-account' && argv[i + 1]) {
      args.maxPerAccount = parseInt(argv[i + 1]) || 5;
      i++;
    }
  }
  return args;
}

function parseDateArg(dateArg) {
  if (!dateArg) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateArg)) return dateArg;
  if (/^\d{2}-\d{2}$/.test(dateArg)) return `2026-${dateArg}`;
  const n = parseInt(dateArg);
  if (!isNaN(n)) {
    const d = new Date(Date.now() - n * 86400000);
    return d.toISOString().slice(0, 10);
  }
  return null;
}

// ─────────────────────────────────────────────
// 主函数
// ─────────────────────────────────────────────

async function main() {
  const args = parseArgs(process.argv.slice(2));

  let accounts = [];
  if (args.accounts) {
    accounts = args.accounts;
  } else if (args.whitelist) {
    accounts = args.whitelist;
  } else {
    accounts = WHITELIST_ACCOUNTS.length > 0 ? WHITELIST_ACCOUNTS : DEFAULT_ACCOUNTS;
  }

  const mode = args.mode || 'briefing';
  const noFilter = args.noFilter || false;
  const maxPerAccount = args.maxPerAccount || 8;
  const targetDate = parseDateArg(args.date);

  const today = new Date();
  const chinaToday = new Date(today.getTime() + 8 * 3600 * 1000);
  const dateStr = chinaToday.toISOString().slice(0, 10);

  const strictWhitelist = !(args.noStrictWhitelist || false);

  process.stderr.write(`\n=== Legal Briefing v2.4 ===\n`);
  process.stderr.write(`Date: ${targetDate || dateStr}\n`);
  process.stderr.write(`Accounts: ${accounts.length}\n`);
  process.stderr.write(`Max/account: ${maxPerAccount}\n`);
  process.stderr.write(`Suppl keywords: ${SUPPLEMENT_KEYWORDS.length}\n`);
  process.stderr.write(`Strict whitelist: ${strictWhitelist}\n`);
  if (targetDate) process.stderr.write(`Date filter: ${targetDate}\n`);
  process.stderr.write('\n');

  let allArticles = [];

  // 1. 白名单公众号搜索（Tier 1 · 来源保证为白名单账号）
  for (const account of accounts) {
    process.stderr.write(`[Account·Tier1] ${account}\n`);
    try {
      const results = await searchWechat(account, maxPerAccount);
      results.forEach(a => a._tier = 1);
      process.stderr.write(`  -> ${results.length} articles\n`);
      allArticles.push(...results);
      await sleep(800 + Math.random() * 600);
    } catch (err) {
      process.stderr.write(`  -> Failed: ${err.message}\n`);
    }
  }

  // 2. 六大方向补充关键词搜索（Tier 2 · 白名单优先模式下仅用于发现白名单账号遗漏的文章）
  for (const kw of SUPPLEMENT_KEYWORDS) {
    process.stderr.write(`[Keyword·Tier2] ${kw}\n`);
    try {
      const results = await searchWechat(kw, 5);
      results.forEach(a => a._tier = 2);
      process.stderr.write(`  -> ${results.length} articles\n`);
      allArticles.push(...results);
      await sleep(700 + Math.random() * 500);
    } catch (err) {
      process.stderr.write(`  -> Failed: ${err.message}\n`);
    }
  }

  process.stderr.write(`\nTotal fetched: ${allArticles.length}\n`);
  const t1 = allArticles.filter(a => a._tier === 1).length;
  const t2 = allArticles.filter(a => a._tier === 2).length;
  process.stderr.write(`Tier1 (whitelist accounts): ${t1} | Tier2 (supplement keywords): ${t2}\n`);

  // 3. 日期过滤（v2.4：默认今日，不足时自动放宽到最近 3 天）
  let dateWindow = [dateStr];
  if (targetDate) {
    // 如果指定了日期参数，严格控制
    allArticles = allArticles.filter(a => a.datetime === targetDate);
    process.stderr.write(`Date filter (${targetDate}): ${allArticles.length}\n`);
  } else {
    // 默认：保留今日 + 最近 2 天（共 3 天窗口）
    // 注意：datetime 解析失败的（null/空）予以保留，排序时放后面
    const d = new Date(chinaToday);
    const dates = [dateStr];
    for (let i = 1; i <= 2; i++) {
      d.setDate(d.getDate() - 1);
      dates.push(d.toISOString().slice(0, 10));
    }
    dateWindow = dates;
    const beforeDateFilter = allArticles.length;
    allArticles = allArticles.filter(a => {
      if (!a.datetime) return true; // 日期解析失败，保留
      return dates.includes(a.datetime);
    });
    process.stderr.write(`Date filter (${dates.join(', ')} + unknown dates): ${beforeDateFilter} -> ${allArticles.length}\n`);
  }

  // 4. 去重
  allArticles = dedup(allArticles);
  process.stderr.write(`After dedup: ${allArticles.length}\n`);

  // 5. 法务筛选 + 来源优先级排序（v2.4 重构）
  let filtered = [];
  if (noFilter) {
    filtered = allArticles;
  } else {
    // 5.1 严格筛选：必须命中 INCLUDE_KEYWORDS + 通过 EXCLUDE_KEYWORDS
    const strictPool = allArticles.filter(a => legalFilter(a));
    process.stderr.write(`Strict filter (hit INCLUDE_KEYWORDS): ${strictPool.length}\n`);

    // 5.2 按来源优先级排序
    strictPool.sort((a, b) => {
      const pa = getSourcePriority(a.source);
      const pb = getSourcePriority(b.source);
      if (pa !== pb) return pa - pb;
      // 同优先级：今日文章优先，其次按发布时间倒序
      const da = a.datetime ? dateWindow.indexOf(a.datetime) : 999;
      const db = b.datetime ? dateWindow.indexOf(b.datetime) : 999;
      if (da !== db) return da - db;
      return (b.datetime || '').localeCompare(a.datetime || '');
    });

    if (strictPool.length >= 10) {
      filtered = strictPool;
      process.stderr.write(`Strict pool sufficient (${strictPool.length} >= 10)\n`);
    } else {
      // 5.3 放宽筛选：仅标题命中 INCLUDE_KEYWORDS（不要求摘要也命中）
      process.stderr.write(`Strict pool < 10 (${strictPool.length}), relaxing filter...\n`);
      const relaxedPool = allArticles.filter(a => {
        if (strictPool.includes(a)) return true; // 已严格筛选的保留
        // 放宽条件：标题命中即通过（不检查摘要）
        const title = a.title || '';
        for (const kw of INCLUDE_KEYWORDS) {
          if (title.includes(kw)) return true;
        }
        return false;
      });
      relaxedPool.sort((a, b) => {
        const pa = getSourcePriority(a.source);
        const pb = getSourcePriority(b.source);
        if (pa !== pb) return pa - pb;
        const da = a.datetime ? dateWindow.indexOf(a.datetime) : 999;
        const db = b.datetime ? dateWindow.indexOf(b.datetime) : 999;
        if (da !== db) return da - db;
        return (b.datetime || '').localeCompare(a.datetime || '');
      });
      process.stderr.write(`Relaxed filter (title hit): ${relaxedPool.length}\n`);

      if (relaxedPool.length >= 10) {
        filtered = relaxedPool;
      } else {
        // 5.4 进一步放宽：允许来源好的文章直接通过（不检查关键词）
        process.stderr.write(`Relaxed pool < 10 (${relaxedPool.length}), further relaxing...\n`);
        const furtherRelaxedPool = allArticles.filter(a => {
          if (relaxedPool.includes(a)) return true;
          // 来源为法院/仲裁/白名单律所，即使关键词未命中也保留
          const src = (a.source || '').trim();
          return isCourtSource(src) || isArbitrationSource(src) || isWhitelistSource(src);
        });
        furtherRelaxedPool.sort((a, b) => {
          const pa = getSourcePriority(a.source);
          const pb = getSourcePriority(b.source);
          if (pa !== pb) return pa - pb;
          const da = a.datetime ? dateWindow.indexOf(a.datetime) : 999;
          const db = b.datetime ? dateWindow.indexOf(b.datetime) : 999;
          if (da !== db) return da - db;
          return (b.datetime || '').localeCompare(a.datetime || '');
        });
        process.stderr.write(`Further relaxed filter (good source): ${furtherRelaxedPool.length}\n`);
        filtered = furtherRelaxedPool;
      }
    }
  }
  process.stderr.write(`After legal filter: ${filtered.length}\n`);

  // 6. 每个公众号每天最多入选篇数规则（v2.4）
  //    法院/仲裁账号：最多 2 篇/天
  //    其他账号（律所/机构等）：最多 1 篇/天
  const seenSourceDate = new Map(); // key: source::date, value: count
  filtered = filtered.filter(a => {
    const dateKey = a.datetime || 'unknown';
    const sourceKey = (a.source || '未知').trim();
    const key = `${sourceKey}::${dateKey}`;
    const current = seenSourceDate.get(key) || 0;

    // 判断是否为法院/仲裁账号
    const isCourtOrArb = isCourtSource(sourceKey) || isArbitrationSource(sourceKey);
    const maxPerDay = isCourtOrArb ? 2 : 1;

    if (current >= maxPerDay) return false;
    seenSourceDate.set(key, current + 1);
    return true;
  });
  process.stderr.write(`After source-date dedup (court/arb≤2, others≤1): ${filtered.length}\n`);

  // 7. 最终取前 10 篇
  filtered = filtered.slice(0, 10);
  process.stderr.write(`Final top ${filtered.length} selected\n\n`);

  if (filtered.length === 0) {
    process.stderr.write('WARNING: 0 articles passed filter, using top 15 raw results\n');
    filtered = allArticles.slice(0, 15);
  }

  if (mode === 'raw') {
    const output = {
      date: targetDate || dateStr,
      total_fetched: allArticles.length,
      filtered_count: filtered.length,
      articles: filtered,
    };
    const json = JSON.stringify(output, null, 2);
    if (args.output) {
      fs.writeFileSync(args.output, json, 'utf-8');
      process.stderr.write(`Saved to ${args.output}\n`);
    }
    console.log(json);
  } else {
    const prompt = buildBriefingPrompt(filtered, dateStr, targetDate);
    if (args.output) {
      fs.writeFileSync(args.output, prompt, 'utf-8');
      process.stderr.write(`Prompt saved to ${args.output}\n`);
    }
    console.log(prompt);
  }
}

main().catch(err => {
  process.stderr.write(`Fatal: ${err.message}\n`);
  process.exit(1);
});
