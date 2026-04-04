"""Elasticsearch インデックス登録モジュール（kuromoji対応）"""

from __future__ import annotations

import logging

from elasticsearch import Elasticsearch

logger = logging.getLogger("doc-qa")

INDEX_SETTINGS = {
    "settings": {
        "analysis": {
            "analyzer": {
                "ja_kuromoji": {
                    "type": "custom",
                    "tokenizer": "kuromoji_tokenizer",
                    "filter": ["kuromoji_baseform", "kuromoji_part_of_speech", "cjk_width", "lowercase"],
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id":          {"type": "keyword"},
            "doc_id":      {"type": "keyword"},
            "doc_name":    {"type": "keyword"},
            "content":     {"type": "text", "analyzer": "ja_kuromoji"},
            "chunk_index": {"type": "integer"},
            "page_number": {"type": "integer"},
            "gcs_path":    {"type": "keyword"},
            "created_at":  {"type": "date"},
        }
    }
}


def create_es_client(cloud_url: str, api_key: str) -> Elasticsearch:
    """Elastic Cloud クライアントを作成する。"""
    return Elasticsearch(cloud_url, api_key=api_key)


def ensure_index(es: Elasticsearch, index_name: str) -> None:
    """インデックスが存在しない場合は作成する。"""
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=INDEX_SETTINGS)
        logger.info(f"Elasticsearchインデックス作成: {index_name}")


def write_chunks_to_es(
    es: Elasticsearch,
    doc_id: str,
    doc_name: str,
    gcs_path: str,
    chunks: list[dict],
    created_at: str,
    index_name: str = "doc-qa",
) -> int:
    """チャンクを Elasticsearch に登録する（冪等）。"""
    ensure_index(es, index_name)

    es.delete_by_query(
        index=index_name,
        body={"query": {"term": {"doc_id": doc_id}}},
        conflicts="proceed",
    )

    for chunk in chunks:
        doc = {
            "id": f"{doc_id}_{chunk['chunk_index']}",
            "doc_id": doc_id,
            "doc_name": doc_name,
            "content": chunk["content"],
            "chunk_index": chunk["chunk_index"],
            "page_number": chunk["page_number"],
            "gcs_path": gcs_path,
            "created_at": created_at,
        }
        es.index(index=index_name, id=doc["id"], document=doc)

    logger.info(f"Elasticsearch登録完了: {len(chunks)} 件 (doc_id={doc_id})")
    return len(chunks)
