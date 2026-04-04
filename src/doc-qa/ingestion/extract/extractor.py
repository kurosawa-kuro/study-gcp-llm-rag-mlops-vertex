"""テキスト抽出モジュール（PDF / Word / TXT）"""

from pathlib import Path

import fitz  # pymupdf
from docx import Document


def extract_text(file_path: str) -> tuple[str, list[dict]]:
    """ファイルからテキストを抽出する。

    Returns:
        (全文テキスト, ページ情報リスト[{"page": int, "text": str}])
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix in (".docx", ".doc"):
        return _extract_docx(path)
    elif suffix == ".txt":
        return _extract_txt(path)
    else:
        raise ValueError(f"未対応のファイル形式: {suffix}")


def _extract_pdf(path: Path) -> tuple[str, list[dict]]:
    pages = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                pages.append({"page": i, "text": text})
    full_text = "\n".join(p["text"] for p in pages)
    return full_text, pages


def _extract_docx(path: Path) -> tuple[str, list[dict]]:
    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    # Word にはページ概念がないため page=1 とする
    return text, [{"page": 1, "text": text}]


def _extract_txt(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    return text, [{"page": 1, "text": text}]
