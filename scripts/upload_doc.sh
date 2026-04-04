#!/usr/bin/env bash
# GCS へドキュメントをアップロードする
# Usage: ./scripts/upload_doc.sh <local_file_or_dir>

set -euo pipefail

BUCKET="mlops-dev-a-doc-qa"

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file_or_directory>"
  echo "Example: $0 data/sample/"
  exit 1
fi

echo "=== アップロード先: gs://${BUCKET}/ ==="
gsutil -m cp -r "$@" "gs://${BUCKET}/"
echo "=== アップロード完了 ==="
