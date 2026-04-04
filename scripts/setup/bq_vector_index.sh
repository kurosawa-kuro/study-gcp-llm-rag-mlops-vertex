#!/usr/bin/env bash
# BigQuery Vector Index 作成（冪等・5000行未満はスキップ）
# Usage: scripts/setup/bq_vector_index.sh <PROJECT_ID> <BQ_DATASET> <BQ_TABLE>
set -euo pipefail

PROJECT_ID="${1:?PROJECT_ID is required}"
BQ_DATASET="${2:?BQ_DATASET is required}"
BQ_TABLE="${3:?BQ_TABLE is required}"

echo "=== BigQuery Vector Index 作成 ==="

# 既存チェック
if bq query --project_id="$PROJECT_ID" --use_legacy_sql=false --format=json \
  "SELECT index_name FROM \`${PROJECT_ID}.${BQ_DATASET}.INFORMATION_SCHEMA.VECTOR_INDEXES\` WHERE index_name = 'embedding_index'" 2>/dev/null \
  | grep -q 'embedding_index'; then
  echo "Vector Index embedding_index は既に存在します（スキップ）"
  exit 0
fi

# 行数チェック（IVF は最低5000行必要）
ROW_COUNT=$(bq query --project_id="$PROJECT_ID" --use_legacy_sql=false --format=csv --quiet \
  "SELECT COUNT(*) FROM \`${PROJECT_ID}.${BQ_DATASET}.${BQ_TABLE}\`" 2>/dev/null | tail -1)

if [ "$ROW_COUNT" -ge 5000 ] 2>/dev/null; then
  echo "Vector Index embedding_index を作成します（${ROW_COUNT} 行）..."
  bq query --project_id="$PROJECT_ID" --use_legacy_sql=false \
    "CREATE VECTOR INDEX IF NOT EXISTS embedding_index ON \`${PROJECT_ID}.${BQ_DATASET}.${BQ_TABLE}\`(embedding) OPTIONS (index_type = 'IVF', distance_type = 'COSINE')"
else
  echo "行数が5000未満（${ROW_COUNT} 行）のため Vector Index 作成をスキップ（VECTOR_SEARCH は Index なしでも動作します）"
fi
