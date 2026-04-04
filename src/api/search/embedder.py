"""クエリ Embedding モジュール（Vertex AI Embedding API）"""

from __future__ import annotations

from config import get
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

_MODEL_NAME = get("ingestion.embedding_model", "text-multilingual-embedding-002")


def embed_query(query: str) -> list[float]:
    """クエリテキストをベクトル化する。"""
    model = TextEmbeddingModel.from_pretrained(_MODEL_NAME)
    inputs = [TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")]
    results = model.get_embeddings(inputs)
    return results[0].values
