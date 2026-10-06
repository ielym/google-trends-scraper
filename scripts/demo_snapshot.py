#!/usr/bin/env python
"""全数据面小样本探测：验证哪些 Google Trends 数据面当前可抓。

输出：
- out/probes.json：每个 surface 的 status / 样本记录数 / 错误 / 耗时
- out/probes-{surface}.json：原始样本信封

跑完请把结果回填到 docs/SURFACES.md 的 verified 列。
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gt_scraper.autocomplete import AutocompleteClient
from gt_scraper.bigquery import describe
from gt_scraper.datastore import DatastoreClient
from gt_scraper.errors import HttpError, ParseError, RateLimitedError
from gt_scraper.explore import ExploreClient
from gt_scraper.export import envelope
from gt_scraper.http import HttpClient, client_from_config, load_config
from gt_scraper.meta import MetaClient
from gt_scraper.registry import DATA_SURFACES
from gt_scraper.topcharts import TopChartsClient
from gt_scraper.trending import TrendingClient

SKIP = {".DS_Store", ".git", ".github"}


def probes(http: HttpClient) -> dict:
    exp = ExploreClient(http)
    tr = TrendingClient(http)
    tc = TopChartsClient(http)
    au = AutocompleteClient(http)
    me = MetaClient(http)
    ds = DatastoreClient()

    out = {}
    _run(out, "iot", lambda: exp.interest_over_time(["chatgpt"], "today 12-m", "US"), {"kw": "chatgpt", "geo": "US", "timeframe": "today 12-m"})
    _run(out, "related_queries", lambda: exp.related_queries("chatgpt", "today 12-m", "US"), {"kw": "chatgpt"})
    _run(out, "related_topics", lambda: exp.related_topics("apple", "today 12-m", "US"), {"kw": "apple"})
    _run(out, "interest_by_region", lambda: exp.interest_by_region(["chatgpt"], "today 12-m", "US", resolution="REGION"), {"resolution": "REGION"})
    _run(out, "autocomplete", lambda: au.suggestions("chat", return_raw=False), {"kw": "chat"})
    _run(out, "categories", lambda: me.categories(return_raw=False), {})
    _run(out, "geo_pickers", lambda: me.geo(return_raw=False), {})
    _run(out, "trending_now", lambda: tr.trending_now("US", hours=24, return_raw=False), {"geo": "US"})
    _run(out, "realtime_trending", lambda: tr.realtime_trending("US", category="all"), {"geo": "US"})
    _run(out, "daily_trends", lambda: tr.daily_trends("US"), {"geo": "US"})
    _run(out, "hot_trends", lambda: tr.hot_trends(), {})
    _run(out, "rss_daily", lambda: tr.rss_daily("US", return_raw=False), {"geo": "US"})
    _run(out, "rss_realtime", lambda: tr.rss_realtime("US", return_raw=False), {"geo": "US"})
    _run(out, "top_charts", lambda: tc.top_charts(2024, "GLOBAL"), {"year": 2024})
    _run(out, "datastore", lambda: ds.list_csv()[:5], {"limit": 5})
    _run(out, "bigquery_meta", lambda: describe(), {})
    _run(out, "official_api_alpha", lambda: {"status": "application_only", "doc": "https://trends.google.com/trends/documentation"}, {})
    return out


def _run(out: dict, sid: str, fn, params: dict):
    started = time.time()
    rec = {
        "surface": sid,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "params": params,
        "status": "ok",
        "elapsed_s": None,
        "record_count": None,
        "error": None,
        "sample": None,
    }
    try:
        payload = fn()
        rec["elapsed_s"] = round(time.time() - started, 2)
        rec["sample"] = payload if isinstance(payload, (str, int, float, bool)) else repr(payload)[:500]
        if isinstance(payload, list):
            rec["record_count"] = len(payload)
        elif isinstance(payload, dict):
            rec["record_count"] = len(payload)
    except RateLimitedError as exc:
        rec["status"] = "rate_limited"
        rec["error"] = f"RateLimitedError: {exc}"
        rec["sample"] = str(exc)[:300]
    except HttpError as exc:
        rec["status"] = "error"
        rec["error"] = f"{type(exc).__name__}: HTTP {exc.status_code} {exc}"
        rec["sample"] = str(exc)[:300]
    except ParseError as exc:
        rec["status"] = "error"
        rec["error"] = f"ParseError: {exc}"
        rec["sample"] = str(exc)[:300]
    except Exception as exc:
        rec["status"] = "error"
        rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["sample"] = str(exc)[:300]
    out[sid] = rec
    return rec


def main() -> int:
    cfg = {**load_config("config.json"), "direct": bool(os.environ.get("GT_DIRECT"))}
    http = client_from_config(cfg)
    results = probes(http)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "probes.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    for sid, rec in results.items():
        with open(os.path.join(out_dir, f"probes-{sid}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results.values() if r["status"] == "ok")
    print(f"probes written to {out_dir}\\probes.json")
    print(f"ok={ok}/{len(results)}")
    for sid, rec in results.items():
        print(f"  [{rec['status']:>5}] {sid:24s} elapsed={rec.get('elapsed_s')} rows={rec.get('record_count')}")
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())