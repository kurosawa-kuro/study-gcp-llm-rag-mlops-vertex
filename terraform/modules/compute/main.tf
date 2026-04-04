# コンピュート層: Cloud Run Job（Ingestion）+ Service（QA API）+ Scheduler

resource "google_cloud_run_v2_job" "ingestion" {
  name     = "doc-qa-ingestion"
  location = var.region

  template {
    template {
      containers {
        image = "${var.image_base}/doc-qa-ingestion:latest"

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

      timeout         = "1800s"
      service_account = var.service_account_email
    }
  }

  lifecycle {
    ignore_changes = [template]
  }
}

resource "google_cloud_run_v2_service" "api" {
  name     = "doc-qa-api"
  location = var.region

  template {
    containers {
      image = "${var.image_base}/doc-qa-api:latest"

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

      env {
        name  = "ES_INDEX"
        value = "doc-qa"
      }

      env {
        name  = "GCS_BUCKET"
        value = var.bucket_name
      }

      env {
        name  = "GOOGLE_AI_STUDIO_API_KEY"
        value = var.google_ai_studio_api_key
      }

      resources {
        limits = {
          memory = "1Gi"
          cpu    = "1"
        }
      }
    }

    service_account = var.service_account_email
  }

  lifecycle {
    ignore_changes = [template]
  }
}

# QA API を公開
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Ingestion Job 実行権限（Scheduler / API → Job）
resource "google_cloud_run_v2_job_iam_member" "job_invoker" {
  name     = google_cloud_run_v2_job.ingestion.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}

# 日次自動 Ingestion
resource "google_cloud_scheduler_job" "ingestion_schedule" {
  name      = "doc-qa-ingestion-schedule"
  region    = var.region
  schedule  = "0 9 * * *"
  time_zone = "Asia/Tokyo"

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/doc-qa-ingestion:run"
    http_method = "POST"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }

  depends_on = [google_cloud_run_v2_job.ingestion]
}

# === RAG評価パイプライン ===

# 評価用 Docker イメージで直接評価を実行する Cloud Run Job
resource "google_cloud_run_v2_job" "eval" {
  name     = "doc-qa-eval"
  location = var.region

  template {
    template {
      containers {
        image = "${var.image_base}/doc-qa-eval:latest"

        args = ["--search-type", "hybrid", "--save-as", "scheduled",
                "--gcs-upload", "gs://${var.bucket_name}/eval-results"]

        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GCP_REGION"
          value = var.region
        }

        env {
          name  = "ES_SECRET_NAME"
          value = var.es_secret_name
        }

        env {
          name  = "GOOGLE_AI_STUDIO_API_KEY"
          value = var.google_ai_studio_api_key
        }

        resources {
          limits = {
            memory = "2Gi"
            cpu    = "2"
          }
        }
      }

      timeout         = "1800s"
      service_account = var.service_account_email
    }
  }

  lifecycle {
    ignore_changes = [template]
  }
}

# 週次評価スケジュール（毎週日曜 22:00 JST）
resource "google_cloud_scheduler_job" "eval_schedule" {
  name      = "doc-qa-eval-schedule"
  region    = var.region
  schedule  = "0 22 * * 0"
  time_zone = "Asia/Tokyo"

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/doc-qa-eval:run"
    http_method = "POST"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }

  depends_on = [google_cloud_run_v2_job.eval]
}

# === Vertex AI Pipeline スケジュール ===
# NOTE: Vertex AI Pipeline スケジュールは Terraform ではなく CI/CD (run_pipeline.py schedule) で管理。
# 理由: google_vertex_ai_pipeline_schedule リソースが Terraform Provider に存在しないため。
# IAM: doc-qa-runner SA は roles/aiplatform.user を保持（iam モジュールで管理）。
# Pipeline JSON: gs://mlops-dev-a-doc-qa/pipeline-artifacts/eval_pipeline.json に CI/CD で配置。
# 詳細: src/doc-qa/pipeline/run_pipeline.py schedule コマンドを参照。
