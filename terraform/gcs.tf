resource "google_storage_bucket" "doc_qa" {
  name     = var.bucket_name
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = true
}
