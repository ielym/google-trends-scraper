"""全数据面注册表：文档中"全部可爬取内容"与代码共用同一来源。

每个数据面包含：
- id/name/group：稳定标识
- endpoint：端点或途径
- params/granularity/fields：数据形态
- notes：已知限制、来源备注
- verified：实测状态（由 scripts/demo_snapshot.py 回填到 out/probes.json）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

DATA_SURFACES: List[Dict[str, Any]] = [
    # ------------------------- Explore 系 ------------------------- #
    {
        "id": "iot",
        "name": "Interest Over Time（相对兴趣曲线）",
        "group": "Explore",
        "endpoint": "/api/explore + /api/widgetdata/multiline",
        "params": ["keywords", "timeframe", "geo", "cat", "gprop"],
        "granularity": "细分：1min/8min/16min/小时/日/周/月（按窗口长度）",
        "fields": ["time", "formattedTime", "value[]（每词0-100）", "isPartial"],
        "notes": "0-100 是相对占比不是绝对量；窗口变化会重标定。",
        "verified": "",
    },
    {
        "id": "multirange",
        "name": "Multirange Interest Over Time（多时间窗合并）",
        "group": "Explore",
        "endpoint": "/api/widgetdata/multirange",
        "params": ["keywords", "timeframes[]", "geo", "cat", "gprop"],
        "granularity": "多窗各自粒度",
        "fields": ["formattedAxisTime", "columnData[].formattedTime/value", "averages"],
        "notes": "pytrends multirange_interest_over_time 使用；同一 comparisonItem 内多时间窗。",
        "verified": "",
    },
    {
        "id": "interest_by_region",
        "name": "Interest by Region（地图/区域兴趣）",
        "group": "Explore",
        "endpoint": "/api/widgetdata/comparedgeo",
        "params": ["keywords", "timeframe", "geo", "resolution(COUNTRY/REGION/DMA/CITY)", "inc_low_vol"],
        "granularity": "国家/州/城市/DMA（美国）",
        "fields": ["geoName", "geoCode", "coordinates", "value[]"],
        "notes": "Explore 页面地图数据；DMA 只在美国语境。",
        "verified": "",
    },
    {
        "id": "related_queries",
        "name": "Related Queries（相关查询 Top+Rising）",
        "group": "Explore",
        "endpoint": "/api/widgetdata/relatedsearches",
        "params": ["keyword", "timeframe", "geo", "cat", "gprop"],
        "granularity": "Top 25 + Rising 25（每词）",
        "fields": ["query", "value", "rank", "link"],
        "notes": "relatedsearches 按 widget 类型区分 query/topic。",
        "verified": "",
    },
    {
        "id": "related_topics",
        "name": "Related Topics（相关主题/实体 Top+Rising）",
        "group": "Explore",
        "endpoint": "/api/widgetdata/relatedsearches",
        "params": ["keyword", "timeframe", "geo", "cat", "gprop"],
        "granularity": "Top 25 + Rising 25（每词）",
        "fields": ["topic.mid", "topic.title", "topic.type", "value", "rank", "link"],
        "notes": "实体级聚合；对歧义词相关主题更有用。",
        "verified": "",
    },
    {
        "id": "categories",
        "name": "Categories（Explore 分类树）",
        "group": "Metadata",
        "endpoint": "/api/explore/pickers/category",
        "params": ["hl"],
        "granularity": "tree",
        "fields": ["id", "name", "children"],
        "notes": "用 cat 参数过滤所有 Explore 数据面。",
        "verified": "",
    },
    {
        "id": "geo_pickers",
        "name": "Geo Pickers（全部地理编码）",
        "group": "Metadata",
        "endpoint": "/api/explore/pickers/geo",
        "params": ["hl", "tz"],
        "granularity": "tree",
        "fields": ["id", "name", "children"],
        "notes": "可枚举 world/country/region/metro/city；自动化全覆盖需要它。",
        "verified": "",
    },
    {
        "id": "autocomplete",
        "name": "Autocomplete / Suggestions（联想词）",
        "group": "Autocomplete",
        "endpoint": "/api/autocomplete/<kw>",
        "params": ["keyword", "hl"],
        "granularity": "即时",
        "fields": ["title", "type", "mid", "base_rank"],
        "notes": "搜索框下拉建议；返回 topic mid，可用于消歧。",
        "verified": "",
    },
    # ------------------------ Trending 系 ------------------------ #
    {
        "id": "trending_now",
        "name": "Trending Now（页面实时趋势列表）",
        "group": "Trending",
        "endpoint": "/_/TrendsUi/data/batchexecute (i0OFE)",
        "params": ["geo", "language", "hours(1..191)", "num_news"],
        "granularity": "每 ~10 分钟刷新（官方）",
        "fields": ["title", "entityNames", "imageUrl", "traffic", "exploreLink", "articles", "id"],
        "notes": "trendspy i0OFE；渲染 JSON 在 batchexecute 输入内。",
        "verified": "",
    },
    {
        "id": "trending_now_csv",
        "name": "Trending Now CSV 导出",
        "group": "Trending",
        "endpoint": "浏览页面导出（trendspyg download_google_trends_csv）",
        "params": ["geo", "hours(4/24/48/168)", "category", "active_only", "sort"],
        "granularity": "当前窗口，约 480 条",
        "fields": ["Trend", "Volume", "Explorer link", "Started at", "Ends at", "Trending searches", "Category", "Image", "Article"],
        "notes": "需 Chrome/Selenium；页内 CSV 是 Trending Now 大表。",
        "verified": "",
    },
    {
        "id": "realtime_trending",
        "name": "Realtime Trends API（旧实时，已下线）",
        "group": "Trending",
        "endpoint": "/api/realtimetrends",
        "params": ["geo", "cat(all/b/e/m/t/s/h)", "ri/rs(<=200)", "sort"],
        "granularity": "准实时",
        "fields": ["storySummaries.trendingStories[]: entityNames/title/image/articles/metrics"],
        "notes": "trendspy trending_stories + pytrends realtime_trending_searches；实测 2026-10-06 返回 404，当前下线。",
        "verified": "down",
    },
    {
        "id": "daily_trends",
        "name": "Daily Trends API（旧每日，已下线）",
        "group": "Trending",
        "endpoint": "/api/dailytrends",
        "params": ["geo", "hl", "tz"],
        "granularity": "日",
        "fields": ["default.trendingSearchesDays[]: trendingSearches[]"],
        "notes": "trendspy daily_trends_deprecated；实测 2026-10-06 返回 404，当前下线。",
        "verified": "down",
    },
    {
        "id": "hot_trends",
        "name": "Hot Trends（各国今日热门，旧可视化端点）",
        "group": "Trending",
        "endpoint": "/hottrends/visualize/internal/data",
        "params": [],
        "granularity": "日",
        "fields": ["pn 键 -> trends[]（pytrends trending_searches）"],
        "notes": "pytrends trending_searches 底端；实测 2026-10-06 返回 404，当前下线，改用 Trending Now/RSS。",
        "verified": "down",
    },
    {
        "id": "rss_daily",
        "name": "Daily Search Trends RSS（旧路径，已下线）",
        "group": "Trending",
        "endpoint": "/trends/trendingsearches/daily/rss（2025-03 起 404）",
        "params": ["geo", "safe"],
        "granularity": "日（旧）",
        "fields": ["title", "link", "ht:approx_traffic", "ht:news_item"],
        "notes": "实测 404；社区（note.com 2025-03-08）证实官方将 daily RSS 迁移到 /trending/rss。请用 rss_realtime 面。",
        "verified": "down",
    },
    {
        "id": "rss_realtime",
        "name": "Realtime Search Trends RSS",
        "group": "Trending",
        "endpoint": "/trending/rss",
        "params": ["geo"],
        "granularity": "准实时；约 10-20 条",
        "fields": ["title", "link", "approx_traffic", "news items", "image"],
        "notes": "trendspyg 用该 RSS + 图片/news 增强；HEAD 实测为 Daily Search Trends XML。",
        "verified": "",
    },
    # ----------------------- Charts / YIS ------------------------ #
    {
        "id": "top_charts",
        "name": "Top Charts / Year in Search（年度排行榜，当前下线）",
        "group": "Charts",
        "endpoint": "/api/topcharts",
        "params": ["date(YYYY)", "geo", "isMobile"],
        "granularity": "年/国家",
        "fields": ["topCharts[0].listItems[]"],
        "notes": "pytrends 有实现；实测 2026-10-06 返回 404，与 trendspyg 源码注释一致，当前下线。",
        "verified": "down",
    },
    {
        "id": "yis_page",
        "name": "Year in Search 页面",
        "group": "Charts",
        "endpoint": "https://trends.google.com/trends/yis/YYYY/GEO/",
        "params": ["year", "geo"],
        "granularity": "年",
        "fields": ["页面渲染榜单/图表"],
        "notes": "与 top_charts 同源；可用浏览器抓页面。",
        "verified": "",
    },
    # ----------------------- 官方数据 ------------------------ #
    {
        "id": "bigquery",
        "name": "BigQuery 官方数据集",
        "group": "Official",
        "endpoint": "bigquery-public-data.google_trends.*",
        "params": ["SQL", "project", "location"],
        "granularity": "US daily rolling 5y / US hourly rolling 1y / international daily rolling 5y",
        "fields": ["refresh_date", "dma/region", "term", "rank", "score", "percent_gain"],
        "notes": "Top25+Top25Rising；TTL 30 天；免费 1TB/月。需要 GCP 凭据。",
        "verified": "",
    },
    {
        "id": "datastore",
        "name": "GoogleTrends/data 官方开源数据集",
        "group": "Official",
        "endpoint": "github.com/GoogleTrends/data（GitHub API + raw CSV）",
        "params": ["pattern", "out_dir", "limit"],
        "granularity": "按数据集（事件/选举/体育/品牌）",
        "fields": ["策展 CSV 列由各数据集定义"],
        "notes": "2026-10-06 枚举 master 顶层：112 个 CSV。",
        "verified": "",
    },
    {
        "id": "official_api_alpha",
        "name": "Trends API alpha（申请制，官方）",
        "group": "Official",
        "endpoint": "https://developers.google.com/search/apis/trends（申请后获取访问）",
        "params": ["auth token", "country/subregion", "aggregation(day/week/month/year)"],
        "granularity": "day/week/month/year；滚动 5 年（1800 天）",
        "fields": ["相对兴趣时间序列（consistently scaled，非 0-100，可跨请求合并）"],
        "notes": "官方文档（OFF-015/OFF-016）：alpha 申请制；可比较数十词；不重跑历史即可补最新时段。本脚本留接口，不内置凭据。",
        "verified": "",
    },
    # ----------------------- 页面导出 ------------------------ #
    {
        "id": "explore_csv_export",
        "name": "Explore 页 CSV 导出",
        "group": "Page Export",
        "endpoint": "https://trends.google.com/trends/explore -> CSV 下载",
        "params": ["keywords", "timeframe", "geo", "cat", "gprop"],
        "granularity": "同 Explore 明细",
        "fields": ["day", "keyword", "interest"],
        "notes": "UI 原生导出；也可用浏览器自动化复现。",
        "verified": "",
    },
]


SURFACE_INDEX: Dict[str, Dict[str, Any]] = {
    s["id"]: s for s in DATA_SURFACES
}


def surface_spec(surface_id: str) -> Dict[str, Any]:
    if surface_id not in SURFACE_INDEX:
        raise KeyError(
            f"unknown surface {surface_id!r}; available: {', '.join(SURFACE_INDEX)}"
        )
    return SURFACE_INDEX[surface_id]


def list_groups() -> List[str]:
    groups = []
    for s in DATA_SURFACES:
        if s["group"] not in groups:
            groups.append(s["group"])
    return groups