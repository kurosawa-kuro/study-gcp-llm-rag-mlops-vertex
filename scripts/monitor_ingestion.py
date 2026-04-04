"""Ingestion Job 実行結果監視 + Discord通知"""

from core import setup_logging, load_env, run, notify_discord

logger = setup_logging("doc-qa-monitor")


def main() -> None:
    load_env()
    import subprocess

    result = subprocess.run(
        "gcloud run jobs executions list --job doc-qa-ingestion --region asia-northeast1 --limit 1 --format json",
        shell=True, capture_output=True, text=True,
    )

    if result.returncode != 0:
        notify_discord("FAILED", "Ingestion Job 実行履歴取得失敗")
        return

    import json
    executions = json.loads(result.stdout or "[]")
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
