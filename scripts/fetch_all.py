#!/usr/bin/env python
"""按需抓取指定 Google Trends 数据面。

示例：
    python scripts/fetch_all.py --surfaces iot,related_queries --kw chatgpt --geo US --timeframe "today 12-m"
    python scripts/fetch_all.py --surfaces trending_now,rss_realtime --geo US --out out/fetch
    python scripts/fetch_all.py --surfaces top_charts,yis_page --geo GLOBAL --year 2024
    python scripts/fetch_all.py --surfaces datastore --out out/datastore --limit 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gt_scraper.autocomplete import AutocompleteClient
from gt_scraper.datastore import DatastoreClient
from gt_scraper.explore import ExploreClient
from gt_scraper.export import envelope, write_csv, write_json
from gt_scraper.http import HttpClient, client_from_config, load_config
from gt_scraper.meta import MetaClient
from gt_scraper.registry import DATA_SURFACES, SURFACE_INDEX, surface_spec
from gt_scraper.topcharts import TopChartsClient
from gt_scraper.trending import TrendingClient


def build_clients(http: HttpClient) -> Dict[str, Any]:
    return {
        "explore": ExploreClient(http),
        "trending": TrendingClient(http),
        "topcharts": TopChartsClient(http),
        "autocomplete": AutocompleteClient(http),
        "meta": MetaClient(http),
        "datastore": DatastoreClient(),
    }


def call_surface(clients, surface_id: str, args: argparse.Namespace) -> Any:
    exp = clients["explore"]
    tr = clients["trending"]
    tc = clients["topcharts"]
    au = clients["autocomplete"]
    me = clients["meta"]
    ds = clients["datastore"]

    kw = args.kw or "chatgpt"
    tf = args.timeframe or "today 12-m"
    geo = args.geo or ""
    cat = args.category or 0
    gprop = args.gprop or ""

    if surface_id == "iot":
        return exp.interest_over_time([kw], tf, geo, cat, gprop)
    if surface_id == "multirange":
        return exp.multirange_interest_over_time([kw], [tf, tf], geo, cat, gprop)
    if surface_id == "interest_by_region":
        return exp.interest_by_region(
            [kw], tf, geo, cat, gprop, resolution=args.resolution or "COUNTRY"
        )
    if surface_id == "related_queries":
        return exp.related_queries(kw, tf, geo, cat, gprop)
    if surface_id == "related_topics":
        return exp.related_topics(kw, tf, geo, cat, gprop)
    if surface_id == "categories":
        return me.categories(return_raw=False)
    if surface_id == "geo_pickers":
        return me.geo(return_raw=False)
    if surface_id == "autocomplete":
        return au.suggestions(kw, return_raw=False)
    if surface_id == "trending_now":
        return tr.trending_now(geo or "US", hours=args.hours or 24, return_raw=False)
    if surface_id == "trending_now_csv":
        raise RuntimeError(
            "trending_now_csv requires browser automation (trendspyg download_google_trends_csv); "
            "install selenium + Chrome and run it directly."
        )
    if surface_id == "realtime_trending":
        return tr.realtime_trending(geo or "US", category=args.category_name or "all")
    if surface_id == "daily_trends":
        return tr.daily_trends(geo or "US")
    if surface_id == "hot_trends":
        return tr.hot_trends()
    if surface_id == "rss_daily":
        return tr.rss_daily(geo or "US", return_raw=False)
    if surface_id == "rss_realtime":
        return tr.rss_realtime(geo or "US", return_raw=False)
    if surface_id == "top_charts":
        return tc.top_charts(args.year or 2024, geo or "GLOBAL")
    if surface_id == "yis_page":
        return {
            "url": f"https://trends.google.com/trends/yis/{args.year or 2024}/{geo or 'GLOBAL'}/"
        }
    if surface_id == "bigquery":
        from gt_scraper.bigquery import describe

        return describe()
    if surface_id == "official_api_alpha":
        return {
            "status": "application_only",
            "doc": "https://trends.google.com/trends/documentation",
            "note": "replace with real access token / base url after Google grants access",
        }
    if surface_id == "datastore":
        files = ds.list_csv()
        if args.limit:
            files = files[: args.limit]
        saved = [ds.download_csv(f["path"], args.out) for f in files]
        return {"count": len(saved), "saved": saved}
    if surface_id == "explore_csv_export":
        return {
            "status": "manual_or_browser",
            "url": (
                f"https://trends.google.com/trends/explore?q={kw}&date={tf}"
                f"&geo={geo}&cat={cat}&gprop={gprop}"
            ),
        }
    raise KeyError(surface_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--surfaces",
        required=True,
        help="comma-separated surface ids; 'all' 跑全部非浏览器面",
    )
    parser.add_argument("--kw", default=None, help="keyword(s), comma separated")
    parser.add_argument("--timeframe", default=None)
    parser.add_argument("--geo", default="")
    parser.add_argument("--category", type=int, default=0)
    parser.add_argument("--gprop", default="", choices=["", "images", "news", "youtube", "froogle"])
    parser.add_argument("--resolution", default="COUNTRY")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--category_name", default="all")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--out", default="out/fetch")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.direct:
        cfg.setdefault("direct", True)
    http = client_from_config(cfg)
    clients = build_clients(http)

    if args.surfaces.strip().lower() == "all":
        ids = [s["id"] for s in DATA_SURFACES]
    else:
        ids = [x.strip() for x in args.surfaces.split(",") if x.strip()]

    os.makedirs(args.out, exist_ok=True)
    summary = []
    for sid in ids:
        spec = surface_spec(sid)
        rec = {"surface": sid, "name": spec["name"], "status": "pending"}
        try:
            payload = call_surface(clients, sid, args)
            rec["status"] = "ok"
            rec["records"] = len(payload) if isinstance(payload, (list, dict)) else 1
        except Exception as exc:  # 一个面失败不影响其余面
            payload = None
            rec["status"] = "error"
            rec["error"] = f"{type(exc).__name__}: {exc}"
        summary.append(rec)

        ev = envelope(sid, payload, {"surface_params": vars(args)})
        safe = sid.replace("/", "_")
        write_json(ev, os.path.join(args.out, f"{safe}.json"))
        # 同时把可展开的列表写一份 CSV（失败/非列表面跳过）
        if rec["status"] == "ok" and isinstance(payload, list) and payload and all(
            isinstance(r, dict) for r in payload
        ):
            try:
                write_csv(payload, os.path.join(args.out, f"{safe}.csv"))
            except Exception:
                pass
        print(f"[{rec['status']}] {sid} -> {args.out}/{safe}.json")
    write_json(summary, os.path.join(args.out, "summary.json"))
    print(f"\nsummary: {args.out}/summary.json  (ok={sum(1 for r in summary if r['status']=='ok')}/{len(summary)})")
    return 0 if all(r["status"] == "ok" for r in summary) else 2


if __name__ == "__main__":
    sys.exit(main())