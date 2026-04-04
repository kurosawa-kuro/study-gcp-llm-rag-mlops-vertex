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
  elastic_api_key = var.elastic_api_key
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
module "compute" {
  source = "./modules/compute"

  project_id            = var.project_id
  region                = var.region
  image_base            = local.image_base
  bucket_name           = module.data.bucket_name
  bq_dataset            = module.data.bq_dataset_id
  es_secret_name        = module.elastic.secret_name
  service_account_email = module.iam.service_account_email
}
