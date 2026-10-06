"""底层 HTTP 会话：cookie、代理、XSSI 剥离、429 识别与重试。

Google Trends 的内部端点返回带 XSSI 前缀的 JS/JSON：
- /trends/api/* 通常前缀是 `)]}',`（4 字符），pytrends 用 trim_chars=4/5。
- embed 端点返回 `JSON.parse('...')`（trendspy _extract_embedded_data）。
本项目统一提供 `get_json(trim=...)` 与 `get_text`。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import requests

from .errors import ConfigError, HttpError, ParseError, RateLimitedError
from .endpoints import BASE

_SORRY_MARKERS = ("/sorry/index", "unusual traffic", "unusual traffic from your network")


class HttpClient:
    def __init__(
        self,
        proxy: Optional[str] = None,
        direct: bool = False,
        hl: str = "en-US",
        tz: int = 360,
        request_delay_s: float = 4.0,
        max_retries: int = 3,
        backoff_s: float = 8.0,
        user_agent: Optional[str] = None,
    ):
        # 环境变量优先，config 兜底
        env_proxy = os.environ.get("GT_PROXY") or os.environ.get("HTTPS_PROXY")
        self.direct = bool(os.environ.get("GT_DIRECT")) or direct
        self.proxy = None if self.direct else (env_proxy or proxy)
        self.hl = hl
        self.tz = tz
        self.request_delay_s = request_delay_s
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Language": self.hl,
                "Referer": f"{BASE}/trends/explore",
            }
        )
        if self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}
        self._last_request_at: float = 0.0
        self._cookie_ready = False

    # ------------------------------------------------------------------ #
    # cookie 初始化
    # ------------------------------------------------------------------ #
    def ensure_cookies(self) -> None:
        """先访问 Explore/Trending 页拿 NID 等 cookie。

        pytrends 用 GET /trends/explore/?geo=US 取 cookie；trendspyg 用
        GET https://trends.google.com/。这里忽略页面状态码，只保留 cookie。
        """
        if self._cookie_ready:
            return
        try:
            self._throttle()
            self.session.get(
                f"{BASE}/trends/explore",
                params={"geo": "US", "hl": self.hl},
                timeout=15,
            )
        except requests.RequestException:
            # 拿不到 cookie 仍继续（referer 已带），部分端点可工作
            pass
        self._cookie_ready = True

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_at
        if elapsed < self.request_delay_s:
            time.sleep(self.request_delay_s - elapsed)
        self._last_request_at = time.time()

    # ------------------------------------------------------------------ #
    # 请求
    # ------------------------------------------------------------------ #
    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        trim: int = 0,
        as_json: bool = True,
        need_cookie: bool = True,
    ) -> Any:
        if need_cookie:
            self.ensure_cookies()

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.request(
                    method, url, params=params, data=data, headers=headers, timeout=20
                )
            except requests.RequestException as exc:
                last_exc = exc
                self._sleep_retry(attempt)
                continue

            text = resp.text or ""
            if resp.status_code == 429 or any(m in text for m in _SORRY_MARKERS):
                raise RateLimitedError(
                    f"status={resp.status_code}, url={url}, marker_text={text[:120]!r}"
                )
            if resp.status_code != 200:
                last_exc = HttpError(resp.status_code, f"GET {url} -> {resp.status_code}")
                self._sleep_retry(attempt)
                continue

            if as_json:
                return self._parse_json(text, trim, url)
            return text

        if isinstance(last_exc, HttpError):
            raise last_exc
        raise last_exc or HttpError(0, f"Request failed: {url}")

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, trim: int = 0) -> Any:
        return self.request("GET", url, params=params, trim=trim, as_json=True)

    def get_text(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        return self.request("GET", url, params=params, as_json=False)

    def post_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, Any]] = None,
        trim: int = 0,
    ) -> Any:
        return self.request(
            "POST", url, params=params, data=data, headers=headers, trim=trim, as_json=True
        )

    def _sleep_retry(self, attempt: int) -> None:
        if attempt >= self.max_retries:
            return
        self._throttle()
        time.sleep(self.backoff_s * (attempt + 1))

    @staticmethod
    def _parse_json(text: str, trim: int, url: str) -> Any:
        if trim:
            text = text[trim:]
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            # 有些端点返回多行，最后一行才是 JSON（trendspy 的兼容策略）
            lines = text.splitlines()
            if lines:
                try:
                    return json.loads(lines[-1])
                except json.JSONDecodeError:
                    pass
            raise ParseError(f"JSON parse failed for {url}: {exc} | head={text[:160]!r}")


def load_config(path: str = "config.json") -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    import json as _json

    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)


def client_from_config(cfg: Dict[str, Any] | None = None) -> HttpClient:
    cfg = cfg or {}
    proxy = cfg.get("proxy") or os.environ.get("GT_PROXY")
    direct = cfg.get("direct", False)
    if not direct and proxy is None and not os.environ.get("GT_DIRECT"):
        # 不强制代理：有代理用代理，没有则直连
        direct = True
    return HttpClient(
        proxy=proxy,
        direct=direct,
        hl=cfg.get("hl", "en-US"),
        tz=cfg.get("tz", 360),
        request_delay_s=cfg.get("request_delay_s", 4.0),
        max_retries=cfg.get("max_retries", 3),
        backoff_s=cfg.get("backoff_s", 8.0),
        user_agent=cfg.get("user_agent"),
    )