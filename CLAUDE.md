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
  ├── POST /query  - 質問受信
  ├── Vertex AI Embedding でクエリベクトル化
  ├── ハイブリッド検索
  │    ├── BigQuery Vector Search（意味検索 Top-5）
  │    └── Elasticsearch 全文検索（kuromoji キーワード検索 Top-5）
  ├── RRF（Reciprocal Rank Fusion）リランク
  ├── プロンプト組み立て
  └── Vertex AI Gemini で回答生成
            ↓
[レスポンス]
  └── 回答文 + 根拠ドキュメント + 該当箇所

[Elastic Cloud]
  ├── Elasticsearch（kuromoji日本語全文検索）
  └── Kibana（管理UI）

[GitHub Actions]
  ├── doc-qa: main push(src/doc-qa) → test → build → push → deploy
  └── terraform: main push(terraform) → plan → apply
```

- **src/doc-qa/ingestion/**: Cloud Run Job - GCS取得→テキスト抽出→チャンク分割→Embedding→BigQuery/Elasticsearch格納
- **src/doc-qa/api/**: Cloud Run Service - FastAPI QA API（ハイブリッド検索→RRFリランク→Gemini回答生成）
- **src/elastic-search/**: Elastic Cloud基盤（Terraform管理、接続確認用）
- **terraform/**: GCS, BigQuery, Cloud Run (Job/Service), Artifact Registry, Cloud Scheduler, IAM のIaC定義
- **scripts/**: 共通ユーティリティ(core.py)、監視(Ingestion/API)、アップロード、クエリテスト
- **data/sample/**: サンプル社内規定ドキュメント（就業規則、経費精算規定、FAQ）
- **docs/**: 仕様・設計書、移行ロードマップ

## Tech Stack

- **LLM/RAG**: Vertex AI Embedding API, Vertex AI Gemini, BigQuery Vector Search
- **検索**: Elasticsearch（kuromoji日本語全文検索）+ BigQuery Vector Search（意味検索）のハイブリッド
- **API**: FastAPI (Cloud Run Service)
- **ドキュメント処理**: PyMuPDF, python-docx
- **Data**: BigQuery（ドキュメントチャンク + Embedding格納）, GCS（ドキュメント格納）
- **Infra**: Cloud Run (Job/Service), Artifact Registry, Cloud Scheduler, Secret Manager
- **IaC**: Terraform（GCP + Elastic Cloud）
- **CI/CD**: GitHub Actions（doc-qa + Terraform）
- **監視**: Discord通知（Ingestion監視・API健全性）
- **ログ**: JSON構造化ログ（Cloud Logging互換）

## GCP Setup

```bash
gcloud init
gcloud config set compute/region asia-northeast1
gcloud config set run/region asia-northeast1
gcloud services enable aiplatform.googleapis.com
```

## Language

このプロジェクトのドキュメントやコミットメッセージは日本語で記述する。
