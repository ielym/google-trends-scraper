"""Explore 系数据面：兴趣曲线、多时间窗、区域地图、相关查询、相关主题。

流程（与 trendspy/pytrends 相同）：
1. 用 comparisonItem 请求 `/api/explore`，得到各 widget 的 request + token；
2. 用 `/api/widgetdata/{multiline,multirange,comparedgeo,relatedsearches}`
   拉数据。

返回结构尽量保留原始 JSON，同时给出标准化 `records` 列表，便于导出。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .endpoints import EP
from .http import HttpClient


class ExploreClient:
    def __init__(self, http: HttpClient):
        self.http = http

    # ------------------------------------------------------------------ #
    # widget token 获取
    # ------------------------------------------------------------------ #
    def explore_widgets(
        self,
        keywords: List[str],
        timeframe: Any = "today 12-m",
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
    ) -> List[Dict[str, Any]]:
        """POST /trends/api/explore -> widgets 列表（含 request/token/id/type）。"""
        if isinstance(timeframe, str):
            timeframes = [timeframe] * len(keywords)
        else:
            timeframes = list(timeframe)
            if len(timeframes) != len(keywords):
                raise ValueError("timeframe list length must match keywords length")

        comparison = [
            {"keyword": kw, "time": tf, "geo": geo}
            for kw, tf in zip(keywords, timeframes)
        ]
        payload = {
            "req": json.dumps(
                {"comparisonItem": comparison, "category": cat, "property": gprop}
            ),
            "hl": self.http.hl,
            "tz": str(self.http.tz),
        }
        data = self.http.post_json(EP.EXPLORE, params=payload)
        return data.get("widgets", [])

    def _widget(self, widgets: List[Dict[str, Any]], widget_id: str) -> Dict[str, Any]:
        for w in widgets:
            if w.get("id") == widget_id:
                return w
        raise KeyError(f"widget {widget_id!r} not found in explore response")

    def _widgetdata(self, widget: Dict[str, Any], url: str) -> Dict[str, Any]:
        params = {
            "req": json.dumps(widget["request"]),
            "token": widget["token"],
            "tz": str(self.http.tz),
        }
        return self.http.get_json(url, params=params, trim=5)

    # ------------------------------------------------------------------ #
    # interest over time (multiline)
    # ------------------------------------------------------------------ #
    def interest_over_time(
        self,
        keywords: List[str],
        timeframe: Any = "today 12-m",
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
        return_raw: bool = True,
    ) -> Any:
        widgets = self.explore_widgets(keywords, timeframe, geo, cat, gprop)
        widget = self._widget(widgets, "TIMESERIES")
        raw = self._widgetdata(widget, EP.MULTILINE)
        if return_raw:
            return raw
        return _flatten_timeline(raw)

    # ------------------------------------------------------------------ #
    # multirange interest over time
    # ------------------------------------------------------------------ #
    def multirange_interest_over_time(
        self,
        keywords: List[str],
        timeframes: List[str],
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
        return_raw: bool = True,
    ) -> Any:
        """多时间窗合并（pytrends multirange_interest_over_time 的底层）。"""
        widgets = self.explore_widgets(keywords, timeframes, geo, cat, gprop)
        widget = self._widget(widgets, "TIMESERIES")
        raw = self._widgetdata(widget, EP.MULTIRANGE)
        if return_raw:
            return raw
        return _flatten_multirange(raw)

    # ------------------------------------------------------------------ #
    # interest by region (comparedgeo)
    # ------------------------------------------------------------------ #
    def interest_by_region(
        self,
        keywords: List[str],
        timeframe: Any = "today 12-m",
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
        resolution: str = "COUNTRY",
        inc_low_vol: bool = False,
        inc_geo_code: bool = False,
        return_raw: bool = True,
    ) -> Any:
        """region 参数：COUNTRY / REGION / DMA / CITY；仅美国支持 DMA/CITY。"""
        widgets = self.explore_widgets(keywords, timeframe, geo, cat, gprop)
        widget = self._widget(widgets, "GEO_MAP")
        widget["request"]["resolution"] = resolution
        widget["request"]["includeLowSearchVolumeGeos"] = inc_low_vol
        raw = self._widgetdata(widget, EP.COMPAREDGEO)
        if return_raw:
            return raw
        records = _flatten_region(raw)
        if inc_geo_code:
            return records
        return [
            {k: v for k, v in r.items() if k not in ("geoCode", "coordinates")}
            for r in records
        ]

    # ------------------------------------------------------------------ #
    # related
    # ------------------------------------------------------------------ #
    def related_queries(
        self,
        keyword: str,
        timeframe: Any = "today 12-m",
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
        return_raw: bool = True,
    ) -> Any:
        widgets = self.explore_widgets([keyword], timeframe, geo, cat, gprop)
        widget = self._widget(widgets, "RELATED_QUERIES")
        raw = self._widgetdata(widget, EP.RELATEDSEARCHES)
        if return_raw:
            return raw
        return _flatten_related(raw)

    def related_topics(
        self,
        keyword: str,
        timeframe: Any = "today 12-m",
        geo: str = "",
        cat: int = 0,
        gprop: str = "",
        return_raw: bool = True,
    ) -> Any:
        widgets = self.explore_widgets([keyword], timeframe, geo, cat, gprop)
        widget = self._widget(widgets, "RELATED_TOPICS")
        raw = self._widgetdata(widget, EP.RELATEDSEARCHES)
        if return_raw:
            return raw
        return _flatten_related(raw)


# ---------------------------------------------------------------------- #
# 标准化
# ---------------------------------------------------------------------- #
def _flatten_timeline(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for item in raw.get("default", {}).get("timelineData", []):
        row = {"time": item.get("time"), "formattedTime": item.get("formattedTime")}
        values = item.get("value", [])
        for i, kw in enumerate(_keyword_names(raw)):
            row[f"{kw}_value"] = values[i] if i < len(values) else None
        if "isPartial" in item:
            row["isPartial"] = item["isPartial"]
        out.append(row)
    return out


def _keyword_names(raw: Dict[str, Any]) -> List[str]:
    bullets = raw.get("default", {}).get("bullets", [])
    names = []
    for b in bullets:
        if isinstance(b, dict) and "text" in b:
            names.append(b["text"])
    return names or [f"kw{i}" for i in range(len(raw.get("default", {}).get("timelineData", [{}])[0].get("value", [])))]


def _flatten_multirange(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    default = raw.get("default", {})
    for i, item in enumerate(default.get("timelineData", [])):
        row = {"range": item.get("formattedAxisTime") or item.get("formattedTime")}
        columns = item.get("columnData", [])
        for j, col in enumerate(columns):
            row[f"kw{j}_time"] = col.get("formattedTime")
            row[f"kw{j}_value"] = col.get("value")
        out.append(row)
    if default.get("averages"):
        avg = {"range": "Average"}
        for j, val in enumerate(default["averages"]):
            avg[f"kw{j}_value"] = val
        out.insert(0, avg)
    return out


def _flatten_region(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for item in raw.get("default", {}).get("geoMapData", []):
        row = {"geoName": item.get("geoName")}
        if "geoCode" in item:
            row["geoCode"] = item["geoCode"]
        if "coordinates" in item:
            row["coordinates"] = item["coordinates"]
        values = item.get("value", [])
        for i, kw in enumerate(_keyword_names(raw)):
            row[f"{kw}_value"] = values[i] if i < len(values) else None
        out.append(row)
    return out


def _flatten_related(raw: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """relatedsearches 返回 rankedList；顺序为 [top, rising]（缺时单列表）。"""
    default = raw.get("default", {})
    ranked = default.get("rankedList", [])
    out: Dict[str, List[Dict[str, Any]]] = {"top": [], "rising": []}
    for idx, block in enumerate(ranked):
        target = "top" if idx % 2 == 0 else "rising"
        for item in block.get("rankedKeyword", []):
            out[target].append(_related_item(item))
    return out


def _related_item(item: Dict[str, Any]) -> Dict[str, Any]:
    topic = item.get("topic", {}) if isinstance(item.get("topic"), dict) else {}
    return {
        "value": item.get("query") or item.get("value"),
        "mid": topic.get("mid"),
        "title": topic.get("title"),
        "type": topic.get("type"),
        "rank": item.get("rank"),
        "link": item.get("link"),
    }