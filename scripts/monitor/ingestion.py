"""Ingestion Job 実行結果監視 + Discord通知"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import logger, load_env, gcloud, notify_discord, REGION


def main() -> None:
    load_env()

    output = gcloud(f"run jobs executions list --job doc-qa-ingestion --region {REGION} --limit 1 --format json")
    if not output:
        notify_discord("FAILED", "Ingestion Job 実行履歴取得失敗")
        return

    executions = json.loads(output)
    if not executions:
        logger.info("実行履歴なし")
        return

    latest = executions[0]
    status = latest.get("status", {}).get("conditions", [{}])[-1].get("type", "Unknown")

    if status == "Completed":
        notify_discord("SUCCESS", "Ingestion Job 正常終了")
    else:
        notify_discord("FAILED", f"Ingestion Job 異常: {status}")


if __name__ == "__main__":
    main()
