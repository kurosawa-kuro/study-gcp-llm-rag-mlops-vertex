output "ingestion_job_name" {
  value = google_cloud_run_v2_job.ingestion.name
}

output "api_service_name" {
  value = google_cloud_run_v2_service.api.name
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}
