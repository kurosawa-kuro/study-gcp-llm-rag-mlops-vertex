# === Terraform ===
TF_DIR := terraform

.PHONY: tf-init tf-plan tf-apply tf-apply-registry tf-destroy tf-fmt tf-validate

tf-init:
	cd $(TF_DIR) && terraform init -input=false

tf-plan: tf-init  ## 差分確認
	cd $(TF_DIR) && terraform plan

tf-apply-registry: tf-init  ## Artifact Registry のみ適用
	cd $(TF_DIR) && terraform apply -auto-approve \
	  -target=module.registry

tf-apply: tf-init  ## 全リソース適用
	cd $(TF_DIR) && terraform apply -auto-approve

tf-destroy: tf-init
	cd $(TF_DIR) && terraform destroy

tf-fmt:
	cd $(TF_DIR) && terraform fmt -recursive

tf-validate: tf-init
	cd $(TF_DIR) && terraform validate
