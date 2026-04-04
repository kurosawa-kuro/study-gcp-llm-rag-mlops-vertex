"""RAG評価 比較レポート生成

複数の評価結果 JSON を読み込み、横並びの比較テーブルを出力する。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


METRICS = [
    ("recall@1", "Recall@1"),
    ("recall@3", "Recall@3"),
    ("recall@5", "Recall@5"),
    ("recall@10", "Recall@10"),
    ("mrr", "MRR"),
    ("exact_match", "Exact Match"),
    ("rouge_l", "ROUGE-L"),
]


def _load_result(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_metric(result: dict, key: str) -> float:
    if key in result.get("retrieval", {}):
        return result["retrieval"][key]
    if key in result.get("generation", {}):
        return result["generation"][key]
    return 0.0


def generate_report(results: list[dict]) -> str:
    """比較レポートの文字列を生成する。"""
    lines = []
    lines.append("\n=== 検索パターン比較レポート ===\n")

    if not results:
        lines.append("比較対象の結果がありません。")
        return "\n".join(lines)

    labels = [r.get("search_type", "unknown") for r in results]
    col_width = max(14, *(len(label) + 2 for label in labels))
    header = f"{'指標':<14}" + "".join(f"{label:<{col_width}}" for label in labels)
    separator = "─" * len(header)

    lines.append(header)
    lines.append(separator)

    for key, display_name in METRICS:
        row = f"{display_name:<14}"
        for result in results:
            value = _get_metric(result, key)
            row += f"{value:<{col_width}.4f}"
        lines.append(row)

    lines.append("")

    if len(results) >= 2:
        lines.append("--- 差分（最終結果 - 最初の結果）---")
        first = results[0]
        last = results[-1]
        for key, display_name in METRICS:
            v_first = _get_metric(first, key)
            v_last = _get_metric(last, key)
            diff = v_last - v_first
            sign = "+" if diff >= 0 else ""
            mark = "✅" if diff > 0 else ("➖" if diff == 0 else "⚠️")
            lines.append(f"  {display_name:<14} {sign}{diff:.4f} {mark}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG評価 比較レポート")
    parser.add_argument("--results", nargs="+", required=True,
                        help="比較する結果 JSON ファイル")
    parser.add_argument("--output", type=str, default=None,
                        help="レポート出力先（省略時: stdout）")
    args = parser.parse_args()

    results = [_load_result(p) for p in args.results]
    report = generate_report(results)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"レポート保存: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
