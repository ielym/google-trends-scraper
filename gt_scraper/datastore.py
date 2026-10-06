"""GoogleTrends/data 官方开源数据集（Datastore）。

该仓库是 Google 官方发布的策展 CSV（选举、体育、事件、品牌等），
本次盘点 GitHub API 显示当前 master 分支 112 个 CSV（加上 .xlsx 的富媒体样例）。
这里提供：列出全部文件、按模式过滤、下载 CSV。
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

import requests

from .errors import HttpError

API_CONTENTS = "https://api.github.com/repos/{owner}/{repo}/contents/{path}"
RAW_BLOB = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


class DatastoreClient:
    def __init__(
        self,
        owner: str = "GoogleTrends",
        repo: str = "data",
        branch: str = "master",
    ):
        self.owner = owner
        self.repo = repo
        self.branch = branch

    def list_files(self, path: str = "") -> List[Dict[str, str]]:
        """GitHub API 列出仓库文件（只兼容顶层/单层；目录需逐层拉取）。"""
        url = API_CONTENTS.format(owner=self.owner, repo=self.repo, path=path)
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            raise HttpError(resp.status_code, f"GitHub API {url}")
        data = resp.json()
        if isinstance(data, dict) and data.get("type") == "file":
            return [{"name": data["name"], "path": data["path"], "download_url": data.get("download_url", "")}]
        return [
            {
                "name": item["name"],
                "path": item["path"],
                "type": item.get("type"),
                "download_url": item.get("download_url", ""),
            }
            for item in data
        ]

    def list_csv(self, pattern: str = r"\.csv$") -> List[Dict[str, str]]:
        files = self.list_files()
        pat = re.compile(pattern, re.I)
        return [f for f in files if f.get("download_url") and pat.search(f["name"])]

    def download_csv(self, path: str, out_dir: str) -> str:
        """下载单个 CSV 到 out_dir，返回本地路径。"""
        os.makedirs(out_dir, exist_ok=True)
        local = os.path.join(out_dir, os.path.basename(path))
        url = RAW_BLOB.format(
            owner=self.owner, repo=self.repo, branch=self.branch, path=path
        )
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise HttpError(resp.status_code, f"download {url}")
        with open(local, "wb") as f:
            f.write(resp.content)
        return local

    def download_all_csv(self, out_dir: str, limit: Optional[int] = None) -> List[str]:
        files = self.list_csv()
        if limit:
            files = files[:limit]
        saved = []
        for f in files:
            saved.append(self.download_csv(f["path"], out_dir))
        return saved