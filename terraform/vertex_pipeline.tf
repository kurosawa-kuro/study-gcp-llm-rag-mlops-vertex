# Vertex AI Pipeline 用 IAM ロール
#
# NOTE: roles/aiplatform.user はプロジェクトレベル IAM のため
# Terraform SA の権限では管理不可。gcp.mk (make gcp-setup-vertex) で付与する。

# Pipeline が GCS バケットにアーティファクトを読み書きするための権限
resource "google_storage_bucket_iam_member" "pipeline_storage_admin" {
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}
