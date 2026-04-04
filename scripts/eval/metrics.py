"""RAG評価指標 計算モジュール

Recall@K / MRR（検索品質）と Exact Match / ROUGE-L（回答品質）を算出する。
"""

from __future__ import annotations


def recall_at_k(results: list[dict], relevant_keywords: list[str], k: int) -> int:
    """Top-K結果に relevant_keywords を全て含むチャンクがあれば 1 を返す。"""
    for doc in results[:k]:
        content = doc.get("content", "")
        if all(kw in content for kw in relevant_keywords):
            return 1
    return 0


def find_first_relevant_rank(
    results: list[dict], relevant_keywords: list[str],
) -> int | None:
    """最初の正解チャンクの 1-based ランクを返す。見つからなければ None。"""
    for rank, doc in enumerate(results, 1):
        content = doc.get("content", "")
        if all(kw in content for kw in relevant_keywords):
            return rank
    return None


def mrr(ranks: list[int | None]) -> float:
    """全クエリの Mean Reciprocal Rank を算出する。"""
    if not ranks:
        return 0.0
    return sum(1.0 / r for r in ranks if r is not None) / len(ranks)


def exact_match(answer: str, keywords: list[str]) -> bool:
    """回答に全キーワードが含まれていれば True。"""
    return all(kw in answer for kw in keywords)


def rouge_l(answer: str, reference: str) -> float:
    """文字レベル LCS ベースの ROUGE-L F1 スコアを算出する。"""
    if not answer or not reference:
        return 0.0
    lcs_len = _lcs_length(answer, reference)
    precision = lcs_len / len(answer)
    recall = lcs_len / len(reference)
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def _lcs_length(x: str, y: str) -> int:
    """2行 DP による最長共通部分列の長さを算出する。"""
    if len(x) < len(y):
        x, y = y, x
    prev = [0] * (len(y) + 1)
    curr = [0] * (len(y) + 1)
    for i in range(1, len(x) + 1):
        for j in range(1, len(y) + 1):
            if x[i - 1] == y[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, [0] * (len(y) + 1)
    return prev[len(y)]
