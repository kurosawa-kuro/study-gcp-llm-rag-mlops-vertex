output "bucket_name" {
  value = google_storage_bucket.doc_qa.name
}

output "bq_dataset_id" {
  value = google_bigquery_dataset.doc_qa.dataset_id
}

output "bq_table_id" {
  value = google_bigquery_table.documents.table_id
}
