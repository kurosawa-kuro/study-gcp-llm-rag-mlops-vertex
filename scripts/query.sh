#!/usr/bin/env bash
# QA API にクエリを送信する
# Usage: ./scripts/query.sh "質問テキスト" [top_k]

set -euo pipefail

QUERY="${1:?Usage: $0 <query> [top_k]}"
TOP_K="${2:-5}"

# API URL を取得
API_URL=$(gcloud run services describe doc-qa-api --region asia-northeast1 --format 'value(status.url)')

echo "=== QA クエリ送信 ==="
echo "質問: ${QUERY}"
echo "API: ${API_URL}"
echo ""

curl -s -X POST "${API_URL}/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${QUERY}\", \"top_k\": ${TOP_K}}" | python3 -m json.tool
