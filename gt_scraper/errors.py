"""自定义异常。"""


class GtScraperError(Exception):
    """基类。"""


class RateLimitedError(GtScraperError):
    """HTTP 429 / /sorry/index 重定向：出口被 Google 限流。

    官方没有公开配额；实测同出口连续请求会进入长封期（见
    google-trends-research/evidence/experiments/EXP-007）。不要用代理轮换去
    规避——官方 ToS 禁止（UST-011）。降低频率、换时段、换出口后重试。
    """

    def __init__(self, message="Rate limited by Google Trends (429/redirect)"):
        super().__init__(message)


class HttpError(GtScraperError):
    def __init__(self, status_code, message=None):
        self.status_code = status_code
        super().__init__(message or f"HTTP {status_code}")


class ParseError(GtScraperError):
    """XSSI 剥离后 JSON 解析失败。"""


class SurfaceNotAvailableError(GtScraperError):
    """该数据面当前不可用（如 topcharts 已被 Google 移除/404）。"""


class ConfigError(GtScraperError):
    """配置错误（如缺代理、缺凭据）。"""