"""gt-scraper: Google Trends 全量数据面抓取包。

把 Google Trends 所有可爬取的数据形态封装成统一接口，
端点清单来自已安装库源码（trendspy/trendspyg/pytrends）逐行核对 + 官方文档 + 实测。
"""

from .errors import (
    RateLimitedError,
    HttpError,
    ParseError,
    SurfaceNotAvailableError,
)
from .http import HttpClient
from .registry import DATA_SURFACES, SURFACE_INDEX, surface_spec

__all__ = [
    "HttpClient",
    "DATA_SURFACES",
    "SURFACE_INDEX",
    "surface_spec",
    "RateLimitedError",
    "HttpError",
    "ParseError",
    "SurfaceNotAvailableError",
]

__version__ = "0.1.0"