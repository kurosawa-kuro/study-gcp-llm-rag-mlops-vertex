"""Google AI Studio Gemini 回答生成モジュール

Cloud Run 上では環境変数 GOOGLE_AI_STUDIO_API_KEY で認証する。
ローカル実行時は env/secret/credentials.yml からフォールバック取得する。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from google import genai

from config import get

logger = logging.getLogger("doc-qa")

_MODEL_NAME = get("api.gemini_model", "gemini-2.5-flash")

SYSTEM_PROMPT = """あなたは社内ドキュメントの専門家です。
以下のドキュメントのみを根拠として日本語で正確に回答してください。
根拠が見つからない場合は「該当する情報が見つかりませんでした」と答えてください。"""


def _get_api_key() -> str:
    """GOOGLE_AI_STUDIO_API_KEY を取得する（環境変数 > credentials.yml）。"""
    key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY")
    if key:
        return key
    for candidate in [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "env" / "secret" / "credentials.yml",
        Path.cwd() / "env" / "secret" / "credentials.yml",
    ]:
        if candidate.is_file():
            creds = yaml.safe_load(candidate.read_text())
            if isinstance(creds, dict) and "google_ai_studio_api_key" in creds:
                return creds["google_ai_studio_api_key"]
    raise RuntimeError("GOOGLE_AI_STUDIO_API_KEY が環境変数にも credentials.yml にも見つかりません")


def generate_answer(query: str, context_docs: list[dict]) -> str:
    """検索結果を元に Gemini で回答を生成する。"""
    client = genai.Client(api_key=_get_api_key())

    context = _build_context(context_docs)
    prompt = f"""【参考ドキュメント】
{context}

【質問】
{query}"""

    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )
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
