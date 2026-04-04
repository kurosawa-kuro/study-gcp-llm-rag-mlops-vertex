include .env
export

# Terraform用環境変数（TF_VAR_で自動認識）
export TF_VAR_project_id            := $(PROJECT_ID)
export TF_VAR_region                := $(REGION)
export TF_VAR_deployment_name       := $(DEPLOYMENT_NAME)
export TF_VAR_job_name              := $(JOB_NAME)
export TF_VAR_repo_name             := $(REPO_NAME)
export TF_VAR_secret_name           := $(SECRET_NAME)
export TF_VAR_elastic_api_key       := $(ELASTIC_API_KEY)
export TF_VAR_elastic_cloud_api_key := $(ELASTIC_CLOUD_API_KEY)

SCRIPTS := PYTHONPATH=scripts python3

.PHONY: run install build push docker-run clean \
        auth-docker execute logs \
        deploy-all destroy-all \
        tf-init tf-plan tf-apply tf-apply-infra tf-import tf-destroy help

# ===== ローカル =====

run:
	python3 main.py

install:
	pip install -r requirements.txt

build:
	$(SCRIPTS) scripts/docker_ops.py build

push:
	$(SCRIPTS) scripts/docker_ops.py push

docker-run:
	$(SCRIPTS) scripts/docker_ops.py docker-run

clean:
	$(SCRIPTS) scripts/docker_ops.py clean

# ===== GCP操作 =====

auth-docker:
	$(SCRIPTS) scripts/gcp_ops.py auth-docker

execute:
	$(SCRIPTS) scripts/gcp_ops.py execute

logs:
	$(SCRIPTS) scripts/gcp_ops.py logs

# ===== デプロイ =====

deploy-all:
	$(MAKE) tf-apply-infra
	$(MAKE) push
	$(MAKE) tf-apply

destroy-all:
	$(MAKE) tf-destroy
	$(MAKE) clean

# ===== Terraform =====

tf-init:
	$(SCRIPTS) scripts/tf_ops.py init

tf-plan:
	$(SCRIPTS) scripts/tf_ops.py plan

tf-apply:
	$(SCRIPTS) scripts/tf_ops.py apply

tf-apply-infra:
	$(SCRIPTS) scripts/tf_ops.py apply-infra

tf-import:
	$(SCRIPTS) scripts/tf_ops.py import

tf-destroy:
	$(SCRIPTS) scripts/tf_ops.py destroy

# ===== ヘルプ =====

help:
	@echo "ローカル:"
	@echo "  make install      依存パッケージインストール"
	@echo "  make run          ローカル実行"
	@echo "  make build        Dockerイメージビルド"
	@echo "  make push         Artifact Registryへpush"
	@echo "  make docker-run   Docker実行"
	@echo "  make clean        ローカルイメージ削除"
	@echo ""
	@echo "GCP操作:"
	@echo "  make auth-docker  Docker認証設定（初回のみ）"
	@echo "  make execute      Cloud Run Job実行"
	@echo "  make logs         ログ確認"
	@echo ""
	@echo "デプロイ:"
	@echo "  make deploy-all   全構築 (infra→push→job)"
	@echo "  make destroy-all  全削除 (terraform destroy→docker clean)"
	@echo ""
	@echo "Terraform:"
	@echo "  make tf-init      プロバイダ初期化"
	@echo "  make tf-plan      差分確認"
	@echo "  make tf-apply     全リソース適用"
	@echo "  make tf-apply-infra インフラのみ適用（Cloud Run Job除外）"
	@echo "  make tf-import    既存リソースをstateにimport"
	@echo "  make tf-destroy   全リソース削除"
