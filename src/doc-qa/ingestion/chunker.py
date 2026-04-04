"""チャンク分割モジュール（800文字・50文字オーバーラップ）"""

from __future__ import annotations

CHUNK_SIZE = 800
OVERLAP = 50


def split_into_chunks(
    text: str,
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[dict]:
    """テキストをチャンクに分割する。

    Returns:
        [{"chunk_index": int, "page_number": int, "content": str}, ...]
    """
    if not text.strip():
        return []

    chunks: list[dict] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size
        content = text[start:end]

        if not content.strip():
            start = end - overlap
            continue

        page_number = _estimate_page(start, pages)
        chunks.append({
            "chunk_index": chunk_index,
            "page_number": page_number,
            "content": content,
        })

        chunk_index += 1
        start = end - overlap

    return chunks


def _estimate_page(char_offset: int, pages: list[dict]) -> int:
    """文字オフセットからページ番号を推定する。"""
    cumulative = 0
    for page_info in pages:
        cumulative += len(page_info["text"])
        if char_offset < cumulative:
            return page_info["page"]
    return pages[-1]["page"] if pages else 1
