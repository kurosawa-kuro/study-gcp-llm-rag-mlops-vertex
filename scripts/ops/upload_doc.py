"""GCS へドキュメントをアップロードする

Usage: python scripts/ops/upload_doc.py <file_or_directory> [...]
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shared"))

from core import logger, get, run

BUCKET = get("storage.bucket_name", "mlops-dev-a-doc-qa")


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_or_directory> [...]")
        print(f"Example: {sys.argv[0]} data/sample/")
        sys.exit(1)

    targets = " ".join(sys.argv[1:])
    dest = f"gs://{BUCKET}/"

    logger.info(f"アップロード先: {dest}")
    run(f"gsutil -m cp -r {targets} {dest}")
    logger.info("アップロード完了")


if __name__ == "__main__":
    main()
