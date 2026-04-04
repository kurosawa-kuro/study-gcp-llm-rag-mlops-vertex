"""scripts/eval/report.py 単体テスト"""

import pytest

from report import generate_report, _get_metric


def _result(search_type: str, retrieval: dict, generation: dict) -> dict:
    return {
        "search_type": search_type,
        "retrieval": retrieval,
        "generation": generation,
    }


# === _get_metric ===

class TestGetMetric:
    def test_retrieval_metric(self):
        r = _result("hybrid", {"recall@1": 0.8, "mrr": 0.6}, {})
        assert _get_metric(r, "recall@1") == 0.8
        assert _get_metric(r, "mrr") == 0.6

    def test_generation_metric(self):
        r = _result("hybrid", {}, {"exact_match": 0.5, "rouge_l": 0.7})
        assert _get_metric(r, "exact_match") == 0.5
        assert _get_metric(r, "rouge_l") == 0.7

    def test_missing_metric_returns_zero(self):
        r = _result("hybrid", {}, {})
        assert _get_metric(r, "nonexistent") == 0.0

    def test_missing_sections(self):
        assert _get_metric({}, "recall@1") == 0.0


# === generate_report ===

class TestGenerateReport:
    def test_single_result(self):
        r = _result("vector", {"recall@1": 0.8, "recall@3": 0.9, "recall@5": 1.0, "recall@10": 1.0, "mrr": 0.85},
                     {"exact_match": 0.6, "rouge_l": 0.7})
        report = generate_report([r])
        assert "vector" in report
        assert "Recall@1" in report
        assert "MRR" in report
        assert "ROUGE-L" in report

    def test_two_results_include_diff(self):
        r1 = _result("vector", {"recall@1": 0.6, "mrr": 0.5}, {"exact_match": 0.4, "rouge_l": 0.5})
        r2 = _result("hybrid", {"recall@1": 0.8, "mrr": 0.7}, {"exact_match": 0.6, "rouge_l": 0.7})
        report = generate_report([r1, r2])
        assert "差分" in report

    def test_empty_results(self):
        report = generate_report([])
        assert "検索パターン比較レポート" in report
        assert "比較対象の結果がありません" in report
