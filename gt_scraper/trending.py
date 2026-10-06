"""Trending 系数据面：Trending Now（页内 RPC）、实时/每日 API、每日/实时 RSS、各国今日热门。

端点与编码方式均来自 trendspy / trendspyg / pytrends 源码核对：
- batchexecute `i0OFE`（trendspy `_get_batch`）
- `/api/realtimetrends`（trendspy `trending_stories`）
- `/api/dailytrends`（trendspy `daily_trends_deprecated`）
- `/hottrends/visualize/internal/data`（pytrends `trending_searches`）
- RSS（trendspyg `download_google_trends_rss`）
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .endpoints import EP, TRENDING_NOW_RPC
from .http import HttpClient


class TrendingClient:
    def __init__(self, http: HttpClient):
        self.http = http

    # ------------------------------------------------------------------ #
    # Trendspy 的 batchexecute RPC（Trending Now 页面数据）
    # ------------------------------------------------------------------ #
    def trending_now(
        self,
        geo: str = "US",
        language: str = "en",
        hours: int = 24,
        num_news: int = 0,
        return_raw: bool = True,
    ) -> Any:
        """Trending Now 页内接口：`hours` 1..191 小时，含标题/展示图/topic/news。"""
        req_data = [None, None, geo, num_news, language, hours, 1]
        body = f"f.req={json.dumps([[[TRENDING_NOW_RPC, json.dumps(req_data), None, 'generic']]])}"
        headers = {"content-type": "application/x-www-form-urlencoded;charset=UTF-8"}
        raw = self.http.post_json(EP.BATCHEXECUTE, data=body, headers=headers, trim=0)
        if return_raw:
            return raw
        return self._flatten_trending_now(raw)

    @staticmethod
    def _flatten_trending_now(raw: Any) -> List[Dict[str, Any]]:
        try:
            # batchexecute 返回 [[ "wrb.fr", rpc, inner_json, ... ], ...]
            outer = raw[0]
            inner = outer[2]
            payload = json.loads(inner) if isinstance(inner, str) else inner
            # 内层 [null, [trend1, trend2, ...], ...]
            items = payload[1] if isinstance(payload, list) and len(payload) > 1 else payload.get("trends", [])
        except (IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"trending_now batch parse failed: {exc} | head={str(raw)[:200]!r}") from exc
        out = []
        for item in items:
            if isinstance(item, dict):
                out.append(
                    {
                        "keyword": item.get("title") or item.get("name"),
                        "entityNames": item.get("entityNames", []),
                        "volume": item.get("volume") or item.get("traffic"),
                        "started_timestamp": item.get("started_timestamp"),
                        "trend_keywords": item.get("trendKeywords") or item.get("related_queries", []),
                        "imageUrl": item.get("imageUrl"),
                        "articles": item.get("articles", []),
                        "exploreLink": item.get("exploreLink") or item.get("link"),
                    }
                )
            elif isinstance(item, list):
                # trendspy TrendKeyword.from_api 字段映射
                out.append(
                    {
                        "keyword": item[0],
                        "news": item[1],
                        "geo": item[2],
                        "started_timestamp": item[3] or None,
                        "ended_timestamp": item[4] or None,
                        "volume": item[6],
                        "volume_growth_pct": item[8],
                        "trend_keywords": item[9],
                        "topics": item[10],
                        "news_tokens": item[11],
                        "normalized_keyword": item[12] if len(item) > 12 else None,
                    }
                )
        return out

    # ------------------------------------------------------------------ #
    # 旧实时趋势 API（trendspy / pytrends）
    # ------------------------------------------------------------------ #
    def realtime_trending(
        self,
        geo: str = "US",
        category: str = "all",
        max_stories: int = 200,
        return_raw: bool = True,
    ) -> Any:
        """`/api/realtimetrends`；category: all/b/e/m/t/s/h；ri/rs 实测上限约 200。"""
        params = {
            "ns": 15,
            "geo": geo,
            "tz": self.http.tz,
            "hl": self.http.hl,
            "cat": category,
            "fi": "0",
            "fs": "0",
            "ri": max_stories,
            "rs": max_stories,
            "sort": 0,
        }
        raw = self.http.get_json(EP.REALTIME_TRENDS, params=params, trim=5)
        if return_raw:
            return raw
        return raw.get("storySummaries", {}).get("trendingStories", [])

    # ------------------------------------------------------------------ #
    # 旧每日趋势 API（trendspy deprecated）
    # ------------------------------------------------------------------ #
    def daily_trends(
        self,
        geo: str = "US",
        return_raw: bool = True,
    ) -> Any:
        params = {"ns": 15, "geo": geo, "hl": self.http.hl, "tz": self.http.tz}
        raw = self.http.get_json(EP.DAILY_TRENDS, params=params, trim=5)
        if return_raw:
            return raw
        return raw.get("default", {}).get("trendingSearchesDays", [])

    # ------------------------------------------------------------------ #
    # 各国今日热门（pytrends trending_searches 使用 hottrends 可视化）
    # ------------------------------------------------------------------ #
    def hot_trends(self, return_raw: bool = True) -> Any:
        """pytrends `trending_searches` 用 `pn`（如 united_states）读该 JSON 对应键。"""
        raw = self.http.get_json(EP.HOT_TRENDS, trim=0)
        if return_raw:
            return raw
        return raw

    # ------------------------------------------------------------------ #
    # RSS 数据面
    # ------------------------------------------------------------------ #
    def rss_daily(
        self,
        geo: str = "US",
        safe: bool = True,
        return_raw: bool = True,
    ) -> Any:
        """Daily Search Trends：`trendingsearches/daily/rss?geo=`. 原样返回 XML 文本或 items。"""
        text = self.http.get_text(EP.RSS_DAILY, params={"geo": geo, "safe": "true" if safe else "false"})
        if return_raw:
            return text
        return _parse_rss_items(text)

    def rss_realtime(
        self,
        geo: str = "US",
        return_raw: bool = True,
    ) -> Any:
        """Realtime Search Trends RSS：`trending/rss?geo=`. 原样返回 XML 文本或 items。"""
        text = self.http.get_text(EP.RSS_REALTIME, params={"geo": geo})
        if return_raw:
            return text
        return _parse_rss_items(text)


def _parse_rss_items(text: str) -> List[Dict[str, Any]]:
    """极简 XML items 提取；如需完整字段可换 xml.etree.ElementTree。"""
    import re
    import xml.etree.ElementTree as ET

    items = []
    try:
        root = ET.fromstring(text)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        for item in root.findall(".//item"):
            rec = {}
            for child in item:
                tag = child.tag.split("}")[-1]
                rec[tag] = child.text or ""
            for htag in ("ht:approx_traffic", "ht:news_item"):
                for node in item.findall(f".//{{{ns['ht']}}}{htag.split(':')[-1]}"):
                    rec.setdefault(htag, node.text or "")
            items.append(rec)
    except ET.ParseError as exc:
        raise ValueError(f"RSS parse failed: {exc}") from exc
    return items