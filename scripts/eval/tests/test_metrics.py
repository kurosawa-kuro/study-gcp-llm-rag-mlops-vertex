"""scripts/eval/metrics.py 単体テスト"""

import pytest

from metrics import recall_at_k, find_first_relevant_rank, mrr, exact_match, rouge_l, _lcs_length


def _doc(content: str) -> dict:
    return {"content": content}


# === recall_at_k ===

class TestRecallAtK:
    def test_hit_in_top_k(self):
        results = [_doc("有給休暇は年20日付与されます")]
        assert recall_at_k(results, ["有給休暇", "20日"], k=1) == 1

    def test_miss_outside_top_k(self):
        results = [_doc("関係ない"), _doc("有給休暇20日")]
        assert recall_at_k(results, ["有給休暇"], k=1) == 0

    def test_miss_partial_keywords(self):
        results = [_doc("有給休暇の案内")]
        assert recall_at_k(results, ["有給休暇", "産休"], k=1) == 0

    def test_empty_results(self):
        assert recall_at_k([], ["key"], k=5) == 0


# === find_first_relevant_rank ===

class TestFindFirstRelevantRank:
    def test_found_at_rank_1(self):
        results = [_doc("有給休暇20日"), _doc("別の文書")]
        assert find_first_relevant_rank(results, ["有給休暇"]) == 1

    def test_found_at_rank_3(self):
        results = [_doc("A"), _doc("B"), _doc("有給休暇")]
        assert find_first_relevant_rank(results, ["有給休暇"]) == 3

    def test_not_found(self):
        results = [_doc("A"), _doc("B")]
        assert find_first_relevant_rank(results, ["有給休暇"]) is None

    def test_empty_results(self):
        assert find_first_relevant_rank([], ["key"]) is None


# === mrr ===

class TestMRR:
    def test_all_found_at_rank_1(self):
        assert mrr([1, 1, 1]) == 1.0

    def test_mixed_ranks(self):
        # 1/1 + 1/2 + 1/3 = 11/6, /3 ≈ 0.6111
        result = mrr([1, 2, 3])
        assert abs(result - 11 / 18) < 1e-9

    def test_with_none(self):
        # None は無視される。(1/1 + 1/2) / 3 = 0.5
        result = mrr([1, None, 2])
        assert abs(result - 0.5) < 1e-9

    def test_all_none(self):
        assert mrr([None, None]) == 0.0

    def test_empty(self):
        assert mrr([]) == 0.0


# === exact_match ===

class TestExactMatch:
    def test_all_keywords_present(self):
        assert exact_match("有給休暇は年20日付与", ["有給休暇", "20日"]) is True

    def test_partial_keywords(self):
        assert exact_match("有給休暇について", ["有給休暇", "20日"]) is False

    def test_empty_keywords(self):
        assert exact_match("何か", []) is True


# === rouge_l ===

class TestRougeL:
    def test_identical_strings(self):
        assert rouge_l("abc", "abc") == 1.0

    def test_no_overlap(self):
        assert rouge_l("abc", "xyz") == 0.0

    def test_partial_overlap(self):
        score = rouge_l("abcde", "ace")
        # LCS = "ace" (長さ3), precision=3/5, recall=3/3=1.0
        # F1 = 2*(3/5*1)/(3/5+1) = 2*(0.6)/(1.6) = 0.75
        assert abs(score - 0.75) < 1e-9

    def test_empty_answer(self):
        assert rouge_l("", "abc") == 0.0

    def test_empty_reference(self):
        assert rouge_l("abc", "") == 0.0

    def test_japanese_text(self):
        score = rouge_l("有給休暇は年20日", "有給休暇20日")
        assert score > 0.0


# === _lcs_length ===

class TestLcsLength:
    def test_basic(self):
        assert _lcs_length("abcde", "ace") == 3

    def test_identical(self):
        assert _lcs_length("abc", "abc") == 3

    def test_no_common(self):
        assert _lcs_length("abc", "xyz") == 0

    def test_empty(self):
        assert _lcs_length("", "abc") == 0
        assert _lcs_length("abc", "") == 0
