"""全部 Google Trends 端点注册表。

所有 URL 均来自对已安装库源码的逐行核对：
- trendspy 0.1.6  client.py — BATCH_URL / API_* / EMBED_* / RSS 常量
- trendspyg 1.9.0 explore/_http.py、rss_downloader.py、compat/request.py、keywords.py
- pytrends 4.9.2 request.py — /api/explore 与 widgetdata 系
以及 Google 官方文档（BigQuery 数据集、RSS、Trends 帮助）与实测。

注意：Google 内部端点是未文档化接口，随时可能变动；404/429 属常态。
"""

from urllib.parse import quote

BASE = "https://trends.google.com"


class EP:
    # ---- Explore widget 流程 ----
    EXPLORE = f"{BASE}/trends/api/explore"                      # 取 widgets token
    # ---- widgetdata 数据面 ----
    WIDGETDATA = f"{BASE}/trends/api/widgetdata"
    MULTILINE = f"{WIDGETDATA}/multiline"                       # interest over time
    MULTIRANGE = f"{WIDGETDATA}/multirange"                     # 多时间窗合并
    COMPAREDGEO = f"{WIDGETDATA}/comparedgeo"                   # interest by region
    RELATEDSEARCHES = f"{WIDGETDATA}/relatedsearches"           # related queries/topics
    # ---- pickers 元数据 ----
    CATEGORY_PICKER = f"{BASE}/trends/api/explore/pickers/category"
    GEO_PICKER = f"{BASE}/trends/api/explore/pickers/geo"
    # ---- 联想 ----
    AUTOCOMPLETE = f"{BASE}/trends/api/autocomplete/"           # 拼接关键词
    # ---- Trending 系 ----
    BATCHEXECUTE = f"{BASE}/_/TrendsUi/data/batchexecute"       # Trending Now 页内 RPC
    REALTIME_TRENDS = f"{BASE}/trends/api/realtimetrends"       # 旧实时趋势 API
    DAILY_TRENDS = f"{BASE}/trends/api/dailytrends"             # 旧每日趋势 API
    HOT_TRENDS = f"{BASE}/trends/hottrends/visualize/internal/data"  # 各国今日热门
    # ---- RSS ----
    RSS_DAILY = f"{BASE}/trends/trendingsearches/daily/rss"     # Daily Search Trends
    RSS_REALTIME = f"{BASE}/trending/rss"                        # Realtime Search Trends
    # ---- Top Charts / Year in Search ----
    TOPCHARTS = f"{BASE}/trends/api/topcharts"                  # 年度排行榜
    # ---- embed 变体（trendspy 用） ----
    EMBED_EXPLORE = f"{BASE}/trends/embed/explore"

    @staticmethod
    def autocomplete(kw: str, hl: str = "en-US") -> str:
        return f"{EP.AUTOCOMPLETE}{quote(kw)}?hl={hl}"


# Trending Now 页内 RPC 名（trendspy 用 i0OFE，参数 [null,null,geo,num_news,language,hours,1]）
TRENDING_NOW_RPC = "i0OFE"

# gprop 合法值（pytrends build_payload 校验；'' 表示网页搜索）
GPROP_VALUES = ("", "images", "news", "youtube", "froogle")

# Trending Now 时间窗：trending_now 接口支持 1..191 小时；页内 UI 固定 4/24/48/168h
TRENDING_HOURS = (4, 24, 48, 168)