"""Ingestion パイプライン 単体テスト"""

import pytest

from extract.chunker import split_into_chunks
from extract.extractor import _extract_txt
from pathlib import Path
import tempfile


# === extractor テスト ===

class TestExtractor:
    def test_extract_txt(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("これはテストドキュメントです。\n2行目のテキスト。", encoding="utf-8")

        text, pages = _extract_txt(txt_file)
        assert "テストドキュメント" in text
        assert len(pages) == 1
        assert pages[0]["page"] == 1

    def test_extract_txt_empty(self, tmp_path):
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("", encoding="utf-8")

        text, pages = _extract_txt(txt_file)
        assert text == ""


# === chunker テスト ===

class TestChunker:
    def test_split_basic(self):
        text = "あ" * 2000
        pages = [{"page": 1, "text": text}]

        chunks = split_into_chunks(text, pages, chunk_size=800, overlap=50)
        assert len(chunks) >= 3
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["page_number"] == 1
        assert len(chunks[0]["content"]) == 800

    def test_split_short_text(self):
        text = "短いテキスト"
        pages = [{"page": 1, "text": text}]

        chunks = split_into_chunks(text, pages)
        assert len(chunks) == 1
        assert chunks[0]["content"] == text

    def test_split_empty_text(self):
        chunks = split_into_chunks("", [])
        assert chunks == []

    def test_split_overlap(self):
        text = "あ" * 1600
        pages = [{"page": 1, "text": text}]

        chunks = split_into_chunks(text, pages, chunk_size=800, overlap=50)
        # 2つ目のチャンクは 750 文字目から始まる
        assert chunks[1]["chunk_index"] == 1
        # オーバーラップ部分が重複していることを確認
        end_of_first = chunks[0]["content"][-50:]
        start_of_second = chunks[1]["content"][:50]
        assert end_of_first == start_of_second

    def test_split_multipage(self):
        page1 = "A" * 500
        page2 = "B" * 500
        text = page1 + page2
        pages = [{"page": 1, "text": page1}, {"page": 2, "text": page2}]

        chunks = split_into_chunks(text, pages, chunk_size=800, overlap=50)
        assert chunks[0]["page_number"] == 1
        # 2つ目のチャンクは 750文字目開始 → page2 の領域
        assert chunks[1]["page_number"] == 2


# === bq_writer テスト ===

class TestBqWriter:
    def test_insert_with_retry_success(self, mocker):
        from store.bq_writer import _insert_with_retry

        mock_client = mocker.MagicMock()
        mock_client.insert_rows_json.return_value = []

        _insert_with_retry(mock_client, "project.dataset.table", [{"id": "1"}])
        mock_client.insert_rows_json.assert_called_once()

    def test_insert_with_retry_retries(self, mocker):
        from store.bq_writer import _insert_with_retry

        mocker.patch("store.bq_writer.time.sleep")
        mock_client = mocker.MagicMock()
        mock_client.insert_rows_json.side_effect = [
            Exception("transient"),
            [],
        ]

        _insert_with_retry(mock_client, "project.dataset.table", [{"id": "1"}])
        assert mock_client.insert_rows_json.call_count == 2

    def test_insert_with_retry_exhausted(self, mocker):
        from store.bq_writer import _insert_with_retry

        mocker.patch("store.bq_writer.time.sleep")
        mock_client = mocker.MagicMock()
        mock_client.insert_rows_json.side_effect = Exception("persistent")

        with pytest.raises(Exception, match="persistent"):
            _insert_with_retry(mock_client, "project.dataset.table", [{"id": "1"}])
        assert mock_client.insert_rows_json.call_count == 3
