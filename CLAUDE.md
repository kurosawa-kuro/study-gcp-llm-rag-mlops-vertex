# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

社内ドキュメント検索・QAシステム。Cloud Runベースで（Kubernetes不使用）ドキュメント取込パイプラインとQA APIを構築。
GCSにアップロードされたPDF/Word/TXTをチャンク分割・Embedding化し、BigQuery Vector Search + Elasticsearch ハイブリッド検索で関連箇所を取得、Vertex AI Geminiで根拠付き回答を生成する。
GCPプロジェクト: `mlops-dev-a`、リージョン: `asia-northeast1`

## Architecture

```
[ユーザー]
  └── PDFをGCSにアップロード
            ↓
[Cloud Run Job（Ingestion）]
  ├── GCSからドキュメント取得
  ├── テキスト抽出（PDF: pymupdf / Word: python-docx / TXT）
  ├── チャンク分割（800文字・50文字オーバーラップ）
  ├── Vertex AI Embedding API でベクトル化
  ├── BigQuery documents テーブルに格納（Vector Search用）
  └── Elasticsearch にインデックス登録（kuromoji全文検索用）
            ↓
[Cloud Scheduler]
  └── 毎日 9:00 JST に自動Ingestion実行
            ↓
[Cloud Run Service（QA API + React SPA）]
  ├── GET /        → React TypeScript SPA（QA検索 / Upload / Eval）
  ├── POST /query  → ハイブリッド検索 → RRFリランク → Gemini回答生成
  ├── POST /ingest → Cloud Run Jobs API で Ingestion Job 非同期実行
  └── GET /health  → ヘルスチェック
```

- **src/ingestion/**: Cloud Run Job - ドキュメント取込（extract/ embed/ store/）
- **src/api/**: Cloud Run Service - QA API + SPA配信（endpoints/ search/ generation/ static/）
- **src/frontend/**: React TypeScript SPA（Vite、ビルド出力 → src/api/static/）
- **src/pipeline/**: Vertex AI Pipeline（RAG評価パイプライン）
- **shared/config.py**: 共通設定ローダー（application.yml キャッシュ・ロギング）
- **shared/core.py**: スクリプト基盤（gcloud・run・notify_discord・load_env）
- **scripts/**: 運用スクリプト（eval/ monitor/ ops/ setup/）
- **terraform/**: GCP + Elastic Cloud IaC（モジュール分離: data/compute/elastic/registry/iam）
- **env/config/application.yml**: プロジェクト固有設定（非シークレット）の唯一の定義元
- **env/secret/credentials.yml**: 全クレデンシャル統合
- **data/sample/**: サンプル社内規定ドキュメント

## Config Architecture

```
env/config/application.yml    ← 全設定の唯一の定義元（Single Source of Truth）
        ↓
shared/config.py              ← 唯一の設定ローダー（キャッシュ付き）
        ↓
    ┌───┴───────────────┐
    ↓                   ↓
ingestion/main.py     api/endpoints/main.py   ← from config import get, setup_logging
shared/core.py        scripts/*/*.py          ← from core import ...
```

設定解決の優先順位: **環境変数 > application.yml > ハードコードデフォルト**
コンテナ内では `CONFIG_PATH` 環境変数でYAMLパスをオーバーライド。

## Tech Stack

- **LLM/RAG**: Vertex AI Embedding API, Google AI Studio Gemini（google-genai SDK）, BigQuery Vector Search
- **検索**: Elasticsearch（kuromoji アナライザー）+ BigQuery Vector Search のハイブリッド
- **API**: FastAPI (Cloud Run Service)
- **フロントエンド**: React TypeScript + Vite（FastAPI と同一ポートで配信）
- **IaC**: Terraform（モジュール分離: data/compute/elastic/registry/iam）
- **CI/CD**: GitHub Actions（doc-qa + Terraform）
- **監視**: Discord通知
- **ログ**: JSON構造化ログ（Cloud Logging互換）
- **評価**: Recall@K / MRR / Exact Match / ROUGE-L（scripts/eval/）

## Docker Build

build context はプロジェクトルート。`-f` で Dockerfile を指定:
```bash
docker build -f src/api/Dockerfile -t doc-qa-api .           # multi-stage: React ビルド + Python
docker build -f src/ingestion/Dockerfile -t doc-qa-ingestion .
```

## Language

このプロジェクトのドキュメントやコミットメッセージは日本語で記述する。
