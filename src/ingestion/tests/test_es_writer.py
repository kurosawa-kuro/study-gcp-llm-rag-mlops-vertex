"""ingestion/store/es_writer.py 単体テスト"""

import pytest


# === ensure_index ===

class TestEnsureIndex:
    def test_creates_index_when_not_exists(self, mocker):
        from store.es_writer import ensure_index, INDEX_SETTINGS

        mock_es = mocker.MagicMock()
        mock_es.indices.exists.return_value = False

        ensure_index(mock_es, "test-index")

        mock_es.indices.create.assert_called_once_with(index="test-index", body=INDEX_SETTINGS)

    def test_skips_when_exists(self, mocker):
        from store.es_writer import ensure_index

        mock_es = mocker.MagicMock()
        mock_es.indices.exists.return_value = True

        ensure_index(mock_es, "test-index")

        mock_es.indices.create.assert_not_called()


# === write_chunks_to_es ===

class TestWriteChunksToEs:
    def test_writes_chunks(self, mocker):
        from store.es_writer import write_chunks_to_es

        mock_es = mocker.MagicMock()
        mock_es.indices.exists.return_value = True

        chunks = [
            {"chunk_index": 0, "content": "chunk0", "page_number": 1},
            {"chunk_index": 1, "content": "chunk1", "page_number": 2},
        ]

        count = write_chunks_to_es(
            mock_es, "doc-001", "test.pdf", "gs://bucket/test.pdf",
            chunks, "2024-01-01T00:00:00", "test-index",
        )

        assert count == 2
        assert mock_es.index.call_count == 2
        # 冪等性: 既存データ削除が呼ばれることを確認
        mock_es.delete_by_query.assert_called_once()

    def test_deletes_existing_before_write(self, mocker):
        from store.es_writer import write_chunks_to_es

        mock_es = mocker.MagicMock()
        mock_es.indices.exists.return_value = True

        write_chunks_to_es(
            mock_es, "doc-001", "test.pdf", "gs://bucket/test.pdf",
            [{"chunk_index": 0, "content": "c", "page_number": 1}],
            "2024-01-01T00:00:00", "test-index",
        )

        call_args = mock_es.delete_by_query.call_args
        assert call_args[1]["body"]["query"]["term"]["doc_id"] == "doc-001"

    def test_empty_chunks(self, mocker):
        from store.es_writer import write_chunks_to_es

        mock_es = mocker.MagicMock()
        mock_es.indices.exists.return_value = True

        count = write_chunks_to_es(
            mock_es, "doc-001", "test.pdf", "gs://bucket/test.pdf",
            [], "2024-01-01T00:00:00", "test-index",
        )

        assert count == 0
        mock_es.index.assert_not_called()
