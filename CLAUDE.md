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
[Cloud Run Service（QA API）]
  ├── POST /query → ハイブリッド検索 → RRFリランク → Gemini回答生成
  ├── POST /ingest → Cloud Run Jobs API で Ingestion Job 非同期実行
  └── GET /health → ヘルスチェック
```

- **src/doc-qa/ingestion/**: Cloud Run Job - ドキュメント取込パイプライン
- **src/doc-qa/api/**: Cloud Run Service - FastAPI QA API
- **scripts/config.py**: 共通設定ローダー（application.yml キャッシュ・ロギング）
- **scripts/core.py**: 共通ユーティリティ（Discord通知・env読み込み・dispatch）
- **terraform/**: GCP + Elastic Cloud IaC（モジュール分離: data/compute/elastic/registry/iam）
- **env/config/application.yml**: プロジェクト固有設定（非シークレット）の唯一の定義元
- **env/secret/credentials.yml**: 全クレデンシャル統合
- **data/sample/**: サンプル社内規定ドキュメント

## Config Architecture

```
env/config/application.yml    ← 全設定の唯一の定義元（Single Source of Truth）
        ↓
scripts/config.py             ← 唯一の設定ローダー（キャッシュ付き）
        ↓
    ┌───┴───────────────┐
    ↓                   ↓
ingestion/main.py     api/main.py      ← from config import get, setup_logging
scripts/core.py       scripts/es_*.py  ← from config import get
```

設定解決の優先順位: **環境変数 > application.yml > ハードコードデフォルト**
コンテナ内では `CONFIG_PATH` 環境変数でYAMLパスをオーバーライド。

## Tech Stack

- **LLM/RAG**: Vertex AI Embedding API, Vertex AI Gemini, BigQuery Vector Search
- **検索**: Elasticsearch（kuromoji）+ BigQuery Vector Search のハイブリッド
- **API**: FastAPI (Cloud Run Service)
- **IaC**: Terraform（モジュール分離: data/compute/elastic/registry/iam）
- **CI/CD**: GitHub Actions（doc-qa + Terraform）
- **監視**: Discord通知
- **ログ**: JSON構造化ログ（Cloud Logging互換）

## Docker Build

build context はプロジェクトルート。`-f` で Dockerfile を指定:
```bash
docker build -f src/doc-qa/api/Dockerfile -t doc-qa-api .
docker build -f src/doc-qa/ingestion/Dockerfile -t doc-qa-ingestion .
```

## Language

このプロジェクトのドキュメントやコミットメッセージは日本語で記述する。
