include .env
export

# Terraform用環境変数（TF_VAR_で自動認識）
# ※ Terraform定義は統合済み terraform/ を参照
export TF_VAR_elastic_api_key       := $(ELASTIC_API_KEY)
export TF_VAR_elastic_cloud_api_key := $(ELASTIC_CLOUD_API_KEY)

# プロジェクトルートの scripts/ を参照
SCRIPTS_DIR := $(shell cd ../.. && pwd)/scripts
SCRIPTS := PYTHONPATH=$(SCRIPTS_DIR) python3

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
	$(SCRIPTS) $(SCRIPTS_DIR)/es_docker_ops.py build

push:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_docker_ops.py push

docker-run:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_docker_ops.py docker-run

clean:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_docker_ops.py clean

# ===== GCP操作 =====

auth-docker:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_gcp_ops.py auth-docker

execute:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_gcp_ops.py execute

logs:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_gcp_ops.py logs

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
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py init

tf-plan:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py plan

tf-apply:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py apply

tf-apply-infra:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py apply-infra

tf-import:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py import

tf-destroy:
	$(SCRIPTS) $(SCRIPTS_DIR)/es_tf_ops.py destroy

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
	@echo "  make tf-apply-infra インフラのみ適用（Elastic Cloud関連のみ）"
	@echo "  make tf-import    既存リソースをstateにimport"
	@echo "  make tf-destroy   全リソース削除"
