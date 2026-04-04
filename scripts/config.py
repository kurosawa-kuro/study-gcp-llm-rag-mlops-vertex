"""プロジェクト設定ローダー（env/config/application.yml を読み込む）"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "env" / "config" / "application.yml"

_config: dict | None = None


def load_config(path: Path = CONFIG_PATH) -> dict:
    """application.yml を読み込んでキャッシュする。"""
    global _config
    if _config is None:
        with open(path, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get(key: str, default: Any = None) -> Any:
    """ドット区切りキーで設定値を取得する。

    例: get("gcp.project_id") → "mlops-dev-a"
         get("ingestion.chunk_size") → 800
    """
    config = load_config()
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value
