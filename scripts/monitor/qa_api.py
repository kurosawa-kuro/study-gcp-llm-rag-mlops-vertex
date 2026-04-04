"""QA API 健全性チェック + Discord通知"""

import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import logger, load_env, gcloud, notify_discord, REGION


def main() -> None:
    load_env()

    url = gcloud(f"run services describe doc-qa-api --region {REGION} --format 'value(status.url)'")
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
