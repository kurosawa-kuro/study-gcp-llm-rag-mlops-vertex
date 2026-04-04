variable "project_id" {
  default = "mlops-dev-a"
}

variable "region" {
  default = "asia-northeast1"
}

variable "repo_name" {
  default = "mlops-dev-a-docker"
}

variable "bucket_name" {
  default = "mlops-dev-a-doc-qa"
}

variable "bq_dataset" {
  default = "doc_qa_dataset"
}

variable "es_secret_name" {
  description = "Secret Manager に格納した Elastic Cloud APIキー名"
  default     = "elastic-cloud-api-key"
}
