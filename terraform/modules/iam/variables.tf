variable "project_id" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "bq_dataset_id" {
  type = string
}

variable "es_secret_id" {
  description = "Elastic Cloud Secret Manager のリソースID"
  type        = string
}
