"""scripts共通ユーティリティ"""

import json
import logging
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = ROOT / "env" / "config" / "application.yml"


def _load_app_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


_APP_CFG = _load_app_config()

# === プロジェクト定数（application.yml から読み込み）===
PROJECT_ID = _APP_CFG.get("gcp", {}).get("project_id", "mlops-dev-a")
REGION = _APP_CFG.get("gcp", {}).get("region", "asia-northeast1")
DATASET = _APP_CFG.get("bigquery", {}).get("dataset", "doc_qa_dataset")

# === Discord通知カラー ===
COLOR_SUCCESS = 3066993   # 緑
COLOR_WARNING = 16776960  # 黄
COLOR_FAILURE = 15158332  # 赤

logger = logging.getLogger("doc-qa")


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


def load_env() -> None:
    """プロジェクトルートの.envファイルを読み込む。"""
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def run(cmd: str, allow_fail: bool = False) -> None:
    """シェルコマンドを実行する。失敗時はsys.exit。"""
    logger.info(f"実行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=ROOT)
    if result.returncode != 0 and not allow_fail:
        logger.error(f"コマンド失敗: '{cmd}' (code={result.returncode})")
        sys.exit(result.returncode)


def dispatch(actions: dict[str, callable]) -> None:
    """CLI引数でアクションを振り分ける汎用ディスパッチャー。"""
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action not in actions:
        print(f"Usage: {sys.argv[0]} [{'/'.join(actions)}]")
        sys.exit(1)
    actions[action]()


def notify_discord(status: str, message: str, fields: list[dict] | None = None) -> None:
    """Discord Webhookで通知を送信する。"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.info("DISCORD_WEBHOOK_URL が未設定のため通知スキップ")
        return

    color_map = {"SUCCESS": COLOR_SUCCESS, "WARNING": COLOR_WARNING, "FAILED": COLOR_FAILURE}
    embed = {
        "title": message,
        "color": color_map.get(status, COLOR_FAILURE),
    }
    if fields:
        embed["fields"] = fields

    payload = {"embeds": [embed]}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)
    logger.info(f"Discord通知送信: {status}")
