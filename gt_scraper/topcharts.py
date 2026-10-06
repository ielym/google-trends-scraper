"""Top Charts / Year in Search：年度搜索排行榜。

pytrends 实现为 `/api/topcharts?date=YYYY&geo=GLOBAL`；
trendspyg 1.9.0 源码注释称 Google 已不再提供该端点（HTTP 404）。
真实可用性以实测为准。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .endpoints import EP
from .http import HttpClient
from .errors import SurfaceNotAvailableError


class TopChartsClient:
    def __init__(self, http: HttpClient):
        self.http = http

    def top_charts(
        self,
        date: int,
        geo: str = "GLOBAL",
        is_mobile: bool = False,
        return_raw: bool = True,
    ) -> Any:
        params = {
            "hl": self.http.hl,
            "tz": self.http.tz,
            "date": int(date),
            "geo": geo,
            "isMobile": str(is_mobile).lower(),
        }
        raw = self.http.get_json(EP.TOPCHARTS, params=params, trim=5)
        if return_raw:
            return raw
        try:
            return raw["topCharts"][0]["listItems"]
        except (KeyError, IndexError) as exc:
            raise SurfaceNotAvailableError(
                f"top_charts payload has no topCharts[0].listItems for {date}/{geo}: {str(raw)[:200]}"
            ) from exc