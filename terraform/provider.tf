terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    ec = {
      source  = "elastic/ec"
      version = "~> 0.12"
    }
  }
}

locals {
  credentials = yamldecode(file("${path.module}/../env/secret/credentials.yml"))
}

provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = jsonencode(local.credentials.gcp_service_account)
}

provider "ec" {
  apikey = var.elastic_cloud_api_key
}
