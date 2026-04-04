"""社内ドキュメント QA API エントリーポイント

POST /query   - 質問に対して根拠付きで回答
POST /ingest  - 指定GCSパスのドキュメントを手動Ingestion
GET  /health  - ヘルスチェック
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager

import vertexai
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery, secretmanager
from elasticsearch import Elasticsearch
from pydantic import BaseModel

from embedder import embed_query
from retriever import hybrid_search
from reranker import reciprocal_rank_fusion
from generator import generate_answer

# === ログ設定 ===
logger = logging.getLogger("doc-qa")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    json.dumps({
        "severity": "%(levelname)s",
        "message": "%(message)s",
        "logger": "%(name)s",
        "timestamp": "%(asctime)s",
    }, ensure_ascii=False)
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# === 環境変数 ===
GCP_PROJECT = os.environ.get("GCP_PROJECT", "mlops-dev-a")
BQ_DATASET = os.environ.get("BQ_DATASET", "doc_qa_dataset")
BQ_TABLE = os.environ.get("BQ_TABLE", "documents")
ES_SECRET_NAME = os.environ.get("ES_SECRET_NAME", "elastic-cloud-api-key")
ES_INDEX = os.environ.get("ES_INDEX", "doc-qa")


# === リクエスト/レスポンスモデル ===
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


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


# === グローバルクライアント ===
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
    """起動時にクライアントを初期化する。"""
    global bq_client, es_client

    logger.info("QA API 起動中...")
    vertexai.init(project=GCP_PROJECT, location="asia-northeast1")
    bq_client = bigquery.Client(project=GCP_PROJECT)
    es_url, es_key = _get_es_credentials()
    es_client = Elasticsearch(es_url, api_key=es_key)
    logger.info("QA API 起動完了")

    yield

    logger.info("QA API シャットダウン")


app = FastAPI(title="社内ドキュメント QA API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(req: QueryRequest):
    """質問に対して根拠ドキュメント付きで回答する。"""
    logger.info(f"クエリ受信: {req.query}")

    try:
        # 1. クエリベクトル化
        query_embedding = embed_query(req.query)

        # 2. ハイブリッド検索
        vector_results, fulltext_results = hybrid_search(
            bq_client, es_client, BQ_DATASET, BQ_TABLE, ES_INDEX,
            req.query, query_embedding, req.top_k,
        )

        # 3. RRF リランク
        ranked = reciprocal_rank_fusion(vector_results, fulltext_results, req.top_k)

        # 4. Gemini で回答生成
        answer = generate_answer(req.query, ranked)

        # 5. レスポンス組み立て
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
    """指定GCSパスのドキュメントを手動Ingestionする。"""
    logger.info(f"手動Ingestion: {req.gcs_path}")

    try:
        import subprocess
        result = subprocess.run(
            ["python", "-c", f"""
import os
os.environ['TARGET_GCS_PATH'] = '{req.gcs_path}'
os.environ['GCP_PROJECT'] = '{GCP_PROJECT}'
os.environ['GCS_BUCKET'] = os.environ.get('GCS_BUCKET', 'mlops-dev-a-doc-qa')
os.environ['BQ_DATASET'] = '{BQ_DATASET}'
os.environ['BQ_TABLE'] = '{BQ_TABLE}'
os.environ['ES_SECRET_NAME'] = '{ES_SECRET_NAME}'
from importlib.machinery import SourceFileLoader
ingestion = SourceFileLoader('main', '/app/ingestion/main.py').load_module()
ingestion.main()
"""],
            capture_output=True, text=True, timeout=600,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        return IngestResponse(doc_id="pending", chunks=0, status="success")

    except Exception as e:
        logger.error(f"Ingestionエラー: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
