export interface QueryRequest {
  query: string
  top_k?: number
}

export interface SourceDoc {
  doc_name: string
  page_number: number | null
  content: string
  score: number
}

export interface QueryResponse {
  answer: string
  sources: SourceDoc[]
}

export interface IngestRequest {
  gcs_path: string
}

export interface IngestResponse {
  doc_id: string
  chunks: number
  status: string
}

export interface HealthResponse {
  status: string
  version: string
}
