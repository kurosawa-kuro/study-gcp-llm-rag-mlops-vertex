"""Google AI Studio Gemini 回答生成モジュール

注意: 無料枠は日次20リクエスト/分次5リクエスト（gemini-2.5-flash）。
Cloud Run 上では環境変数 GOOGLE_AI_STUDIO_API_KEY で認証する。
"""

from __future__ import annotations

import logging
import os

from config import get
import google.generativeai as genai

logger = logging.getLogger("doc-qa")

_MODEL_NAME = get("api.gemini_model", "gemini-2.5-flash")

SYSTEM_PROMPT = """あなたは社内ドキュメントの専門家です。
以下のドキュメントのみを根拠として日本語で正確に回答してください。
根拠が見つからない場合は「該当する情報が見つかりませんでした」と答えてください。"""


def generate_answer(query: str, context_docs: list[dict]) -> str:
    """検索結果を元に Gemini で回答を生成する。"""
    genai.configure(api_key=os.environ["GOOGLE_AI_STUDIO_API_KEY"])

    context = _build_context(context_docs)
    prompt = f"""【参考ドキュメント】
{context}

【質問】
{query}"""

    model = genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(prompt)
    answer = response.text
    logger.info(f"回答生成完了: {len(answer)} 文字")
    return answer


def _build_context(docs: list[dict]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.get("doc_name", "不明")
        page = doc.get("page_number", "?")
        content = doc.get("content", "")
        parts.append(f"[{i}] {source}（p.{page}）\n{content}")
    return "\n\n".join(parts)
