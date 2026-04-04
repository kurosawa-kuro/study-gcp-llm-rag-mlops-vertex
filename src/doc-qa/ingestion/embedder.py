"""Vertex AI Embedding API 呼び出しモジュール"""

from __future__ import annotations

import logging

from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

logger = logging.getLogger("doc-qa")

MODEL_NAME = "text-multilingual-embedding-002"
BATCH_SIZE = 100


def generate_embeddings(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """テキストリストをバッチでベクトル化する。

    Args:
        texts: ベクトル化するテキストのリスト
        task_type: RETRIEVAL_DOCUMENT（Ingestion時）または RETRIEVAL_QUERY（検索時）

    Returns:
        各テキストに対応する Embedding ベクトルのリスト（768次元）
    """
    model = TextEmbeddingModel.from_pretrained(MODEL_NAME)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        inputs = [TextEmbeddingInput(text=t, task_type=task_type) for t in batch]
        results = model.get_embeddings(inputs)
        all_embeddings.extend([r.values for r in results])
        logger.info(f"Embedding完了: {len(all_embeddings)}/{len(texts)} 件")

    return all_embeddings
