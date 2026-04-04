output "api_url" {
  description = "QA API の URL"
  value       = module.compute.api_url
}

output "elasticsearch_endpoint" {
  description = "Elasticsearch エンドポイント"
  value       = module.elastic.elasticsearch_endpoint
}

output "service_account_email" {
  description = "実行用 Service Account"
  value       = module.iam.service_account_email
}
