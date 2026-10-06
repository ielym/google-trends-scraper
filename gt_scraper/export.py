"""导出：JSON 信封 + CSV。

所有抓取输出统一带 `_meta`（surface / captured_at / params / status / error），
便于审计与后续治理。
"""

from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def write_json(payload: Any, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    return path


def write_csv(rows: List[Dict[str, Any]], path: str) -> str:
    if not rows:
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def envelope(
    surface: str,
    payload: Any,
    params: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    source: str = "google-trends",
) -> Dict[str, Any]:
    return {
        "source": source,
        "surface": surface,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "params": params or {},
        "status": "ok" if error is None else "error",
        "error": error,
        "records": payload,
    }