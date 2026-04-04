"""BigQuery documents テーブル書き込みモジュール（冪等・リトライ付き）"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from google.cloud import bigquery

logger = logging.getLogger("doc-qa")

MAX_RETRIES = 3


def write_chunks_to_bq(
    client: bigquery.Client,
    dataset: str,
    table: str,
    doc_id: str,
    doc_name: str,
    gcs_path: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> int:
    """チャンクと Embedding を BigQuery に書き込む（冪等）。

    Returns:
        書き込んだ行数
    """
    table_ref = f"{client.project}.{dataset}.{table}"

    # 冪等性: 同一 doc_id の既存行を削除してから挿入
    _delete_existing(client, table_ref, doc_id)

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "id": f"{doc_id}_{chunk['chunk_index']}",
            "doc_id": doc_id,
            "doc_name": doc_name,
            "content": chunk["content"],
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk["page_number"],
            "gcs_path": gcs_path,
            "embedding": embedding,
            "created_at": now,
        })

    _insert_with_retry(client, table_ref, rows)
    logger.info(f"BigQuery書き込み完了: {len(rows)} 行 (doc_id={doc_id})")
    return len(rows)


def _delete_existing(client: bigquery.Client, table_ref: str, doc_id: str) -> None:
    """既存の doc_id のデータを削除する（冪等性確保）。"""
    query = f"DELETE FROM `{table_ref}` WHERE doc_id = @doc_id"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("doc_id", "STRING", doc_id)]
    )
    client.query(query, job_config=job_config).result()


def _insert_with_retry(client: bigquery.Client, table_ref: str, rows: list[dict]) -> None:
    """指数バックオフ付きリトライで BigQuery に行を挿入する。"""
    for attempt in range(MAX_RETRIES):
        try:
            errors = client.insert_rows_json(table_ref, rows)
            if not errors:
                return
            raise RuntimeError(f"BigQuery insert errors: {errors}")
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2**attempt
            logger.warning(f"BigQuery書き込みリトライ ({attempt + 1}/{MAX_RETRIES}), {wait}秒待機")
            time.sleep(wait)
