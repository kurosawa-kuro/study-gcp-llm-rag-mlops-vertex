"""QA API にクエリを送信する

Usage: python scripts/query.py "質問テキスト" [top_k]
"""

import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "shared"))

from core import logger, gcloud, REGION


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <query> [top_k]")
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) >= 3 else 5

    api_url = gcloud(f"run services describe doc-qa-api --region {REGION} --format 'value(status.url)'")
    if not api_url:
        logger.error("QA API URL取得失敗")
        sys.exit(1)

    logger.info(f"質問: {query}")
    logger.info(f"API: {api_url}")

    payload = json.dumps({"query": query, "top_k": top_k}).encode()
    req = urllib.request.Request(
        f"{api_url}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=60)
    body = json.loads(resp.read().decode())
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
