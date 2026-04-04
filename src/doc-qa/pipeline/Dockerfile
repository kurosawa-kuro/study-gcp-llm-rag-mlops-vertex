# Build context: プロジェクトルート
# docker build -f src/doc-qa/pipeline/Dockerfile -t doc-qa-eval .
#
# evaluate.py のパス解決（_ROOT）を維持するためディレクトリ構造を再現
FROM python:3.11-slim

WORKDIR /app

# API依存関係（evaluate.py が使う search/generation モジュール用）
COPY src/doc-qa/api/requirements.txt /tmp/api-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt \
    && pip install --no-cache-dir google-cloud-storage>=2.14.0

# shared 設定ローダー
COPY shared/ /app/shared/

# API モジュール（search / generation）
COPY src/doc-qa/api/ /app/src/doc-qa/api/

# 評価スクリプト + クエリデータ
COPY scripts/eval/ /app/scripts/eval/

# アプリケーション設定
COPY env/config/application.yml /app/env/config/application.yml

# Pipeline 用エントリポイント（環境変数を引数から設定）
COPY src/doc-qa/pipeline/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV CONFIG_PATH=/app/env/config/application.yml

ENTRYPOINT ["python", "/app/scripts/eval/evaluate.py"]
