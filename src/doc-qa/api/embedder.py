"""クエリ Embedding モジュール（Vertex AI Embedding API）"""

from __future__ import annotations

from pathlib import Path

import yaml
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "env" / "config" / "application.yml"


def _get_model_name() -> str:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("ingestion", {}).get("embedding_model", "text-multilingual-embedding-002")
    return "text-multilingual-embedding-002"


def embed_query(query: str) -> list[float]:
    """クエリテキストをベクトル化する。

    Returns:
        768次元の Embedding ベクトル
    """
    model = TextEmbeddingModel.from_pretrained(_get_model_name())
    inputs = [TextEmbeddingInput(text=query, task_type="RETRIEVAL_QUERY")]
    results = model.get_embeddings(inputs)
    return results[0].values
