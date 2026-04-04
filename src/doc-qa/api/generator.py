"""Vertex AI Gemini 回答生成モジュール"""

from __future__ import annotations

import logging

from vertexai.generative_models import GenerativeModel

logger = logging.getLogger("doc-qa")

MODEL_NAME = "gemini-2.0-flash"

SYSTEM_PROMPT = """あなたは社内ドキュメントの専門家です。
以下のドキュメントのみを根拠として日本語で正確に回答してください。
根拠が見つからない場合は「該当する情報が見つかりませんでした」と答えてください。"""


def generate_answer(query: str, context_docs: list[dict]) -> str:
    """検索結果を元に Gemini で回答を生成する。

    Args:
        query: ユーザーの質問
        context_docs: リランク済みの検索結果リスト

    Returns:
        生成された回答テキスト
    """
    context = _build_context(context_docs)
    prompt = f"""{SYSTEM_PROMPT}

【参考ドキュメント】
{context}

【質問】
{query}"""

    model = GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    answer = response.text
    logger.info(f"回答生成完了: {len(answer)} 文字")
    return answer


def _build_context(docs: list[dict]) -> str:
    """検索結果をプロンプト用のコンテキスト文字列に変換する。"""
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("doc_name", "不明")
        page = doc.get("page_number", "?")
        content = doc.get("content", "")
        parts.append(f"[{i}] {source}（p.{page}）\n{content}")
    return "\n\n".join(parts)
