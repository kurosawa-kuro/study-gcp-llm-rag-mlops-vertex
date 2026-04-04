"""クエリ Embedding モジュール（Vertex AI Embedding API）"""

from __future__ import annotations

from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

MODEL_NAME = "text-multilingual-embedding-002"


def embed_query(query: str) -> list[float]:
    """クエリテキストをベクトル化する。

    Returns:
        768次元の Embedding ベクトル
    """
    model = TextEmbeddingModel.from_pretrained(MODEL_NAME)
    inputs = [TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")]
    results = model.get_embeddings(inputs)
    return results[0].values
