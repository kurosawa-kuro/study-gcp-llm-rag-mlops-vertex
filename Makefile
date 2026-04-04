# === 共通設定（env/config/application.yml と同期すること）===
PROJECT_ID := mlops-dev-a
REGION := asia-northeast1
REPO := mlops-dev-a-docker
TAG := latest
BUCKET := mlops-dev-a-doc-qa
IMAGE_BASE := $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)
TF_DIR := terraform
TF_SA := terraform@$(PROJECT_ID).iam.gserviceaccount.com
COMPUTE_SA := $(shell gcloud projects describe $(PROJECT_ID) --format='value(projectNumber)' 2>/dev/null)-compute@developer.gserviceaccount.com
INGESTION_DIR := src/doc-qa/ingestion
INGESTION_IMAGE := $(IMAGE_BASE)/doc-qa-ingestion:$(TAG)
QA_API_DIR := src/doc-qa/api
QA_API_IMAGE := $(IMAGE_BASE)/doc-qa-api:$(TAG)

# =====================================================================
# ブートストラップ（冪等・全自動・初回〜再実行すべて対応）
# =====================================================================
.PHONY: bootstrap

bootstrap: gcp-setup tf-bootstrap ingestion-push qa-api-push tf-apply  ## 全環境構築（冪等）
	@echo "=== bootstrap 完了 ==="

# =====================================================================
# GCPセットアップ（全て冪等）
# =====================================================================
.PHONY: gcp-setup gcp-setup-apis gcp-setup-sa gcp-setup-vertex gcp-setup-docker

gcp-setup-apis:
	gcloud services enable \
	  artifactregistry.googleapis.com \
	  run.googleapis.com \
	  compute.googleapis.com \
	  iam.googleapis.com \
	  cloudresourcemanager.googleapis.com \
	  cloudscheduler.googleapis.com \
	  bigquery.googleapis.com \
	  aiplatform.googleapis.com \
	  generativelanguage.googleapis.com \
	  secretmanager.googleapis.com \
	  --project=$(PROJECT_ID)

gcp-setup-sa:
	@for ROLE in roles/editor roles/run.admin roles/resourcemanager.projectIamAdmin roles/secretmanager.admin; do \
	  gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	    --member="serviceAccount:$(TF_SA)" \
	    --role="$$ROLE" --quiet > /dev/null 2>&1; \
	done
	@echo "Terraform SA 権限設定完了"

gcp-setup-vertex:
	@gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$(COMPUTE_SA)" \
	  --role="roles/aiplatform.user" --quiet > /dev/null 2>&1
	@echo "Vertex AI 権限設定完了"

gcp-setup-docker:
	@gcloud auth configure-docker $(REGION)-docker.pkg.dev --quiet 2>/dev/null
	@echo "Docker 認証設定完了"

gcp-setup: gcp-setup-apis gcp-setup-sa gcp-setup-vertex gcp-setup-docker

# =====================================================================
# Terraform（冪等・import付き）
# =====================================================================
.PHONY: tf-init tf-plan tf-apply tf-apply-registry tf-bootstrap tf-destroy tf-fmt tf-validate

tf-init:
	@cd $(TF_DIR) && terraform init -input=false > /dev/null 2>&1
	@echo "Terraform init 完了"

tf-import-registry: tf-init
	@cd $(TF_DIR) && terraform state show module.registry.google_artifact_registry_repository.repo > /dev/null 2>&1 \
	  || terraform import -input=false module.registry.google_artifact_registry_repository.repo \
	       projects/$(PROJECT_ID)/locations/$(REGION)/repositories/$(REPO) 2>/dev/null \
	  || true
	@echo "Artifact Registry import 確認完了"

tf-bootstrap: tf-init tf-import-registry tf-apply-registry  ## Registry作成→import→イメージpush準備

tf-plan: tf-init
	cd $(TF_DIR) && terraform plan -input=false

tf-apply-registry: tf-init
	cd $(TF_DIR) && terraform apply -auto-approve -input=false -target=module.registry

tf-apply: tf-init
	cd $(TF_DIR) && terraform apply -auto-approve -input=false

tf-destroy: tf-init
	cd $(TF_DIR) && terraform destroy -input=false

tf-fmt:
	cd $(TF_DIR) && terraform fmt -recursive

tf-validate: tf-init
	cd $(TF_DIR) && terraform validate

# =====================================================================
# Ingestion（ドキュメント取込パイプライン）
# =====================================================================
.PHONY: ingestion-test ingestion-build ingestion-push ingestion-deploy ingestion-run ingestion-logs

ingestion-test:
	cd $(INGESTION_DIR) && PYTHONPATH=.:../../../shared python3 -m pytest -v tests/

ingestion-build:
	docker build -f $(INGESTION_DIR)/Dockerfile -t $(INGESTION_IMAGE) .

ingestion-push: ingestion-build
	docker push $(INGESTION_IMAGE)

ingestion-deploy: ingestion-push
	gcloud run jobs update doc-qa-ingestion --image $(INGESTION_IMAGE) --region $(REGION)

ingestion-run:
	gcloud run jobs execute doc-qa-ingestion --region $(REGION) --wait

ingestion-logs:
	gcloud run jobs executions list --job doc-qa-ingestion --region $(REGION) --limit 5

# =====================================================================
# QA API（社内ドキュメント QA サービス）
# =====================================================================
.PHONY: qa-api-test qa-api-build qa-api-push qa-api-deploy qa-api-logs qa-api-url qa-api-monitor

qa-api-test:
	cd $(QA_API_DIR) && PYTHONPATH=.:../../../shared python3 -m pytest -v tests/

qa-api-build:
	docker build -f $(QA_API_DIR)/Dockerfile -t $(QA_API_IMAGE) .

qa-api-push: qa-api-build
	docker push $(QA_API_IMAGE)

qa-api-deploy: qa-api-push
	gcloud run services update doc-qa-api --image $(QA_API_IMAGE) --region $(REGION)

qa-api-logs:
	gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="doc-qa-api"' \
		--limit 20 --format json

qa-api-url:
	@gcloud run services describe doc-qa-api --region $(REGION) --format 'value(status.url)'

qa-api-monitor:
	python3 scripts/monitor/qa_api.py

# =====================================================================
# 統合コマンド
# =====================================================================
.PHONY: deploy-all destroy-all deploy test help

deploy-all: bootstrap  ## 全構築（GCP設定→Terraform→イメージpush→apply）冪等

destroy-all: tf-destroy  ## 全GCPリソース削除
	@echo "=== 全リソース削除完了 ==="

deploy: ingestion-deploy qa-api-deploy  ## アプリのみ再デプロイ（build→push→update）

test: ingestion-test qa-api-test

help:
	@echo "=== 全体操作 ==="
	@echo "  make deploy-all         全構築（冪等・全自動）"
	@echo "  make destroy-all        全GCPリソース削除"
	@echo "  make deploy             アプリのみ再デプロイ"
	@echo "  make test               全テスト実行"
	@echo ""
	@echo "=== Setup ==="
	@echo "  make gcp-setup          GCP初回セットアップ"
	@echo ""
	@echo "=== Terraform ==="
	@echo "  make tf-plan            差分確認"
	@echo "  make tf-apply           全リソース反映"
	@echo "  make tf-destroy         全リソース削除"
	@echo "  make tf-fmt             フォーマット"
	@echo ""
	@echo "=== Ingestion ==="
	@echo "  make ingestion-test     テスト実行"
	@echo "  make ingestion-build    Dockerイメージビルド"
	@echo "  make ingestion-deploy   冪等デプロイ"
	@echo "  make ingestion-run      Cloud Run Job実行"
	@echo "  make ingestion-logs     実行履歴確認"
	@echo ""
	@echo "=== QA API ==="
	@echo "  make qa-api-test        テスト実行"
	@echo "  make qa-api-build       Dockerイメージビルド"
	@echo "  make qa-api-deploy      冪等デプロイ"
	@echo "  make qa-api-logs        ログ確認"
	@echo "  make qa-api-url         URL表示"
	@echo "  make qa-api-monitor     健全性チェック"
