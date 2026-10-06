# gt-scraper：Google Trends 全量数据面抓取工具

一个面向 **“Google Trends 全部可爬取数据面”** 的 Python 抓取项目，而不是只封装“常用功能”。

项目把 Google Trends 的公开/半公开数据入口分成 21 个数据面，并逐个给出端点、参数、返回字段、粒度与 2026-10-06 实测可用状态。代码、注册表、文档共用同一份端点清单，避免“文档说一套、代码跑另一套”。

---

## 目录

- [为什么做这个项目](#为什么做这个项目)
- [特性](#特性)
- [项目结构](#项目结构)
- [数据面全景（21 个）](#数据面全景21-个)
- [安装](#安装)
- [快速开始](#快速开始)
- [CLI 用法](#cli-用法)
- [Python API 用法](#python-api-用法)
- [配置](#配置)
- [输出格式](#输出格式)
- [实测验证](#实测验证)
- [合规与反爬](#合规与反爬)
- [已知限制](#已知限制)
- [开发与测试](#开发与测试)
- [License](#license)

---

## 为什么做这个项目

Google Trends 没有面向公众的稳定 REST API（官方 alpha 需申请），但多年积累了大量“事实上可爬取”的数据入口：

- Explore 页背后的 widgetdata 接口：兴趣曲线、区域地图、相关查询、相关主题；
- Trending Now 页内 RPC：实时热搜及其流量、趋势关键词、相关话题；
- 官方 RSS：实时趋势 feed；
- 官方 BigQuery 公共数据集、官方 GitHub Datastore；
- 历史库（trendspy / trendspyg / pytrends）中遗留的旧端点。

很多教程只教你“pytrends 五个函数”，但旧库里的 `realtimetrends`、`dailytrends`、`topcharts`、旧 daily RSS 等端点已经下线。这个项目把“全量可爬取内容”整理成可运行、可审计、可持续更新的清单。

## 特性

- **全数据面注册表**：21 个数据面统一登记在 `gt_scraper/registry.py`，与 `docs/SURFACES.md` 一一对应。
- **真实端点实现**：Endpoint 清单来自已安装库源码逐行核对 + 官方文档 + 实测探测，不是记忆拼凑。
- **统一 HTTP 客户端**：cookie、代理、XSSI 剥离、429 识别、指数退避、JSON/XML 解析。
- **标准输出信封**：每次抓取都带 `source / surface / captured_at / params / status / records`。
- **CLI + Python API 双入口**：既能一行命令抓取，也能在代码里组合调用。
- **官方面也覆盖**：BigQuery 表清单与示例 SQL、官方 API alpha 接入占位、GoogleTrends/data 官方 Datastore 下载器。
- **实测证据入库**：`evidence/VERIFICATION.md` 记录“哪些端点当前活着、哪些已 404”。

## 项目结构

```text
google-trends-scraper/
├─ README.md                 # 本文档
├─ pyproject.toml            # 打包/依赖/入口元数据
├─ requirements.txt          # 最小运行依赖
├─ config.example.json       # 配置模板（代理、时区、重试、GitHub、BigQuery）
├─ LICENSE                   # MIT
├─ .gitignore
├─ gt_scraper/               # 核心抓取包
│  ├─ __init__.py
│  ├─ errors.py              # RateLimitedError / HttpError / ParseError 等
│  ├─ endpoints.py           # 全部端点 URL + 常量
│  ├─ http.py                # 会话、cookie、代理、重试、XSSI 剥离
│  ├─ explore.py             # Interest Over Time / Region / Related / Multirange
│  ├─ trending.py            # Trending Now RPC / RSS / 旧实时 / 旧每日 / Hot
│  ├─ topcharts.py           # Top Charts（当前 404，保留实现）
│  ├─ autocomplete.py        # 联想词
│  ├─ meta.py                # 分类树 / 地理编码
│  ├─ datastore.py           # GoogleTrends/data 官方开源数据集
│  ├─ bigquery.py            # BigQuery 官方公共数据集（可选）
│  ├─ registry.py            # DATA_SURFACES 21 面注册表
│  └─ export.py              # JSON/CSV 落盘
├─ scripts/
│  ├─ demo_snapshot.py       # 全数据面健康探测
│  └─ fetch_all.py           # 按需抓取 CLI
├─ docs/
│  └─ SURFACES.md            # 穷举数据面目录（端点/参数/字段/粒度/来源/状态）
├─ evidence/
│  └─ VERIFICATION.md        # 2026-10-06 实测验证记录
├─ data/                     # 运行时缓存（gitignored）
└─ out/                      # 抓取输出（gitignored）
```

## 数据面全景（21 个）

| # | 组 | 数据面 | 端点/途径 | 当前状态 |
|---|---|---|---|---|
| 1 | Explore | Interest Over Time | `/api/explore` + `/api/widgetdata/multiline` | ✅ 可用 |
| 2 | Explore | Multirange Interest Over Time | `/api/widgetdata/multirange` | 🔶 可调用（待单独实测） |
| 3 | Explore | Interest by Region | `/api/widgetdata/comparedgeo` | ✅ 可用（受限流） |
| 4 | Explore | Related Queries | `/api/widgetdata/relatedsearches` | ✅ 可用（受限流） |
| 5 | Explore | Related Topics | `/api/widgetdata/relatedsearches` | ✅ 可用 |
| 6 | Metadata | Categories 分类树 | `/api/explore/pickers/category` | ✅ 可用 |
| 7 | Metadata | Geo Pickers 全部地理编码 | `/api/explore/pickers/geo` | ✅ 可用 |
| 8 | Autocomplete | 联想词/实体消歧 | `/api/autocomplete/<kw>` | ✅ 可用 |
| 9 | Trending | Trending Now（页内 RPC） | `/_/TrendsUi/data/batchexecute` | ✅ 可用 |
| 10 | Trending | Trending Now CSV 大表 | 浏览器导出 | 🔶 需 Chrome |
| 11 | Trending | 实时 RSS | `trending/rss?geo=` | ✅ 可用 |
| 12 | Trending | 每日 RSS（旧路径） | `trendingsearches/daily/rss` | ❌ 已迁移 |
| 13 | Trending | 实时 API（旧） | `/api/realtimetrends` | ❌ 404 |
| 14 | Trending | 每日 API（旧） | `/api/dailytrends` | ❌ 404 |
| 15 | Trending | Hot Trends（旧） | `/hottrends/visualize/internal/data` | ❌ 404 |
| 16 | Charts | Top Charts | `/api/topcharts` | ❌ 404 |
| 17 | Charts | Year in Search 页面 | `trends/yis/YYYY/GEO` | 🔶 JS/浏览器 |
| 18 | Official | BigQuery 公共数据集 | `bigquery-public-data.google_trends` | 🔶 需 GCP |
| 19 | Official | GoogleTrends/data Datastore | GitHub 仓库 | ✅ 可用（266 CSV） |
| 20 | Official | Trends API alpha | `developers.google.com/search/apis/trends` | 🔶 申请制 |
| 21 | Page Export | Explore CSV 导出 | Explore 页面 | 🔶 浏览器 |

完整字段、参数、粒度、来源证据见 [docs/SURFACES.md](docs/SURFACES.md)。

## 安装

```bash
# 基础依赖
pip install -r requirements.txt

# 或完整安装（含 CLI 入口）
pip install -e .
```

可选依赖：

```bash
pip install google-cloud-bigquery   # BigQuery 查询
pip install selenium                # Trending Now CSV 浏览器导出
```

Python 要求：`>=3.9`。

## 快速开始

```bash
# 1) 全数据面健康探测（会真实请求 Google）
python scripts/demo_snapshot.py

# 2) 按需抓取：兴趣曲线 + 相关查询 + Trending Now + 实时 RSS
python scripts/fetch_all.py \
  --surfaces iot,related_queries,trending_now,rss_realtime \
  --kw "chatgpt" \
  --geo US \
  --timeframe "today 12-m" \
  --out out/fetch
```

Windows PowerShell 下的代理示例：

```powershell
$env:GT_PROXY = "http://127.0.0.1:10808"
python scripts/fetch_all.py --surfaces rss_realtime --geo US --out out/fetch
```

## CLI 用法

```bash
python scripts/fetch_all.py \
  --surfaces <surface1,surface2,...|all> \
  [--kw KEYWORD] [--timeframe TIMEFRAME] [--geo GEO] \
  [--category N] [--gprop ''|images|news|youtube|froogle] \
  [--resolution COUNTRY|REGION|DMA|CITY] \
  [--hours HOURS] [--category_name all|b|e|m|t|s|h] \
  [--year YYYY] [--out DIR] [--config config.json] [--direct] [--limit N]
```

常用参数说明：

| 参数 | 默认 | 说明 |
|---|---|---|
| `--surfaces` | 必填 | 逗号分隔的数据面 ID；`all` 跑全部非浏览器面 |
| `--kw` | `chatgpt` | 关键词，可逗号分隔（Explore 系支持多词） |
| `--timeframe` | `today 12-m` | `now 1-H` / `today 5-y` / `YYYY-MM-DD YYYY-MM-DD` / `all` |
| `--geo` | 空 | 国家代码，如 `US`、`GB`、`US-CA` |
| `--category` | `0` | Explore 分类 ID（`categories` 面可枚举） |
| `--gprop` | 空 | 网页/图片/新闻/YouTube/Froogle 过滤 |
| `--resolution` | `COUNTRY` | 区域地图粒度 |
| `--hours` | `24` | Trending Now 窗口（1..191） |
| `--category_name` | `all` | 旧实时 API 分类参数（保留） |
| `--year` | `2024` | Top Charts 年份（保留） |
| `--out` | `out/fetch` | 输出目录 |
| `--direct` | 关 | 强制直连（不读代理） |
| `--limit` | 无 | Datastore 下载数量上限 |

可用数据面 ID：

```text
iot, multirange, interest_by_region, related_queries, related_topics,
categories, geo_pickers, autocomplete, trending_now, trending_now_csv,
realtime_trending, daily_trends, hot_trends, rss_daily, rss_realtime,
top_charts, yis_page, bigquery, datastore, official_api_alpha, explore_csv_export
```

## Python API 用法

```python
import sys
sys.path.insert(0, ".")

from gt_scraper.http import HttpClient
from gt_scraper.explore import ExploreClient
from gt_scraper.trending import TrendingClient

http = HttpClient(proxy="http://127.0.0.1:10808", request_delay_s=5)
explore = ExploreClient(http)
trending = TrendingClient(http)

# 兴趣曲线（返回原始 widgetdata JSON）
iot = explore.interest_over_time(["chatgpt", "llm"], "today 12-m", "US")

# 区域分布
region = explore.interest_by_region(["chatgpt"], "today 12-m", "US", resolution="REGION")

# 相关查询
related = explore.related_queries("chatgpt", "today 12-m", "US")

# Trending Now（batchexecute i0OFE，约 300+ 条）
trends = trending.trending_now("US", hours=24)

# 实时 RSS
rss = trending.rss_realtime("US")

# 官方 Datastore：先列文件，再下载
from gt_scraper.datastore import DatastoreClient
ds = DatastoreClient()
files = ds.list_csv(pattern=r"COVID|election")[:10]
for f in files:
    print(f["name"])
```

## 配置

默认读取 `config.json`（模板见 [config.example.json](config.example.json)）：

```json
{
  "proxy": "http://127.0.0.1:10808",
  "direct": false,
  "hl": "en-US",
  "tz": 360,
  "request_delay_s": 4.0,
  "max_retries": 3,
  "backoff_s": 8.0,
  "user_agent": "Mozilla/5.0 ...",
  "github": {
    "owner": "GoogleTrends",
    "repo": "data",
    "branch": "master"
  },
  "bigquery": {
    "project": "bigquery-public-data",
    "dataset": "google_trends",
    "tables": [
      "top_terms",
      "top_rising_terms",
      "international_top_terms",
      "international_top_rising_terms"
    ]
  }
}
```

环境变量优先：

| 变量 | 说明 |
|---|---|
| `GT_PROXY` | HTTP 代理（如 `http://127.0.0.1:10808`） |
| `GT_DIRECT` | 非空即直连 |
| `GOOGLE_APPLICATION_CREDENTIALS` | BigQuery 服务账号 JSON（可选） |

## 输出格式

抓取输出统一为 JSON 信封：

```json
{
  "source": "google-trends",
  "surface": "rss_realtime",
  "captured_at": "2026-10-06T12:00:00+00:00",
  "params": {"geo": "US"},
  "status": "ok",
  "error": null,
  "records": []
}
```

- `iot` / `multirange` / `interest_by_region`：`records` 为原始 widgetdata JSON；脚本也会生成 CSV 标准化行。
- `trending_now`：`records` 为已映射字段（keyword / volume / trend_keywords / topics / news_tokens / started_timestamp）。
- `rss_realtime`：`records` 为 RSS 解析后的 item 列表。
- `datastore`：`records` 为下载到的本地文件列表。
- 失败面：`status=error`，`error` 保留异常详情，其余面继续执行。

## 实测验证

2026-10-06 在同一出口用 `scripts/demo_snapshot.py` 完成两轮探测：

| 结果 | 数据面 |
|---|---|
| ✅ 12 个可用 | `iot`、`related_queries`、`related_topics`、`interest_by_region`、`autocomplete`、`categories`、`geo_pickers`、`trending_now`、`rss_realtime`、`datastore`、`bigquery_meta`、`official_api_alpha` |
| ❌ 5 个 404 | `realtime_trending`、`daily_trends`、`hot_trends`、`rss_daily`（旧路径）、`top_charts` |
| 🔶 前置条件 | `trending_now_csv`、`yis_page`、`explore_csv_export`、BigQuery 实查 |

完整记录： [evidence/VERIFICATION.md](evidence/VERIFICATION.md)。原始探测产物在本地 `out/probes.json`（gitignored）。

关键事实：

- 旧 daily RSS 路径 `trendingsearches/daily/rss` 已迁移到 `trending/rss`（2025-03 社区确认，2026-10-06 实测一致）。
- `realtimetrends` / `dailytrends` / `hottrends` / `topcharts` 当前均 404。
- 官方 API alpha 入口是 `developers.google.com/search/apis/trends`，申请制，支持 5 年滚动、日/周/月/年、consistently scaled。

## 合规与反爬

- Google Trends 官方口径：0-100 是归一化相对占比，不是绝对搜索量。
- 内部 widgetdata / batchexecute 端点未文档化且随时可能变动。
- 429 与 `/sorry/index` 是常态；本项目自带退避，但**不要**用代理轮换去规避 Google 配额（违反 ToS）。
- 生产环境优先顺序建议：官方 API alpha → BigQuery → RSS/页面导出 → 内部端点（需自评合规）。

## 已知限制

- `trending_now_csv` / YIS 页面 / Explore CSV 导出需要浏览器自动化，本仓库不内置 Chrome。
- BigQuery 需要 GCP 凭据与 `google-cloud-bigquery`。
- 官方 API alpha 需要 Google 授权 token，项目只保留接入占位。
- `multirange` 与 `top_charts` 等旧实现保留在代码中，`top_charts` 当前 404。
- 代理/时区会影响 0-100 重标定；跨请求对比前需保存完整参数与抓取时间。
- 旧端点的“全量抓取”教程大多过时；本项目建议以 `demo_snapshot.py` 做端点健康检查后再批量抓取。

## 开发与测试

```bash
# 编译检查
python -m py_compile gt_scraper/*.py scripts/*.py

# 全量探测
python scripts/demo_snapshot.py

# 按需抓取冒烟
python scripts/fetch_all.py --surfaces rss_realtime,autocomplete --out out/fetch-smoke
```

扩展新数据面的流程：

1. 在 `gt_scraper/endpoints.py` 添加 URL；
2. 在对应 client 模块实现 `xxx()`；
3. 在 `gt_scraper/registry.py` 的 `DATA_SURFACES` 注册；
4. 在 `scripts/fetch_all.py` 的 `call_surface()` 挂接；
5. 用 `demo_snapshot.py` 实测并更新 `evidence/VERIFICATION.md` 与 `docs/SURFACES.md`。

## License

[MIT](LICENSE) © 2026 ielym

---

相关背景调研：`google-trends-research/`（141 张证据卡，含官方/方法/上游/下游/工具/社区/实测），本项目端点清单与那份调研同源。
