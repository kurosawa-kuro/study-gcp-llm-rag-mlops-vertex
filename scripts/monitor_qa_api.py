"""QA API 健全性チェック + Discord通知"""

import urllib.request

from core import setup_logging, load_env, notify_discord

logger = setup_logging("doc-qa-monitor")


def main() -> None:
    load_env()
    import subprocess

    result = subprocess.run(
        "gcloud run services describe doc-qa-api --region asia-northeast1 --format 'value(status.url)'",
        shell=True, capture_output=True, text=True,
    )
    url = result.stdout.strip()
    if not url:
        notify_discord("FAILED", "QA API URL取得失敗")
        return

    try:
        req = urllib.request.Request(f"{url}/health", method="GET")
        resp = urllib.request.urlopen(req, timeout=10)
        if resp.status == 200:
            notify_discord("SUCCESS", "QA API 正常稼働中")
        else:
            notify_discord("WARNING", f"QA API ステータス: {resp.status}")
    except Exception as e:
        notify_discord("FAILED", f"QA API 異常: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
