# === プロジェクト共通 ===
variable "project_id" {
  description = "GCP プロジェクトID"
  default     = "mlops-dev-a"
}

variable "region" {
  description = "GCP リージョン"
  default     = "asia-northeast1"
}

# === Artifact Registry ===
variable "repo_name" {
  description = "Docker リポジトリ名"
  default     = "mlops-dev-a-docker"
}

# === データ層 ===
variable "bucket_name" {
  description = "GCS ドキュメントバケット名"
  default     = "mlops-dev-a-doc-qa"
}

variable "bq_dataset" {
  description = "BigQuery データセット名"
  default     = "doc_qa_dataset"
}

# === Elastic Cloud ===
variable "es_deployment_name" {
  description = "Elastic Cloud デプロイメント名"
  default     = "doc-qa-es"
}

variable "es_secret_name" {
  description = "Secret Manager に格納した Elastic Cloud APIキー名"
  default     = "elastic-cloud-api-key"
}

variable "elastic_cloud_api_key" {
  description = "Elastic Cloud Org APIキー（ec プロバイダ認証用）"
  sensitive   = true
}

# === Gemini ===
variable "google_ai_studio_api_key" {
  description = "Google AI Studio APIキー"
  sensitive   = true
}
