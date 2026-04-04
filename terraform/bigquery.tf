resource "google_bigquery_dataset" "doc_qa" {
  dataset_id = var.bq_dataset
  location   = var.region
}

resource "google_bigquery_table" "documents" {
  dataset_id          = google_bigquery_dataset.doc_qa.dataset_id
  table_id            = "documents"
  deletion_protection = false

  schema = jsonencode([
    { name = "id", type = "STRING", mode = "REQUIRED", description = "チャンクID（UUID）" },
    { name = "doc_id", type = "STRING", mode = "REQUIRED", description = "元ドキュメントID" },
    { name = "doc_name", type = "STRING", mode = "REQUIRED", description = "ファイル名" },
    { name = "content", type = "STRING", mode = "REQUIRED", description = "チャンクテキスト" },
    { name = "chunk_index", type = "INT64", mode = "NULLABLE", description = "チャンク番号" },
    { name = "page_number", type = "INT64", mode = "NULLABLE", description = "ページ番号" },
    { name = "gcs_path", type = "STRING", mode = "NULLABLE", description = "GCS上のパス" },
    { name = "embedding", type = "FLOAT64", mode = "REPEATED", description = "Vertex AI Embedding（768次元）" },
    { name = "created_at", type = "TIMESTAMP", mode = "NULLABLE", description = "作成日時" },
  ])
}

# NOTE: BigQuery Vector Index は Terraform 未対応のため、手動で以下を実行する:
# CREATE VECTOR INDEX embedding_index
# ON doc_qa_dataset.documents(embedding)
# OPTIONS (distance_type = 'COSINE');
