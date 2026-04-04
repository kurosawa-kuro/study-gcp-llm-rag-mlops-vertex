"""プロジェクト共通設定・ロギング

全モジュールはこのファイルから設定を取得する。
- application.yml のロード（キャッシュ付き）
- ドット区切りキーアクセス: get("gcp.project_id")
- JSON構造化ロガー: setup_logging()

コンテナ内では環境変数 CONFIG_PATH でYAMLパスをオーバーライド可能。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# === アプリケーションルート ===
# shared/ → プロジェクトルート
APP_ROOT = Path(__file__).resolve().parent.parent

# === 設定ファイルパス（環境変数でオーバーライド可能）===
CONFIG_PATH = Path(os.environ.get(
    "CONFIG_PATH",
    str(APP_ROOT / "env" / "config" / "application.yml"),
))

_config: dict | None = None


def load_config() -> dict:
    """application.yml を読み込んでキャッシュする。"""
    global _config
    if _config is not None:
        return _config
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    else:
        _config = {}
    return _config


def get(key: str, default: Any = None) -> Any:
    """ドット区切りキーで設定値を取得する。

    例: get("gcp.project_id") → "mlops-dev-a"
         get("ingestion.chunk_size") → 800
    """
    cfg = load_config()
    for k in key.split("."):
        if isinstance(cfg, dict) and k in cfg:
            cfg = cfg[k]
        else:
            return default
    return cfg


def setup_logging(name: str = "doc-qa") -> logging.Logger:
    """JSON構造化ログを設定する。Cloud Logging互換。"""
    log = logging.getLogger(name)
    if log.handlers:
        return log

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        json.dumps({
            "severity": "%(levelname)s",
            "message": "%(message)s",
            "logger": "%(name)s",
            "timestamp": "%(asctime)s",
        }, ensure_ascii=False)
    ))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log
