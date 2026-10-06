"""自动补全/联想（Google Trends 搜索框下拉）。

端点：`/trends/api/autocomplete/<keyword>?hl=...`，
pytrends `suggestions()` 与 trendspyg `get_keyword_suggestions()` 均使用。
"""

from __future__ import annotations

from typing import Any, Dict

from .endpoints import EP
from .http import HttpClient


class AutocompleteClient:
    def __init__(self, http: HttpClient):
        self.http = http

    def suggestions(self, keyword: str, return_raw: bool = True) -> Any:
        raw = self.http.get_json(EP.autocomplete(keyword, self.http.hl), trim=5)
        if return_raw:
            return raw
        return raw.get("default", {}).get("topics", [])

    @staticmethod
    def flatten(topics: list) -> list:
        out = []
        for t in topics:
            out.append(
                {
                    "title": t.get("title"),
                    "type": t.get("type"),
                    "mid": t.get("mid"),
                    "base_rank": t.get("base_rank"),
                }
            )
        return out