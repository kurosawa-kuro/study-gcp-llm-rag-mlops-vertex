resource "google_cloud_run_v2_service" "doc_qa_api" {
  name     = "doc-qa-api"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}/doc-qa-api:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }

      env {
        name  = "BQ_DATASET"
        value = var.bq_dataset
      }

      env {
        name  = "BQ_TABLE"
        value = "documents"
      }

      env {
        name  = "ES_SECRET_NAME"
        value = var.es_secret_name
      }

      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }
    }

    service_account = google_service_account.doc_qa_runner.email
  }

  lifecycle {
    ignore_changes = [template]
  }

  depends_on = [
    google_artifact_registry_repository.myrepo,
    google_bigquery_table.documents,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.doc_qa_api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
