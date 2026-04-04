# === 共通設定（env/config/application.yml と同期すること）===
PROJECT_ID := mlops-dev-a
REGION := asia-northeast1
REPO := mlops-dev-a-docker
TAG := latest
BUCKET := mlops-dev-a-doc-qa
IMAGE_BASE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)

include makefiles/gcp.mk
include makefiles/terraform.mk
include makefiles/ingestion.mk
include makefiles/doc-qa-api.mk

# === 統合コマンド ===
.PHONY: deploy test help

deploy: ingestion-deploy qa-api-deploy  ## 全体デプロイ（Ingestion + QA API）

test: ingestion-test qa-api-test  ## 全テスト一括実行

help:  ## コマンド一覧表示
	@echo "=== Setup ==="
	@echo "  make gcp-setup          GCP初回セットアップ一括"
	@echo ""
	@echo "=== Terraform ==="
	@echo "  make tf-init            初期化"
	@echo "  make tf-plan            差分確認"
	@echo "  make tf-apply           全リソース反映"
	@echo "  make tf-destroy         全リソース削除"
	@echo "  make tf-fmt             フォーマット"
	@echo ""
	@echo "=== Ingestion（ドキュメント取込） ==="
	@echo "  make ingestion-test     テスト実行"
	@echo "  make ingestion-build    Dockerイメージビルド"
	@echo "  make ingestion-push     ビルド & push"
	@echo "  make ingestion-deploy   冪等デプロイ"
	@echo "  make ingestion-run      Cloud Run Job実行"
	@echo "  make ingestion-logs     実行履歴確認"
	@echo ""
	@echo "=== QA API（社内ドキュメントQA） ==="
	@echo "  make qa-api-test        テスト実行"
	@echo "  make qa-api-build       Dockerイメージビルド"
	@echo "  make qa-api-push        ビルド & push"
	@echo "  make qa-api-deploy      冪等デプロイ"
	@echo "  make qa-api-logs        ログ確認"
	@echo "  make qa-api-url         URL表示"
	@echo "  make qa-api-monitor     健全性チェック + Discord通知"
	@echo ""
	@echo "=== 統合 ==="
	@echo "  make deploy             全体デプロイ（Ingestion + QA API）"
	@echo "  make test               全テスト一括実行"
