resource "google_cloud_scheduler_job" "doc_qa_ingestion_schedule" {
  name      = "doc-qa-ingestion-schedule"
  region    = var.region
  schedule  = "0 9 * * *"
  time_zone = "Asia/Tokyo"

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/doc-qa-ingestion:run"
    http_method = "POST"

    oauth_token {
      service_account_email = google_service_account.doc_qa_runner.email
    }
  }

  depends_on = [google_cloud_run_v2_job.doc_qa_ingestion]
}
