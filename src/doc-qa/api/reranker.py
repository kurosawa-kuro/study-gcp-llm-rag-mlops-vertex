"""RRF（Reciprocal Rank Fusion）リランクモジュール"""

from __future__ import annotations

RRF_K = 60  # RRF 定数（標準的な値）


def reciprocal_rank_fusion(
    vector_results: list[dict],
    fulltext_results: list[dict],
    top_k: int = 5,
    k: int = RRF_K,
) -> list[dict]:
    """2つの検索結果を RRF でマージ・リランクする。

    RRF score = sum(1 / (k + rank_i))

    Returns:
        マージ・リランクされた結果リスト（上位 top_k 件）
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
