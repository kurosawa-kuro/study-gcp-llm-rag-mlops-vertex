# Elastic Cloud デプロイメント
resource "ec_deployment" "hello" {
  name                   = var.deployment_name
  region                 = "gcp-${var.region}"
  version                = "9.3.2"
  deployment_template_id = "gcp-storage-optimized"

  elasticsearch = {
    hot = {
      autoscaling = {}
      size        = "1g"
      zone_count  = 1
    }
  }

  kibana = {
    size       = "1g"
    zone_count = 1
  }
}

# Artifact Registry
resource "google_artifact_registry_repository" "hello" {
  repository_id = var.repo_name
  location      = var.region
  format        = "DOCKER"
}

# Secret Manager
resource "google_secret_manager_secret" "elastic_api_key" {
  secret_id = var.secret_name
  replication {
    user_managed {
      replicas { location = var.region }
    }
  }
}

resource "google_secret_manager_secret_version" "elastic_api_key" {
  secret      = google_secret_manager_secret.elastic_api_key.id
  secret_data = var.elastic_api_key
}

# IAM: Cloud Run → Secret Manager
resource "google_secret_manager_secret_iam_member" "hello" {
  secret_id = google_secret_manager_secret.elastic_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

data "google_project" "project" {}

# Cloud Run Job
resource "google_cloud_run_v2_job" "hello" {
  name     = var.job_name
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repo_name}/${var.job_name}:latest"

        env {
          name  = "ELASTIC_CLOUD_URL"
          value = ec_deployment.hello.elasticsearch.https_endpoint
        }
        env {
          name = "ELASTIC_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.elastic_api_key.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [google_secret_manager_secret_iam_member.hello]
}
