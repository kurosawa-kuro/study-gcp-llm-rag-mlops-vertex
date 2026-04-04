variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "image_base" {
  description = "Artifact Registry のイメージベースパス（例: asia-northeast1-docker.pkg.dev/project/repo）"
  type        = string
}

variable "bucket_name" {
  type = string
}

variable "bq_dataset" {
  type = string
}

variable "es_secret_name" {
  type = string
}

variable "service_account_email" {
  type = string
}
