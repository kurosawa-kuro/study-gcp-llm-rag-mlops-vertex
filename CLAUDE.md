# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MLOps・検索基盤・LLMの学習プロジェクト。Cloud Runベースで（Kubernetes不使用）MLパイプラインと検索基盤を構築。Vertex AI Pipeline（KFP v2）で学習→評価→品質ゲート→Champion比較→デプロイの6 Step Pipeline を実装済み。
GCPプロジェクト: `mlops-dev-a`、リージョン: `asia-northeast1`

## Architecture

```
[Cloud Run Job (batch)]
   ├── データ取得（California Housing）
   ├── 特徴量生成 → 学習（scikit-learn RandomForest）
   ├── 評価（RMSE, MAE） → MLflow記録
   ├── モデル保存 → [GCS models/]（リトライ付き）
   ├── ログ出力 → [GCS logs/]
   └── メトリクス投入 → [BigQuery mlops.metrics]（リトライ付き）

[BigQuery]
   └── metrics テーブル → 最良モデル選択（90日リテンション・日別パーティション）

[Cloud Run Service (FastAPI API)]
   ├── BigQueryから最良モデルパス取得（リトライ付き）
   ├── GCSからモデルロード（リトライ付き）
   └── POST /predict で推論レスポンス

[Cloud Run Job (elastic-search)]
   ├── Elastic Cloud 接続（Secret Manager経由でAPIキー取得）
   ├── ドキュメント投入・検索
   └── クリーンアップ

[Elastic Cloud]
   ├── Elasticsearch（データ格納・全文検索）
   └── Kibana（管理UI・APIキー発行）

[Vertex AI Pipeline（KFP v2・実装済み）]
   ├── Step1: load_data（California Housingデータ取得・分割）
   ├── Step2: train_model（RandomForest学習）
   ├── Step3: evaluate_model（RMSE/MAE算出→GCS保存→BigQuery記録）
   ├── Step4: quality_gate（RMSE閾値チェック→不合格時Discord通知）
   ├── Step5: compare_champion（BigQuery Champion比較→改善なし時Discord通知）
   └── Step6: deploy_model（Vertex AI Endpoint デプロイ→Discord通知）

[Vertex AI（MVP実装済み）]
   └── Notebook: 学習→Model Registry→Endpoint→推論→クリーンアップ
```

- **batch/**: Cloud Run Job - データ取得→学習→評価(MLflow)→モデル保存(GCS)→ログ出力(GCS)→メトリクス投入(BigQuery)
- **api/**: Cloud Run Service - BigQueryで最良モデル選択→GCSからロード→FastAPIで推論レスポンス
- **pipeline/**: Vertex AI Pipeline（KFP v2） - 6 Stepの学習→評価→品質ゲート→Champion比較→デプロイ Pipeline
- **elastic-search/**: Cloud Run Job - Elastic Cloud接続確認（Terraform管理、.envで設定一元管理）
- **terraform/**: GCS, BigQuery, Cloud Run (Job/Service), Artifact Registry, Cloud Scheduler, Vertex AI IAM のIaC定義
- **scripts/**: 共通ユーティリティ(core.py)、監視(batch/API)、ドリフト検知、デプロイ、リセット（Vertex AIクリーンアップ含む）
- **notebooks/**: Vertex AI学習用ノートブック（MVP実装済み）
- **docs/**: 各領域の仕様・設計書（vertex/, vertex-pipeline/, elastic-search/, llm/）

## Tech Stack

- **ML**: scikit-learn, MLflow, pandas, Vertex AI (Model Registry, Endpoint, Pipelines)
- **Pipeline**: KFP v2（Lightweight Python Components）、品質ゲート、Champion/Challenger比較
- **LLM（予定）**: ELECTRA (日本語Embedding), FAISS, Vertex AI Gemini (RAG)
- **API**: FastAPI (Cloud Run Service)
- **検索**: Elastic Cloud (Elasticsearch + Kibana)
- **Data**: BigQuery（評価メトリクス蓄積・最良モデル選択・90日リテンション）
- **Infra**: Cloud Run (Job/Service), GCS, Artifact Registry, Cloud Scheduler, Secret Manager
- **IaC**: Terraform（GCP + Elastic Cloud）
- **CI/CD**: GitHub Actions（batch/API/Terraform 3本）
- **監視**: Discord通知（batch監視・API健全性・モデルドリフト検知・Pipeline通知）
- **ログ**: JSON構造化ログ（Cloud Logging互換）

## GCP Setup

```bash
gcloud init
gcloud config set compute/region asia-northeast1
gcloud config set run/region asia-northeast1
```

## Language

このプロジェクトのドキュメントやコミットメッセージは日本語で記述する。
