resource "google_service_account" "doc_qa_runner" {
  account_id   = "doc-qa-runner"
  display_name = "Doc QA Runner"
}

# BigQuery データ読み書き
resource "google_bigquery_dataset_iam_member" "bq_editor" {
  dataset_id = google_bigquery_dataset.doc_qa.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# BigQuery ジョブ実行
resource "google_project_iam_member" "bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# GCS ドキュメント読み取り
resource "google_storage_bucket_iam_member" "gcs_reader" {
  bucket = google_storage_bucket.doc_qa.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# Vertex AI Embedding / Gemini 呼び出し
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# Secret Manager（Elastic Cloud APIキー取得）
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}

# Cloud Run Job 実行権限（Scheduler → Ingestion Job）
resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_job.doc_qa_ingestion.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.doc_qa_runner.email}"
}
