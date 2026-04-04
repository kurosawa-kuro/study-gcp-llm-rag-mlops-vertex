"""スクリプト共通基盤

全スクリプトの冒頭で `from core import ...` するだけで
設定・ロギング・gcloud・Discord通知が使える。

提供するもの:
  - get(): application.yml からの設定取得
  - logger: 初期化済みロガー
  - gcloud(): gcloud コマンド実行（出力を返す）
  - run(): シェルコマンド実行（失敗時 sys.exit）
  - notify_discord(): Discord 通知
  - load_env(): .env 読み込み
  - REGION / PROJECT_ID: application.yml から取得済み定数
"""

import json
import logging
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from config import get, setup_logging, APP_ROOT  # noqa: F401

# === 初期化済みオブジェクト ===
logger: logging.Logger = setup_logging("doc-qa")

# === application.yml から取得済み定数 ===
PROJECT_ID: str = get("gcp.project_id", "mlops-dev-a")
REGION: str = get("gcp.region", "asia-northeast1")


def load_env() -> None:
    """プロジェクトルートの .env を読み込む。"""
    env_file = APP_ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def run(cmd: str, capture: bool = False) -> subprocess.CompletedProcess:
    """シェルコマンドを実行する。失敗時は sys.exit。"""
    logger.info(f"実行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=capture)
    if result.returncode != 0:
        if capture and result.stderr:
            logger.error(result.stderr.strip())
        logger.error(f"コマンド失敗: (code={result.returncode})")
        sys.exit(result.returncode)
    return result


def gcloud(args: str) -> str:
    """gcloud コマンドを実行し、stdout を返す。失敗時は空文字。"""
    result = subprocess.run(
        f"gcloud {args}",
        shell=True, capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.warning(f"gcloud 失敗: {result.stderr.strip()}")
        return ""
    return result.stdout.strip()


def notify_discord(status: str, message: str) -> None:
    """Discord Webhook で通知を送信する。"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.info("DISCORD_WEBHOOK_URL が未設定のため通知スキップ")
        return

    color_map = {"SUCCESS": 3066993, "WARNING": 16776960, "FAILED": 15158332}
    payload = {"embeds": [{"title": message, "color": color_map.get(status, 15158332)}]}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    logger.info(f"Discord通知送信: {status}")
