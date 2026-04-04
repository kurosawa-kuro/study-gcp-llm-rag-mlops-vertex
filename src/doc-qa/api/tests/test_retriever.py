"""api/search/retriever.py 単体テスト"""

import pytest
from unittest.mock import MagicMock


# === search_bigquery_vector ===

class TestSearchBigqueryVector:
    def test_returns_formatted_results(self, mocker):
        from search.retriever import search_bigquery_vector

        mock_row = MagicMock()
        mock_row.id = "chunk-001"
        mock_row.doc_id = "doc-001"
        mock_row.doc_name = "test.pdf"
        mock_row.content = "テスト内容"
        mock_row.chunk_index = 0
        mock_row.page_number = 1
        mock_row.gcs_path = "gs://bucket/test.pdf"
        mock_row.distance = 0.2

        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_client.query.return_value.result.return_value = [mock_row]

        results = search_bigquery_vector(mock_client, "dataset", "table", [0.1, 0.2], top_k=5)

        assert len(results) == 1
        assert results[0]["id"] == "chunk-001"
        assert results[0]["score"] == pytest.approx(0.8)  # 1.0 - 0.2
        assert results[0]["source"] == "vector"

    def test_empty_results(self, mocker):
        from search.retriever import search_bigquery_vector

        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_client.query.return_value.result.return_value = []

        results = search_bigquery_vector(mock_client, "dataset", "table", [0.1], top_k=5)
        assert results == []


# === search_elasticsearch ===

class TestSearchElasticsearch:
    def test_returns_formatted_results(self, mocker):
        from search.retriever import search_elasticsearch

        mock_es = MagicMock()
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "id": "chunk-001",
                            "doc_id": "doc-001",
                            "doc_name": "test.pdf",
                            "content": "テスト内容",
                            "chunk_index": 0,
                            "page_number": 1,
                            "gcs_path": "gs://bucket/test.pdf",
                        },
                        "_score": 5.0,
                    }
                ]
            }
        }

        results = search_elasticsearch(mock_es, "doc-qa", "テスト", top_k=5)

        assert len(results) == 1
        assert results[0]["id"] == "chunk-001"
        assert results[0]["score"] == 5.0
        assert results[0]["source"] == "fulltext"

    def test_empty_results(self, mocker):
        from search.retriever import search_elasticsearch

        mock_es = MagicMock()
        mock_es.search.return_value = {"hits": {"hits": []}}

        results = search_elasticsearch(mock_es, "doc-qa", "テスト", top_k=5)
        assert results == []


# === hybrid_search ===

class TestHybridSearch:
    def test_returns_both_results(self, mocker):
        from search.retriever import hybrid_search

        mocker.patch("search.retriever.search_bigquery_vector", return_value=[{"id": "v1"}])
        mocker.patch("search.retriever.search_elasticsearch", return_value=[{"id": "f1"}])

        mock_bq = MagicMock()
        mock_es = MagicMock()

        vector, fulltext = hybrid_search(
            mock_bq, mock_es, "dataset", "table", "index",
            "query", [0.1], top_k=5,
        )

        assert len(vector) == 1
        assert vector[0]["id"] == "v1"
        assert len(fulltext) == 1
        assert fulltext[0]["id"] == "f1"
