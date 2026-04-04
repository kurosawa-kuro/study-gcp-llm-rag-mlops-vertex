"""Ingestion パイプライン エントリーポイント

GCS からドキュメントを取得 → テキスト抽出 → チャンク分割 →
Vertex AI Embedding → BigQuery格納 → Elasticsearch登録

設定値は env/config/application.yml から読み込む。
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml
import vertexai
from google.cloud import bigquery, secretmanager, storage

from chunker import split_into_chunks
from embedder import generate_embeddings
from es_writer import create_es_client, write_chunks_to_es
from extractor import extract_text
from bq_writer import write_chunks_to_bq

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

# === 設定読み込み ===
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "env" / "config" / "application.yml"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


CFG = _load_config()

# 環境変数 > application.yml > デフォルト値 の優先順で解決
GCP_PROJECT = os.environ.get("GCP_PROJECT", CFG.get("gcp", {}).get("project_id", "mlops-dev-a"))
GCS_BUCKET = os.environ.get("GCS_BUCKET", CFG.get("storage", {}).get("bucket_name", "mlops-dev-a-doc-qa"))
BQ_DATASET = os.environ.get("BQ_DATASET", CFG.get("bigquery", {}).get("dataset", "doc_qa_dataset"))
BQ_TABLE = os.environ.get("BQ_TABLE", CFG.get("bigquery", {}).get("table", "documents"))
ES_SECRET_NAME = os.environ.get("ES_SECRET_NAME", CFG.get("elasticsearch", {}).get("secret_name", "elastic-cloud-api-key"))
TARGET_GCS_PATH = os.environ.get("TARGET_GCS_PATH", "")

# Ingestion 固有設定
INGESTION_CFG = CFG.get("ingestion", {})
CHUNK_SIZE = INGESTION_CFG.get("chunk_size", 800)
CHUNK_OVERLAP = INGESTION_CFG.get("chunk_overlap", 50)
EMBEDDING_MODEL = INGESTION_CFG.get("embedding_model", "text-multilingual-embedding-002")
EMBEDDING_BATCH_SIZE = INGESTION_CFG.get("embedding_batch_size", 100)
SUPPORTED_EXTENSIONS = tuple(INGESTION_CFG.get("supported_extensions", [".pdf", ".docx", ".doc", ".txt"]))


def get_es_credentials() -> tuple[str, str]:
    """Secret Manager から Elastic Cloud の接続情報を取得する。"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT}/secrets/{ES_SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret = json.loads(response.payload.data.decode("utf-8"))
    return secret["cloud_url"], secret["api_key"]


def list_documents(gcs_client: storage.Client, bucket_name: str) -> list[storage.Blob]:
    """GCS バケットから処理対象ドキュメントを列挙する。"""
    bucket = gcs_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs())
    return [b for b in blobs if b.name.lower().endswith(SUPPORTED_EXTENSIONS)]


def process_document(
    blob: storage.Blob,
    bq_client: bigquery.Client,
    es_client,
) -> dict:
    """1ファイルを処理してBigQuery/Elasticsearchに格納する。"""
    doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"gs://{blob.bucket.name}/{blob.name}"))
    doc_name = blob.name.split("/")[-1]
    gcs_path = f"gs://{blob.bucket.name}/{blob.name}"
    now = datetime.now(timezone.utc).isoformat()

    logger.info(f"処理開始: {doc_name} (doc_id={doc_id})")

    # 1. ダウンロード
    with tempfile.NamedTemporaryFile(suffix=f"_{doc_name}", delete=False) as tmp:
        blob.download_to_filename(tmp.name)
        local_path = tmp.name

    # 2. テキスト抽出
    full_text, pages = extract_text(local_path)
    logger.info(f"テキスト抽出完了: {len(full_text)} 文字, {len(pages)} ページ")

    # 3. チャンク分割（application.yml の設定値を使用）
    chunks = split_into_chunks(full_text, pages, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    logger.info(f"チャンク分割完了: {len(chunks)} チャンク (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    if not chunks:
        logger.warning(f"空のドキュメント: {doc_name}")
        return {"doc_id": doc_id, "chunks": 0, "status": "skipped"}

    # 4. Embedding生成（application.yml の設定値を使用）
    texts = [c["content"] for c in chunks]
    embeddings = generate_embeddings(texts, model_name=EMBEDDING_MODEL, batch_size=EMBEDDING_BATCH_SIZE)

    # 5. BigQuery格納
    write_chunks_to_bq(bq_client, BQ_DATASET, BQ_TABLE, doc_id, doc_name, gcs_path, chunks, embeddings)

    # 6. Elasticsearch登録
    write_chunks_to_es(es_client, doc_id, doc_name, gcs_path, chunks, now)

    logger.info(f"処理完了: {doc_name} ({len(chunks)} チャンク)")
    return {"doc_id": doc_id, "chunks": len(chunks), "status": "success"}


def main() -> None:
    """メイン処理: GCS上の全ドキュメントを処理する。"""
    logger.info("=== Ingestion 開始 ===")

    # Vertex AI 初期化
    vertexai.init(project=GCP_PROJECT, location=CFG.get("gcp", {}).get("region", "asia-northeast1"))

    # クライアント初期化
    gcs_client = storage.Client(project=GCP_PROJECT)
    bq_client = bigquery.Client(project=GCP_PROJECT)
    es_url, es_key = get_es_credentials()
    es_client = create_es_client(es_url, es_key)

    # 処理対象ドキュメントの列挙
    if TARGET_GCS_PATH:
        bucket_name, blob_name = TARGET_GCS_PATH.replace("gs://", "").split("/", 1)
        bucket = gcs_client.bucket(bucket_name)
        blobs = [bucket.blob(blob_name)]
    else:
        blobs = list_documents(gcs_client, GCS_BUCKET)

    if not blobs:
        logger.info("処理対象ドキュメントなし")
        return

    logger.info(f"処理対象: {len(blobs)} ファイル")

    results = []
    for blob in blobs:
        try:
            result = process_document(blob, bq_client, es_client)
            results.append(result)
        except Exception as e:
            logger.error(f"処理失敗: {blob.name} - {type(e).__name__}: {e}")
            results.append({"doc_name": blob.name, "status": "failed", "error": str(e)})

    success = sum(1 for r in results if r.get("status") == "success")
    total_chunks = sum(r.get("chunks", 0) for r in results)
    logger.info(f"=== Ingestion 完了: {success}/{len(results)} 成功, {total_chunks} チャンク ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Ingestion異常終了: {type(e).__name__}: {e}")
        sys.exit(1)
