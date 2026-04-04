#!/bin/bash
# Vertex AI Pipeline コンテナ用エントリポイント
# 最初の3引数を環境変数に設定し、残りを evaluate.py に渡す

export GCP_PROJECT="$1"
export GCP_REGION="$2"
export GOOGLE_AI_STUDIO_API_KEY="$3"
shift 3

exec python /app/scripts/eval/evaluate.py "$@"
