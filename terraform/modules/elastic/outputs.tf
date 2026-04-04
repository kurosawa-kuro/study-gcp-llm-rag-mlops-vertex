output "elasticsearch_endpoint" {
  value = ec_deployment.doc_qa.elasticsearch.https_endpoint
}

output "secret_id" {
  value = google_secret_manager_secret.elastic_api_key.id
}

output "secret_name" {
  value = google_secret_manager_secret.elastic_api_key.secret_id
}
