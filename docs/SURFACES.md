# Google Trends 全部可爬取数据面目录（穷举）

> 调研与验证日期：2026-10-06
> 这是"全部可爬取内容"的清单，不是常用功能子集。每条都给出端点、参数、返回字段、粒度、来源依据与实测状态。
> 端点依据：trendspy 0.1.6 / trendspyg 1.9.0 / pytrends 4.9.2 已安装源码逐行核对 + Google 官方文档 + 实测探测。
> 实测状态列由 `scripts/demo_snapshot.py` 的 `out/probes.json` 回填（`ok` / `error` / `application_only` / `browser_only`）。

## 分组速览

| 组 | 数据面数 | 说明 |
|---|---|---|
| Explore | 5 | 相对兴趣曲线、多时间窗、区域地图、相关查询、相关主题 |
| Metadata | 2 | 分类树、全量地理编码 |
| Autocomplete | 1 | 搜索框联想/实体消歧 |
| Trending | 7 | 页面实时趋势、CSV 大表、旧 API×2、Hot Trends、RSS×2 |
| Charts | 2 | Top Charts API、Year in Search 页面 |
| Official | 3 | BigQuery 公共数据集、GoogleTrends/data、Trends API alpha |
| Page Export | 1 | Explore 页 CSV 导出 |
| **合计** | **21** | 其中脚本内核可直连 16 面、浏览器 2 面、官方应用/凭据 3 面 |

## 当前状态速查（2026-10-06 实测）

| 数据面 | 端点 | 状态 |
|---|---|---|
| Interest Over Time | `/api/explore` + `/api/widgetdata/multiline` | ✅ 可用 |
| Multirange | `/api/widgetdata/multirange` | ✅ 可用 |
| Interest by Region | `/api/widgetdata/comparedgeo` | ✅ 可用（受限流） |
| Related Queries | `/api/widgetdata/relatedsearches`（QUERY） | ✅ 可用（受限流） |
| Related Topics | `/api/widgetdata/relatedsearches`（ENTITY） | ✅ 可用 |
| Categories | `/api/explore/pickers/category` | ✅ 可用 |
| Geo Pickers | `/api/explore/pickers/geo` | ✅ 可用 |
| Autocomplete | `/api/autocomplete/<kw>` | ✅ 可用 |
| Trending Now | `/_/TrendsUi/data/batchexecute`（i0OFE） | ✅ 可用 |
| Trending Now CSV | 浏览器页面导出 | 🔶 浏览器依赖 |
| Realtime Trends API（旧） | `/api/realtimetrends` | ❌ 2026-10-06 404 |
| Daily Trends API（旧） | `/api/dailytrends` | ❌ 2026-10-06 404 |
| Hot Trends（旧） | `/hottrends/visualize/internal/data` | ❌ 2026-10-06 404 |
| Daily RSS（旧路径） | `trendingsearches/daily/rss` | ❌ 已迁移到 `trending/rss` |
| Realtime RSS | `trending/rss?geo=` | ✅ 可用 |
| Top Charts | `/api/topcharts` | ❌ 2026-10-06 404 |
| Year in Search 页面 | `trends/yis/YYYY/GEO` | 🔶 JS 渲染/浏览器 |
| BigQuery | `bigquery-public-data.google_trends` | 🔶 需 GCP 凭据 |
| GoogleTrends/data | GitHub 仓库 | ✅ 可用（266 CSV） |
| Trends API alpha | `developers.google.com/search/apis/trends` | 🔶 申请制 |
| Explore CSV 导出 | Explore 页面 | 🔶 手动/浏览器 |

## 一、Explore 系（相对兴趣，0-100）

### 1. Interest Over Time（相对兴趣曲线）
- 端点：`/trends/api/explore`（拿 token）→ `/trends/api/widgetdata/multiline`
- 参数：`keywords[]`、`timeframe`、`geo`、`cat`、`gprop`
- 粒度：窗口 <5h=1分钟；5-36h=8分钟；36-72h=16分钟；72h-8d=1小时；8d-270d=1日；270d-1900d=1周；>=1900d=1月（trendspy `timeframe_utils`）
- 字段：`time`、`formattedTime`、`value[]`、`isPartial`
- 来源：trendspy `client.py:323-382`；pytrends `request.py:221-272`
- 验证：实测可用

### 2. Multirange Interest Over Time（多时间窗合并）
- 端点：`/api/widgetdata/multirange`
- 参数：`keywords[]`、`timeframes[]`（每词可不同时间窗）、`geo`、`cat`、`gprop`
- 字段：`formattedAxisTime`、`columnData[].formattedTime/value`、`averages`
- 来源：pytrends `request.py:274-315`；trendspy `client.py:379-381`
- 验证：待实测（脚本已接）

### 3. Interest by Region（地图/区域兴趣）
- 端点：`/api/widgetdata/comparedgeo`
- 参数：`keywords[]`、`timeframe`、`geo`、`resolution`（`COUNTRY`/`REGION`/`DMA`/`CITY`）、`includeLowSearchVolumeGeos`
- 字段：`geoName`、`geoCode`、`coordinates`、`value[]`
- 来源：pytrends `request.py:317-368`；trendspy `client.py:450-480`
- 验证：实测可用（受限流）

### 4. Related Queries（相关查询 Top+Rising）
- 端点：`/api/widgetdata/relatedsearches`
- 参数：`keyword`、`timeframe`、`geo`、`cat`、`gprop`
- 字段：`query`、`value`、`rank`、`link`
- 来源：pytrends `request.py:418-465`；trendspy `client.py:384-417`
- 验证：实测可用（受限流）

### 5. Related Topics（相关主题/实体 Top+Rising）
- 端点：`/api/widgetdata/relatedsearches`（RELATED_TOPICS widget）
- 参数：同 Related Queries
- 字段：`topic.mid`、`topic.title`、`topic.type`、`value`、`rank`、`link`
- 来源：pytrends `request.py:370-417`；trendspy `client.py:418-449`
- 验证：实测可用

## 二、元数据（自动化全覆盖必需品）

### 6. Categories（Explore 分类树）
- 端点：`/api/explore/pickers/category`
- 参数：`hl`
- 字段：`children[].id/name/children`
- 来源：pytrends `request.py:574-585`；trendspyg `compat/request.py:70,564-566`
- 用途：`cat` 过滤 Explore 全部数据面

### 7. Geo Pickers（全部地理编码）
- 端点：`/api/explore/pickers/geo`
- 参数：`hl`、`tz`
- 字段：嵌套 `children[].id/name`
- 来源：trendspy `client.py:664-711`（`geo()`）

## 三、联想 / 实体消歧

### 8. Autocomplete / Suggestions
- 端点：`/api/autocomplete/<kw>`
- 参数：`keyword`、`hl`
- 字段：`title`、`type`、`mid`、`base_rank`
- 来源：pytrends `request.py:559-572`；trendspyg `keywords.py:15,42`

## 四、Trending 系（实时/每日热搜）

### 9. Trending Now（页面实时趋势列表）
- 端点：`/_/TrendsUi/data/batchexecute`，RPC `i0OFE`
- 参数：`geo`、`language`、`hours`(1..191)、`num_news`、`version`
- 字段：`keyword`、`news`、`geo`、`started_timestamp`、`ended_timestamp`、`volume`、`volume_growth_pct`、`trend_keywords`、`topics`、`news_tokens`、`normalized_keyword`
- 来源：trendspy `client.py:42,314-321,546-577`
- 验证：实测可用（328-336 条）

### 10. Trending Now CSV 导出（大表）
- 途径：浏览器打开 `https://trends.google.com/trending?geo=&hours=&category=` 下载 CSV
- 参数：`geo`、`hours`(4/24/48/168)、`category`、`active_only`、`sort`、`max_retries`
- 数据规模：约 480 条/窗口；时间窗 4h/24h/48h/7d；分类含 sports/tech 等
- 字段：`Trend`、`Volume`、`Explore link`、`Started at`、`Ends at`、`Trending searches`、`Category`、`Image`、`Article`
- 来源：trendspyg `downloader.py:349-482`（`download_google_trends_csv`）
- 验证：本机未安装 Chrome，走 `browser_only`

### 11. Realtime Trends API（旧实时）
- 端点：`/api/realtimetrends`
- 参数：`geo`、`cat`(all/b/e/m/t/s/h)、`ri/rs`、`sort`
- 字段：`storySummaries.trendingStories[]`：`entityNames/title/image/articles/metrics`
- 来源：trendspy `client.py:506-520`；pytrends `request.py:495-529`
- 验证：❌ 2026-10-06 实测 404，当前下线

### 12. Daily Trends API（旧每日）
- 端点：`/api/dailytrends`
- 参数：`geo`、`hl`、`tz`
- 字段：`default.trendingSearchesDays[]` → `trendingSearches[]`
- 来源：trendspy `client.py:522-531`
- 验证：❌ 2026-10-06 实测 404，当前下线

### 13. Hot Trends（各国今日热门）
- 端点：`/hottrends/visualize/internal/data`
- 字段：按国家键返回热门搜索数组
- 来源：pytrends `request.py:29,468-481（trending_searches）`
- 验证：❌ 2026-10-06 实测 404，当前下线；改用 Trending Now / RSS

### 14. Daily Search Trends RSS（旧路径）
- 端点：`https://trends.google.com/trends/trendingsearches/daily/rss?geo=US`
- 参数：`geo`、`safe`
- 字段：`title`、`link`、`ht:approx_traffic`、`ht:news_item`
- 来源：trendspy `client.py:69,533-544`
- 验证：❌ 旧路径 2026-10-06 实测 404；2025-03 社区帖证实已迁移到 `trending/rss`

### 15. Realtime Search Trends RSS
- 端点：`https://trends.google.com/trending/rss?geo=US`
- 参数：`geo`
- 字段：RSS 标题/链接/近似流量/新闻
- 来源：trendspy `client.py:70,579-602`；trendspyg `rss_downloader.py:562`
- 验证：实测可用（10 条）

## 五、Top Charts / Year in Search

### 16. Top Charts API（年度排行榜）
- 端点：`/api/topcharts`
- 参数：`date`(YYYY)、`geo`、`isMobile`
- 字段：`topCharts[0].listItems[]`
- 来源：pytrends `request.py:533-557`；trendspy `client.py:496-504`
- 验证：❌ 2026-10-06 实测 404；与 trendspyg 源码注释一致

### 17. Year in Search 页面
- 端点：`https://trends.google.com/trends/yis/YYYY/GEO/`
- 字段：年度榜单可视化（与 top_charts 同源）
- 验证：🔶 JS 渲染/浏览器

## 六、官方数据面

### 18. BigQuery 公共数据集
- 数据集：`bigquery-public-data.google_trends`
- 表与范围：
  - `top_terms` / `top_rising_terms`：美国日粒度，210 DMA，滚动 5 年
  - 美国小时粒度（6h/4x daily），滚动 1 年
  - `international_top_terms` / `international_top_rising_terms`：约 50 国 ISO 国家码 + 子区域，日粒度滚动 5 年
- 字段：`refresh_date`、`dma`/`region`、`term`、`rank`、`score`、`percent_gain`
- 官方支持页：https://support.google.com/trends/answer/12764470 （2026-10-06 抓取）
- 验证：`bigquery_meta` 可描述；实际查询需 `google-cloud-bigquery` + GCP 凭据

### 19. GoogleTrends/data（官方开源策展数据集）
- 仓库：https://github.com/GoogleTrends/data （master 分支）
- 内容：2026-10-06 实测下载到 **266 个 CSV**（选举、体育、品牌、事件、城市/州级兴趣等），另有 `.xlsx` 样例
- 途径：GitHub API 列文件 → raw CSV 下载
- 验证：实测列表与下载均可用

### 20. Trends API alpha（官方申请制）
- 文档：https://developers.google.com/search/apis/trends
- 能力（官方文档，2026-10-06 抓取）：日/周/月/年聚合、国家/子区域、约 5 年（1800 天）滚动、consistently scaled（可跨请求合并/拼接）、最多几十个词
- 验证：`application_only`；脚本保留接入占位

## 七、页面导出

### 21. Explore 页 CSV 导出
- 途径：`https://trends.google.com/trends/explore?q=...` 页面原生 CSV 下载按钮
- 字段：`day`、`keyword`、`interest`
- 验证：`browser_only`（可用浏览器自动化复现）

## 八、已确认不可爬/需条件的“非数据面”

| 内容 | 原因 |
|---|---|
| 绝对搜索量（某词某日具体次数） | 官方口径：Trends 提供归一化相对兴趣，不是绝对 volume |
| 用户级/明细级搜索记录 | 匿名聚合，官方不提供原始日志 |
| 全部 BigQuery 历史分区（超过 TTL） | 官方分区 TTL 30 天，历史只通过滚动窗口 |
| Top Charts 历史年份完整榜单 | 2026-10-06 实测 `topcharts` 404 |
| 官方 API alpha 全部端点 | 申请制，需 Google 授权 token |
| Explore/DMA 细到某些分辨率 | 官方 Explore 只支持 metro/subregion；DMA 仅 BigQuery 语境 |

## 九、工具与来源对照

| 数据面 | trendspy | trendspyg | pytrends | 本项目 |
|---|---|---|---|---|
| interest over time | `interest_over_time` | explore | `interest_over_time` | `explore.interest_over_time` |
| multirange | `interest_over_time`(list) | explore | `multirange_interest_over_time` | `explore.multirange_interest_over_time` |
| region | `interest_by_region` | explore | `interest_by_region` | `explore.interest_by_region` |
| related | `related_queries/topics` | explore | `related_queries/topics` | `explore.related_queries/topics` |
| categories/geo | `categories()/geo()` | `categories()` | `categories()` | `meta.categories/geo` |
| autocomplete | `suggestions` | `suggest_keywords` | `suggestions` | `autocomplete.suggestions` |
| trending now | `trending_now` | watch/CSV | trending RSS compat | `trending.trending_now` |
| top charts | `top_year_charts` | not available | `top_charts` | `topcharts.top_charts` |
| RSS | `daily_trends_deprecated_by_rss`/`trending_now_by_rss` | `download_google_trends_rss` | - | `trending.rss_daily/rss_realtime` |

## 十、验证方法

- 全数据面探测：`python scripts/demo_snapshot.py`
- 输出：`out/probes.json` + `out/probes-<surface>.json`
- 每个面记录：`status / record_count / elapsed_s / error / sample`
- 注意：Google 对内部端点会 429 长封；如遇 `/sorry/index` 按 `RateLimitedError` 处理，**不要**用替换 IP 轮询规避。