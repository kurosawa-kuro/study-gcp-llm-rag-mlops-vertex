"""Vertex AI Embedding API 呼び出しモジュール"""

from __future__ import annotations

import logging

from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

logger = logging.getLogger("doc-qa")


def generate_embeddings(
    texts: list[str],
    model_name: str = "text-multilingual-embedding-002",
    batch_size: int = 100,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """テキストリストをバッチでベクトル化する。

    Args:
        texts: ベクトル化するテキストのリスト
        model_name: application.yml の ingestion.embedding_model から渡される
        batch_size: application.yml の ingestion.embedding_batch_size から渡される
        task_type: RETRIEVAL_DOCUMENT（Ingestion時）または RETRIEVAL_QUERY（検索時）

    Returns:
        各テキストに対応する Embedding ベクトルのリスト（768次元）
    """
    model = TextEmbeddingModel.from_pretrained(model_name)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = [TextEmbeddingInput(text=t, task_type=task_type) for t in batch]
        results = model.get_embeddings(inputs)
        all_embeddings.extend([r.values for r in results])
        logger.info(f"Embedding完了: {len(all_embeddings)}/{len(texts)} 件")

    return all_embeddings
