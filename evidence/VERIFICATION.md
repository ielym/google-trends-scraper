# 2026-10-06 Google Trends 数据面实测验证记录

> 这是 `scripts/demo_snapshot.py` + 独立 HTTP 状态探测的结果汇总。
> 目的：**区分"端点已下线""端点限流""端点可用"**，避免把旧库里的老 URL 当成当前可爬面。

## 一、探测环境

- 日期：2026-10-06
- 出口：v2rayN 本地代理 `http://127.0.0.1:10808`（非 Google 官方数据渠道）
- 库版本：trendspy 0.1.6 / trendspyg 1.9.0 / pytrends 4.9.2（读取源码枚举端点）
- 方法：HTTP GET 状态码 + 正文特征（`/sorry/index` 视为限流）；运行时产物见 `out/probes.json`

## 二、结果分级

| 状态 | 含义 |
|---|---|
| ok | 端点返回数据，样本已落盘 |
| rate_limited | HTTP 429 或 `/sorry/index`；端点本身存在，当前出口被限流 |
| error/404 | 当前该 URL 返回 404；大概率已下线或迁移 |
| application_only | 官方声明需申请/凭据，不适用于匿名抓取 |
| browser_only | 需要浏览器自动化（Chrome）或 UI 导出 |

## 三、逐面结果（二次完整探测，17 面中 12 ok、5 个 404 下线）

| 数据面 | 状态 | 证据 |
|---|---|---|
| interest_over_time | ok | `/api/widgetdata/multiline` 返回 JSON |
| related_queries | ok（二次探测） | `relatedsearches`（QUERY widget）返回 |
| related_topics | ok | `relatedsearches`（ENTITY widget）返回 |
| interest_by_region | ok（二次探测） | `comparedgeo`（REGION resolution）返回 |
| autocomplete | ok | `/api/autocomplete/<kw>` 返回 5 条建议 |
| categories | ok | `/api/explore/pickers/category` 展开 1426 节点 |
| geo_pickers | ok | `/api/explore/pickers/geo` 展开 3681 节点 |
| trending_now | ok | `batchexecute i0OFE` 返回 328-336 条趋势（首次探测 336，二次 328） |
| realtime_trending | **404 已下线** | `/api/realtimetrends` 404 |
| daily_trends | **404 已下线** | `/api/dailytrends` 404 |
| hot_trends | **404 已下线** | `/hottrends/visualize/internal/data` 404 |
| rss_daily（旧路径） | **404 已下线** | `trendingsearches/daily/rss` 404；2025-03 社区帖证实迁移 |
| rss_realtime | ok | `trending/rss?geo=US` 200，10 条 |
| top_charts | **404 已下线** | `/api/topcharts` 404；trendspyg 源码注释印证 |
| datastore | ok | GitHub API 顶层枚举 266 CSV |
| bigquery_meta | ok | 官方支持页确认表名/范围 |
| official_api_alpha | application_only | `developers.google.com/search/apis/trends`（2026-10-06 可访问） |

另有 4 面未纳入匿名探测（前置条件）：trending_now_csv / yis_page / explore_csv_export（browser_only）、BigQuery 查询（需凭据）。

## 四、关键事实核对（外部来源）

1. **Daily RSS 迁移**：note.com 2025-03-08（https://note.com/maru2501/n/n4afd658a00a1）：旧 `https://trends.google.co.jp/trends/trendingsearches/daily/rss?geo=JP` 已 404，新地址为 `https://trends.google.co.jp/trending/rss?geo=JP`。本项目 2026-10-06 实测旧路径 404、新路径 200，一致。
2. **Top Charts 下线**：trendspyg 1.9.0 `compat/request.py:625-632` 源码注释明确"Google no longer serves the Year in Search endpoint it used ... answers HTTP 404"；本项目实测 `/api/topcharts` 404，一致。
3. **Trends API alpha**：官方文档 https://developers.google.com/search/apis/trends （2026-10-06 可访问）确认申请制 alpha、5 年滚动（1800 天）、日/周/月/年、区域/子区域、consistently scaled、可比数十词。旧的 `trends.google.com/trends/documentation` 页面 404，官方入口以 Developers 页为准。
4. **Explore 相对语义**：官方帮助确认 0-100 为相对占比，非绝对量；支持精确字符串/布尔运算/复数变体规则（support.google.com/trends/answer/4359582）。

## 五、对"全部可爬取"的结论

当前（2026-10-06）匿名可稳定抓取的官方/半官方数据面：

- **Explore widgetdata 系**（interest_over_time / multirange / region / related queries / topics）：仍可用，但受 429 限流。
- **Trending Now 页内 RPC**（batchexecute i0OFE）：可用，字段比 RSS 丰富（volume、趋势关键词、topic/news tokens）。
- **实时 RSS** `trending/rss?geo=`：可用，作为 Trending Now 的轻量替代。
- **官方开源数据集**：GoogleTrends/data GitHub CSV（266 个）、BigQuery 公共数据集（需 GCP 凭据）。
- **官方 API alpha**：申请制，匿名不可用。
- **已被 Google 下线/迁移的旧面**：realtimetrends、dailytrends、hottrends、topcharts、旧 daily RSS 路径。

因此，任何按 trendspy/pytrends 旧源码"全量抓取"的方案都必须在启动时做端点健康检查，否则大部分旧 Trending/Charts 端点只是历史代码。