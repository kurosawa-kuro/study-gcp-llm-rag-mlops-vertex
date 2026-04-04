# 外部SaaS: Elastic Cloud デプロイメント + Secret Manager

resource "ec_deployment" "doc_qa" {
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

# Secret Manager: Elasticsearch 接続情報
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
