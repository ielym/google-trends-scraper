"""元数据数据面：分类树、地理选择器。

- `/api/explore/pickers/category`：Explore 分类树（pytrends/trendspyg）
- `/api/explore/pickers/geo`：可用地理编码（trendspy `geo()`）

这两个面看起来是"辅助数据"，但它们本身也是可抓取内容：
自动化覆盖所有 category/geo 时需要它们，因此纳入全量清单。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .endpoints import EP
from .http import HttpClient


class MetaClient:
    def __init__(self, http: HttpClient):
        self.http = http

    def categories(self, return_raw: bool = True) -> Any:
        raw = self.http.get_json(
            EP.CATEGORY_PICKER, params={"hl": self.http.hl}, trim=5
        )
        if return_raw:
            return raw
        return _flatten_tree(raw, parent_id="")

    def geo(self, return_raw: bool = True) -> Any:
        raw = self.http.get_json(
            EP.GEO_PICKER, params={"hl": self.http.hl, "tz": self.http.tz}, trim=5
        )
        if return_raw:
            return raw
        return _flatten_geo(raw)


def _flatten_tree(node: Dict[str, Any], parent_id: str = "") -> list:
    """category picker 返回 {children:[{id,name,children}]}，展平成列表。"""
    out = []
    children = node.get("children", [])
    if not isinstance(children, list):
        return out
    for child in children:
        cid = child.get("id")
        rec = {
            "id": cid,
            "name": child.get("name"),
            "parent_id": parent_id,
        }
        out.append(rec)
        for sub in _flatten_tree(child, parent_id=cid):
            out.append(sub)
    return out


def _flatten_geo(raw: Dict[str, Any]) -> list:
    """geo picker 结构为嵌套 children；简化为 {id,name,type,parent}。"""
    out = []

    def walk(node: Dict[str, Any], parent: str = ""):
        for child in node.get("children", []):
            rec = {
                "id": child.get("id"),
                "name": child.get("name"),
                "parent_id": parent,
            }
            out.append(rec)
            walk(child, parent=rec["id"])

    walk(raw, parent="")
    return out