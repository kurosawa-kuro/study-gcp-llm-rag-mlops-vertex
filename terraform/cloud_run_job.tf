resource "google_cloud_run_v2_job" "doc_qa_ingestion" {
  name     = "doc-qa-ingestion"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}/doc-qa-ingestion:latest"

        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GCS_BUCKET"
          value = var.bucket_name
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
            memory = "2Gi"
            cpu    = "2"
          }
        }
      }

      timeout = "1800s"

      service_account = google_service_account.doc_qa_runner.email
    }
  }

  lifecycle {
    ignore_changes = [template]
  }

  depends_on = [
    google_artifact_registry_repository.myrepo,
    google_storage_bucket.doc_qa,
    google_bigquery_table.documents,
  ]
}
