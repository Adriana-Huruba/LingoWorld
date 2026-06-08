"""
Unit tests for the the system recommender logic. It covers ELO calculation, CEFR mapping, ZPD targeting and SM-2 scheduling

Run:
    pytest test/test_recommender_unit.py -v
"""

import sys
from unittest.mock import MagicMock

for _mod in [
    'spylls', 'spylls.hunspell',
    'langgraph', 'langgraph.graph', 'langgraph.graph.state',
    'google.generativeai',
    'services.agent_service', 'services.vector_service',
    'core.embeddings', 'qdrant_client',
]:
    sys.modules.setdefault(_mod, MagicMock())

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.recommender_service import (
    elo_expected_score,
    calculate_new_elo,
    elo_to_cefr,
    cefr_to_elo,
    get_target_levels,
    estimate_quality,
    calculate_next_review_sm2,
    CEFR_ORDER,
)


class TestEloExpectedScore:
    def test_equal_elos_gives_50_percent(self):
        assert elo_expected_score(800, 800) == pytest.approx(0.5, abs=1e-6)

    def test_much_stronger_user_gives_high_probability(self):
        assert elo_expected_score(1200, 800) > 0.9

    def test_much_weaker_user_gives_low_probability(self):
        assert elo_expected_score(800, 1200) < 0.1

    def test_result_always_between_0_and_1(self):
        for user_elo in [0, 200, 800, 1600]:
            for item_elo in [0, 200, 800, 1600]:
                p = elo_expected_score(user_elo, item_elo)
                assert 0 < p < 1


class TestCalculateNewElo:
    def test_correct_answer_increases_elo(self):
        new = calculate_new_elo(800, 800, correct=True, total_responses=5)
        assert new > 800

    def test_incorrect_answer_decreases_elo(self):
        new = calculate_new_elo(800, 800, correct=False, total_responses=5)
        assert new < 800

    def test_elo_never_below_zero(self):
        new = calculate_new_elo(0, 1600, correct=False, total_responses=100)
        assert new >= 0

    def test_elo_never_above_1600(self):
        new = calculate_new_elo(1600, 0, correct=True, total_responses=100)
        assert new <= 1600

    def test_k_factor_new_user(self):
        delta_new = abs(calculate_new_elo(800, 800, True, 5) - 800)
        delta_stable = abs(calculate_new_elo(800, 800, True, 50) - 800)
        assert delta_new > delta_stable

    def test_easy_exercise_gives_small_gain(self):
        small_gain = calculate_new_elo(1000, 200, correct=True, total_responses=50)- 1000
        big_gain = calculate_new_elo(1000, 1000, correct=True, total_responses=50) - 1000
        assert small_gain < big_gain

    def test_hard_exercise_correct_gives_big_gain(self):
        gain = calculate_new_elo(500, 1200, correct=True, total_responses=5) - 500
        assert gain > 10


class TestEloToCefr:
    @pytest.mark.parametrize("elo,expected", [
        (0,  "A1"), (200, "A1"), (399, "A1"),
        (400, "A2"), (500, "A2"), (599, "A2"),
        (600, "B1"), (700, "B1"), (799, "B1"),
        (800, "B2"), (900, "B2"), (999, "B2"),
        (1000, "C1"), (1100, "C1"), (1199, "C1"),
        (1200, "C2"), (1400, "C2"), (1600, "C2"),
    ])
    def test_elo_maps_to_correct_cefr(self, elo, expected):
        assert elo_to_cefr(elo) == expected


class TestCefrToElo:
    @pytest.mark.parametrize("level,expected", [
        ("A1", 200), ("A2", 500), ("B1", 700),
        ("B2", 900), ("C1", 1100), ("C2", 1400),
    ])
    def test_known_levels(self, level, expected):
        assert cefr_to_elo(level) == expected

    def test_unknown_level_defaults_to_a1(self):
        assert cefr_to_elo("X9") == 200


class TestGetTargetLevels:
    def test_always_includes_current_level(self):
        for elo in [200, 500, 700, 900, 1100, 1300]:
            current = elo_to_cefr(elo)
            assert current in get_target_levels(elo)

    def test_top_of_band_includes_next_level(self):
        levels = get_target_levels(390)
        assert "A2" in levels

    def test_bottom_of_band_includes_previous_level(self):
        levels = get_target_levels(405)
        assert "A1" in levels

    def test_middle_of_band_only_current_level(self):
        levels = get_target_levels(750)
        assert levels == ["B1"]

    def test_no_level_beyond_c2(self):
        levels = get_target_levels(1580)
        assert all(l in CEFR_ORDER for l in levels)

    def test_no_level_below_a1(self):
        levels = get_target_levels(10)
        assert all(l in CEFR_ORDER for l in levels)


class TestEstimateQuality:
    def test_incorrect_slow_gives_quality_1(self):
        assert estimate_quality(False, False, 30.0, "multiple-choice") == 1

    def test_incorrect_fast_gives_quality_2(self):
        assert estimate_quality(False, False, 4.0, "multiple-choice") == 2

    def test_correct_with_hint_gives_quality_3(self):
        assert estimate_quality(True, True, 8.0, "multiple-choice") == 3

    def test_correct_fast_no_hint_gives_quality_5(self):
        assert estimate_quality(True, False, 2.0, "multiple-choice") == 5

    def test_correct_normal_speed_gives_quality_4(self):
        assert estimate_quality(True, False, 6.0, "multiple-choice") == 4

    def test_correct_slow_gives_quality_3_or_2(self):
        q = estimate_quality(True, False, 20.0, "multiple-choice")
        assert q in (2, 3)

    def test_fill_in_blank_uses_correct_expected_time(self):
        assert estimate_quality(True, False, 9.0, "fill-in-the-blank") == 5


class TestSM2:
    def _run_sm2(self, is_correct, used_hint, response_time, ex_type,
                 consecutive, ef=2.5, last_interval=1):
        _, new_ef, new_interval, quality = calculate_next_review_sm2(
            is_correct, used_hint, response_time, ex_type,
            consecutive, ef, last_interval
        )
        return new_ef, new_interval, quality

    def test_first_correct_answer_gives_interval_1(self):
        _, interval, _ = self._run_sm2(True, False, 4.0, "multiple-choice", consecutive=0)
        assert interval == 1

    def test_second_correct_gives_interval_6(self):
        _, interval, _ = self._run_sm2(True, False, 4.0, "multiple-choice", consecutive=1)
        assert interval == 6

    def test_third_correct_grows_interval(self):
        _, interval, _ = self._run_sm2(True, False, 4.0, "multiple-choice", consecutive=2, ef=2.5, last_interval=6)
        assert interval > 6

    def test_wrong_answer_resets_interval_to_1(self):
        _, interval, _ = self._run_sm2(False, False, 15.0, "multiple-choice", consecutive=5)
        assert interval == 1

    def test_ef_never_below_1_3(self):
        for _ in range(20):
            new_ef, _, _ = self._run_sm2(False, False, 20.0, "multiple-choice", consecutive=0, ef=1.3, last_interval=1)
            assert new_ef >= 1.3

    def test_high_quality_increases_ef(self):
        ef_before = 2.5
        new_ef, _, q = self._run_sm2(True, False, 2.0, "multiple-choice", consecutive=2, ef=ef_before, last_interval=6)

        assert q == 5
        assert new_ef > ef_before

    def test_low_quality_does_not_increase_ef(self):
        ef_before = 2.5
        new_ef, _, _ = self._run_sm2(False, False, 20.0, "multiple-choice", consecutive=0, ef=ef_before, last_interval=1)
        assert new_ef <= ef_before

    def test_interval_grows_over_multiple_repetitions(self):
        ef, interval, consecutive = 2.5, 1, 0
        intervals = []
        for _ in range(5):
            ef, interval, _ = self._run_sm2(
                True, False, 3.0, "multiple-choice",
                consecutive=consecutive, ef=ef, last_interval=interval
            )
            consecutive += 1
            intervals.append(interval)
      
        assert intervals[-1] > intervals[0]
