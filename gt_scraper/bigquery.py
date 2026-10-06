"""BigQuery 官方数据集（可选，需 GCP 凭据）。

官方支持页（support.google.com/trends/answer/12764470，2026-10-06 抓取）：
- 美国日粒度：Top 25 + Top 25 Rising，210 个 DMA，滚动 5 年
- 美国小时粒度：6h/4x daily，滚动 1 年
- 国际：约 50 国，ISO 国家码 + 子区域，日粒度滚动 5 年
- 分区 TTL 30 天

`google-cloud-bigquery` 与凭据为可选依赖。没有凭据时给出明确错误；
只研究元数据/表结构时也够用。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

TABLE_META: List[Dict[str, str]] = [
    {
        "table": "bigquery-public-data.google_trends.top_terms",
        "scope": "US",
        "granularity": "daily",
        "window": "rolling 5 years",
        "note": "Top 25 overall, 210 DMA, partition TTL 30 days",
    },
    {
        "table": "bigquery-public-data.google_trends.top_rising_terms",
        "scope": "US",
        "granularity": "daily",
        "window": "rolling 5 years",
        "note": "Top 25 rising",
    },
    {
        "table": "bigquery-public-data.google_trends.international_top_terms",
        "scope": "international ~50 countries",
        "granularity": "daily",
        "window": "rolling 5 years",
        "note": "ISO country + subregions; Top 25 overall",
    },
    {
        "table": "bigquery-public-data.google_trends.international_top_rising_terms",
        "scope": "international ~50 countries",
        "granularity": "daily",
        "window": "rolling 5 years",
        "note": "Top 25 rising",
    },
    {
        "table": "bigquery-public-data.google_trends.hourly_top_terms",
        "scope": "US",
        "granularity": "hourly (6h captures, 4x daily)",
        "window": "rolling 1 year",
        "note": "hourly dataset available via marketplace",
    },
    {
        "table": "bigquery-public-data.google_trends.hourly_top_rising_terms",
        "scope": "US",
        "granularity": "hourly",
        "window": "rolling 1 year",
        "note": "hourly rising dataset",
    },
]


def describe() -> List[Dict[str, str]]:
    return TABLE_META


def run_query(
    sql: str,
    project: Optional[str] = None,
    location: str = "US",
    credentials: Any = None,
) -> Any:
    """执行 BigQuery SQL；未安装/未认证时给出明确错误。"""
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise ImportError(
            "google-cloud-bigquery is required for BigQuery queries. "
            "pip install google-cloud-bigquery, then configure GOOGLE_APPLICATION_CREDENTIALS."
        ) from exc

    kwargs: Dict[str, Any] = {"location": location}
    if project:
        kwargs["project"] = project
    if credentials is not None:
        kwargs["credentials"] = credentials
    client = bigquery.Client(**kwargs)
    job = client.query(sql)
    return [list(row.values()) for row in job.result()]


def sample_sql(table: str = "bigquery-public-data.google_trends.top_terms") -> str:
    return (
        f"SELECT refresh_date, dma_name, term, rank, score "
        f"FROM `{table}` "
        f"WHERE refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) "
        f"LIMIT 100"
    )