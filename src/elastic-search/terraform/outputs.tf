output "elasticsearch_endpoint" {
  value = ec_deployment.hello.elasticsearch.https_endpoint
}

output "cloud_run_job_name" {
  value = google_cloud_run_v2_job.hello.name
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}"
}
