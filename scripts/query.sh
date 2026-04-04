#!/usr/bin/env bash
# QA API にクエリを送信する
# Usage: ./scripts/query.sh "質問テキスト" [top_k]

set -euo pipefail

QUERY="${1:?Usage: $0 <query> [top_k]}"
TOP_K="${2:-5}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="${SCRIPT_DIR}/../env/config/application.yml"

# application.yml から region を取得
REGION=$(python3 -c "
import yaml
with open('${CONFIG}') as f:
    cfg = yaml.safe_load(f)
print(cfg['gcp']['region'])
")

# API URL を取得
API_URL=$(gcloud run services describe doc-qa-api --region "${REGION}" --format 'value(status.url)')

echo "=== QA クエリ送信 ==="
echo "質問: ${QUERY}"
echo "API: ${API_URL}"
echo ""

curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${QUERY}\", \"top_k\": ${TOP_K}}" | python3 -m json.tool
