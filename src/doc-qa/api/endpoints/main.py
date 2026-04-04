"""社内ドキュメント QA API エントリーポイント

POST /query   - 質問に対して根拠付きで回答
POST /ingest  - 指定GCSパスのドキュメントを手動Ingestion
GET  /health  - ヘルスチェック
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

import vertexai
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery, secretmanager
from elasticsearch import Elasticsearch
from pydantic import BaseModel

from config import get, setup_logging
from search.embedder import embed_query
from search.retriever import hybrid_search
from search.reranker import reciprocal_rank_fusion
from generation.generator import generate_answer

logger = setup_logging("doc-qa")

# === 環境変数 > application.yml > デフォルト値 ===
GCP_PROJECT = os.environ.get("GCP_PROJECT", get("gcp.project_id", "mlops-dev-a"))
BQ_DATASET = os.environ.get("BQ_DATASET", get("bigquery.dataset", "doc_qa_dataset"))
BQ_TABLE = os.environ.get("BQ_TABLE", get("bigquery.table", "documents"))
ES_SECRET_NAME = os.environ.get("ES_SECRET_NAME", get("elasticsearch.secret_name", "elastic-cloud-api-key"))
ES_INDEX = os.environ.get("ES_INDEX", get("elasticsearch.index_name", "doc-qa"))
DEFAULT_TOP_K = get("api.default_top_k", 5)
RRF_K = get("api.rrf_k", 60)
API_VERSION = get("api.version", "1.0.0")


class QueryRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_TOP_K


class SourceDoc(BaseModel):
    doc_name: str
    page_number: int | None
    content: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDoc]


class IngestRequest(BaseModel):
    gcs_path: str


class IngestResponse(BaseModel):
    doc_id: str
    chunks: int
    status: str


bq_client: bigquery.Client | None = None
es_client: Elasticsearch | None = None


def _get_es_credentials() -> tuple[str, str]:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT}/secrets/{ES_SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode("utf-8"))
    return secret["cloud_url"], secret["api_key"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bq_client, es_client
    logger.info("QA API 起動中...")
    vertexai.init(project=GCP_PROJECT, location=get("gcp.region", "asia-northeast1"))
    bq_client = bigquery.Client(project=GCP_PROJECT)
    es_url, es_key = _get_es_credentials()
    es_client = Elasticsearch(es_url, api_key=es_key)
    logger.info("QA API 起動完了")
    yield
    logger.info("QA API シャットダウン")


app = FastAPI(title="社内ドキュメント QA API", version=API_VERSION, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "version": API_VERSION}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    logger.info(f"クエリ受信: {req.query}")
    try:
        query_embedding = embed_query(req.query)

        vector_results, fulltext_results = hybrid_search(
            bq_client, es_client, BQ_DATASET, BQ_TABLE, ES_INDEX,
            req.query, query_embedding, req.top_k,
        )

        ranked = reciprocal_rank_fusion(vector_results, fulltext_results, req.top_k, k=RRF_K)
        answer = generate_answer(req.query, ranked)

        sources = [
            SourceDoc(
                doc_name=doc["doc_name"],
                page_number=doc.get("page_number"),
                content=doc["content"][:200],
                score=round(doc.get("rrf_score", 0), 4),
            )
            for doc in ranked
        ]
        return QueryResponse(answer=answer, sources=sources)

    except Exception as e:
        logger.error(f"クエリ処理エラー: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
def ingest_endpoint(req: IngestRequest):
    logger.info(f"手動Ingestion: {req.gcs_path}")
    try:
        from google.cloud import run_v2

        region = get("gcp.region", "asia-northeast1")
        jobs_client = run_v2.JobsClient()
        job_name = f"projects/{GCP_PROJECT}/locations/{region}/jobs/doc-qa-ingestion"

        override = run_v2.RunJobRequest.Overrides(
            container_overrides=[
                run_v2.RunJobRequest.Overrides.ContainerOverride(
                    env=[run_v2.EnvVar(name="TARGET_GCS_PATH", value=req.gcs_path)],
                )
            ],
        )
        request = run_v2.RunJobRequest(name=job_name, overrides=override)
        operation = jobs_client.run_job(request=request)

        logger.info(f"Ingestion Job 実行開始: {req.gcs_path}")
        return IngestResponse(
            doc_id=operation.metadata.name if hasattr(operation, "metadata") else "submitted",
            chunks=0,
            status="accepted",
        )

    except Exception as e:
        logger.error(f"Ingestionエラー: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
