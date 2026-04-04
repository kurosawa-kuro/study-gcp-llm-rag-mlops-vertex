"""ハイブリッド検索モジュール（BigQuery Vector Search + Elasticsearch 全文検索）"""

from __future__ import annotations

import logging

from google.cloud import bigquery
from elasticsearch import Elasticsearch

logger = logging.getLogger("doc-qa")


def search_bigquery_vector(
    client: bigquery.Client,
    dataset: str,
    table: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    """BigQuery Vector Search で意味検索を行う。"""
    embedding_str = ", ".join(str(v) for v in query_embedding)

    query = f"""
    SELECT
        id, doc_id, doc_name, content, chunk_index, page_number, gcs_path,
        ML.DISTANCE(embedding, [{embedding_str}], 'COSINE') AS distance
    FROM `{client.project}.{dataset}.{table}`
    ORDER BY distance ASC
    LIMIT {top_k}
    """

    results = client.query(query).result()
    return [
        {
            "id": row.id,
            "doc_id": row.doc_id,
            "doc_name": row.doc_name,
            "content": row.content,
            "chunk_index": row.chunk_index,
            "page_number": row.page_number,
            "gcs_path": row.gcs_path,
            "score": 1.0 - row.distance,  # cosine similarity
            "source": "vector",
        }
        for row in results
    ]


def search_elasticsearch(
    es: Elasticsearch,
    index_name: str,
    query_text: str,
    top_k: int = 5,
) -> list[dict]:
    """Elasticsearch で全文検索（kuromoji）を行う。"""
    result = es.search(
        index=index_name,
        query={"match": {"content": query_text}},
        size=top_k,
    )

    return [
        {
            "id": hit["_source"]["id"],
            "doc_id": hit["_source"]["doc_id"],
            "doc_name": hit["_source"]["doc_name"],
            "content": hit["_source"]["content"],
            "chunk_index": hit["_source"].get("chunk_index"),
            "page_number": hit["_source"].get("page_number"),
            "gcs_path": hit["_source"].get("gcs_path"),
            "score": hit["_score"],
            "source": "fulltext",
        }
        for hit in result["hits"]["hits"]
    ]


def hybrid_search(
    bq_client: bigquery.Client,
    es_client: Elasticsearch,
    dataset: str,
    table: str,
    es_index: str,
    query_text: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> tuple[list[dict], list[dict]]:
    """ハイブリッド検索を実行し、Vector / 全文検索の結果を返す。"""
    vector_results = search_bigquery_vector(bq_client, dataset, table, query_embedding, top_k)
    fulltext_results = search_elasticsearch(es_client, es_index, query_text, top_k)

    logger.info(f"Vector検索: {len(vector_results)} 件, 全文検索: {len(fulltext_results)} 件")
    return vector_results, fulltext_results
