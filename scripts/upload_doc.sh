#!/usr/bin/env bash
# GCS へドキュメントをアップロードする
# Usage: ./scripts/upload_doc.sh <local_file_or_dir>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${SCRIPT_DIR}/../env/config/application.yml"

# application.yml から bucket_name を取得
BUCKET=$(python3 -c "
import yaml
with open('${CONFIG}') as f:
    cfg = yaml.safe_load(f)
print(cfg['storage']['bucket_name'])
")

if [ $# -eq 0 ]; then
  echo "Usage: $0 <file_or_directory>"
  echo "Example: $0 data/sample/"
  exit 1
fi

echo "=== アップロード先: gs://${BUCKET}/ ==="
gsutil -m cp -r "$@" "gs://${BUCKET}/"
echo "=== アップロード完了 ==="
