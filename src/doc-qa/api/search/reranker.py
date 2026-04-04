"""RRF（Reciprocal Rank Fusion）リランクモジュール"""

from __future__ import annotations


def reciprocal_rank_fusion(
    vector_results: list[dict],
    fulltext_results: list[dict],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """2つの検索結果を RRF でマージ・リランクする。

    RRF score = sum(1 / (k + rank_i))
    k はデフォルト60。呼び出し元が application.yml の api.rrf_k を渡す。
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results, 1):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        docs[doc_id] = doc

    for rank, doc in enumerate(fulltext_results, 1):
        doc_id = doc["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
        if doc_id not in docs:
            docs[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    results = []
    for doc_id in sorted_ids[:top_k]:
        doc = docs[doc_id].copy()
        doc["rrf_score"] = scores[doc_id]
        results.append(doc)

    return results
