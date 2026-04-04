terraform {
  required_providers {
    ec = {
      source  = "elastic/ec"
      version = "~> 0.12"
    }
  }
}

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
    config = {
      plugins = ["analysis-kuromoji"]
    }
  }

  kibana = {
    size       = "1g"
    zone_count = 1
  }
}

# Secret Manager: Elasticsearch 接続情報（ec_deployment から自動取得）
resource "google_secret_manager_secret" "elastic_api_key" {
  secret_id = var.secret_name
  replication {
    user_managed {
      replicas { location = var.region }
    }
  }
}

resource "google_secret_manager_secret_version" "elastic_api_key" {
  secret = google_secret_manager_secret.elastic_api_key.id
  secret_data = jsonencode({
    cloud_url = ec_deployment.doc_qa.elasticsearch.https_endpoint
    username  = ec_deployment.doc_qa.elasticsearch_username
    password  = ec_deployment.doc_qa.elasticsearch_password
  })
}
