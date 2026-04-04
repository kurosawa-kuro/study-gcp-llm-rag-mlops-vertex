# === モジュール呼び出し ===
#
# 依存グラフ:
#   registry ─────────────────────────┐
#   data ──────── iam ──────── compute
#   elastic ─────┘       ┌────┘
#                        │
# iam は SA を作成し compute に渡す（一方向、循環なし）

locals {
  image_base = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}"
}

# --- Artifact Registry ---
module "registry" {
  source = "./modules/registry"

  region    = var.region
  repo_name = var.repo_name
}

# --- データ層（GCS + BigQuery）---
module "data" {
  source = "./modules/data"

  region      = var.region
  bucket_name = var.bucket_name
  bq_dataset  = var.bq_dataset
}

# --- Elastic Cloud + Secret Manager ---
module "elastic" {
  source = "./modules/elastic"

  region          = var.region
  deployment_name = var.es_deployment_name
  secret_name     = var.es_secret_name
}

# --- IAM（SA + 権限バインディング）---
module "iam" {
  source = "./modules/iam"

  project_id    = var.project_id
  bucket_name   = module.data.bucket_name
  bq_dataset_id = module.data.bq_dataset_id
  es_secret_id  = module.elastic.secret_id
}

# --- コンピュート層（Cloud Run + Scheduler）---
# depends_on: elastic モジュール全体（ec_deployment + Secret Version 書込み）の
# 完了を待ってから Cloud Run Service を作成する。secret_name だけでは
# ec_deployment の完了を待てない（Secret リソース自体は2秒で作成されるため）。
module "compute" {
  source = "./modules/compute"

  project_id            = var.project_id
  region                = var.region
  image_base            = local.image_base
  bucket_name           = module.data.bucket_name
  bq_dataset            = module.data.bq_dataset_id
  es_secret_name        = module.elastic.secret_name
  service_account_email = module.iam.service_account_email
  google_ai_studio_api_key        = var.google_ai_studio_api_key

  depends_on = [module.elastic]
}
