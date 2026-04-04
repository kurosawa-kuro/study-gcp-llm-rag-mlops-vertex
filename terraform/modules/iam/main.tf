# 認証認可: Service Account + 最小権限 IAM バインディング
# NOTE: Cloud Run Job invoker は compute モジュール側で管理（循環依存回避）

resource "google_service_account" "doc_qa_runner" {
  account_id   = "doc-qa-runner"
  display_name = "Doc QA Runner"
}

# --- BigQuery ---

resource "google_bigquery_dataset_iam_member" "bq_editor" {
  dataset_id = var.bq_dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# --- GCS ---

resource "google_storage_bucket_iam_member" "gcs_reader" {
  bucket = var.bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# --- Vertex AI ---

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# --- Secret Manager ---

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

resource "google_secret_manager_secret_iam_member" "es_secret_access" {
  secret_id = var.es_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}
