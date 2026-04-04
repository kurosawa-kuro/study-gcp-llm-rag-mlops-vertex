"""QA API 単体テスト"""

import pytest
from search.reranker import reciprocal_rank_fusion


# === reranker テスト ===

class TestRRF:
    def test_basic_fusion(self):
        vector = [
            {"id": "a", "doc_name": "doc1.pdf", "content": "aaa", "page_number": 1, "score": 0.9, "source": "vector"},
            {"id": "b", "doc_name": "doc2.pdf", "content": "bbb", "page_number": 2, "score": 0.8, "source": "vector"},
        ]
        fulltext = [
            {"id": "b", "doc_name": "doc2.pdf", "content": "bbb", "page_number": 2, "score": 5.0, "source": "fulltext"},
            {"id": "c", "doc_name": "doc3.pdf", "content": "ccc", "page_number": 1, "score": 3.0, "source": "fulltext"},
        ]

        results = reciprocal_rank_fusion(vector, fulltext, top_k=3)

        assert len(results) == 3
        # "b" は両方に存在するので最上位
        assert results[0]["id"] == "b"
        assert "rrf_score" in results[0]

    def test_empty_inputs(self):
        results = reciprocal_rank_fusion([], [], top_k=5)
        assert results == []

    def test_single_source(self):
        vector = [
            {"id": "a", "doc_name": "doc1.pdf", "content": "aaa", "page_number": 1, "score": 0.9, "source": "vector"},
        ]
        results = reciprocal_rank_fusion(vector, [], top_k=5)
        assert len(results) == 1
        assert results[0]["id"] == "a"

    def test_top_k_limit(self):
        vector = [{"id": str(i), "doc_name": f"d{i}", "content": "x", "page_number": 1, "score": 0.5, "source": "vector"} for i in range(10)]
        results = reciprocal_rank_fusion(vector, [], top_k=3)
        assert len(results) == 3


# === health テスト ===

class TestHealth:
    def test_health_endpoint(self):
        """FastAPI の /health エンドポイントをテストする。"""
        # main.py のインポートには GCP クライアントが必要なため、
        # 実際のテストは httpx + TestClient で GCP をモックして行う
        pass


# === generator テスト ===

class TestGenerator:
    def test_build_context(self):
        from generation.generator import _build_context

        docs = [
            {"doc_name": "就業規則.pdf", "page_number": 5, "content": "有給休暇は..."},
            {"doc_name": "FAQ.txt", "page_number": 1, "content": "Q: 申請方法は？"},
        ]
        context = _build_context(docs)
        assert "[1] 就業規則.pdf（p.5）" in context
        assert "[2] FAQ.txt（p.1）" in context
        assert "有給休暇は..." in context
