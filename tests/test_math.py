"""Tests for core math module — verifies the formulae from BRIEF.md."""

import math
import pytest
from src.core.math import (
    compute_ev,
    d_threshold_no,
    d_threshold_yes,
    deuce_prob_from_p,
    fractional_to_decimal,
    decimal_to_implied,
    kelly_stake,
    p_no_two_games,
    p_yes_two_games,
)


class TestDeuceProb:
    def test_peaks_at_half(self):
        d = deuce_prob_from_p(0.5)
        assert abs(d - 0.3125) < 0.001

    def test_zero_at_extremes(self):
        assert deuce_prob_from_p(0.0) == 0.0
        assert deuce_prob_from_p(1.0) == 0.0

    def test_symmetric(self):
        assert abs(deuce_prob_from_p(0.3) - deuce_prob_from_p(0.7)) < 1e-10

    def test_big_server(self):
        d = deuce_prob_from_p(0.68)
        assert d < 0.21


class TestTwoGameProb:
    def test_identity(self):
        d = 0.25
        p_yes = p_yes_two_games(d, d)
        p_no = p_no_two_games(d, d)
        assert abs(p_yes + p_no - 1.0) < 1e-10

    def test_not_2d(self):
        """P(YES) = 2d - d², NOT 2d."""
        d = 0.3
        p_yes = p_yes_two_games(d, d)
        assert abs(p_yes - (2 * d - d**2)) < 1e-10
        assert abs(p_yes - 2 * d) > 0.01

    def test_asymmetric(self):
        p_yes = p_yes_two_games(0.1, 0.4)
        p_no = p_no_two_games(0.1, 0.4)
        assert abs(p_yes + p_no - 1.0) < 1e-10
        assert p_yes == pytest.approx(1 - 0.9 * 0.6)


class TestOdds:
    def test_4_6_decimal(self):
        assert abs(fractional_to_decimal(4, 6) - 1.6667) < 0.001

    def test_4_6_implied(self):
        dec = fractional_to_decimal(4, 6)
        imp = decimal_to_implied(dec)
        assert abs(imp - 0.6) < 0.001

    def test_6_4_decimal(self):
        assert abs(fractional_to_decimal(6, 4) - 2.5) < 0.001


class TestEV:
    def test_no_value_at_typical_rates(self):
        result = compute_ev(0.25, 0.25, 1.6667, 2.5, margin=0.10)
        assert result.side is None or result.ev_yes < 0.10

    def test_yes_value_high_deuce(self):
        result = compute_ev(0.45, 0.45, 1.6667, 2.5, margin=0.10)
        assert result.side == "YES"
        assert result.ev_yes > 0.10

    def test_no_value_low_deuce(self):
        result = compute_ev(0.10, 0.10, 1.6667, 2.5, margin=0.10)
        assert result.side == "NO"
        assert result.ev_no > 0.10


class TestThresholds:
    """Verify table from BRIEF.md at 4/6 odds."""

    def test_no_threshold_10pct(self):
        # Brief table assumes 4/6 = 1.6667 on both sides
        t = d_threshold_no(1.6667, 0.10)
        assert abs(t - 0.188) < 0.005

    def test_yes_threshold_10pct(self):
        t = d_threshold_yes(1.6667, 0.10)
        assert abs(t - 0.417) < 0.005

    def test_no_threshold_breakeven(self):
        t = d_threshold_no(1.6667, 0.0)
        assert abs(t - 0.225) < 0.005

    def test_yes_threshold_breakeven(self):
        t = d_threshold_yes(1.6667, 0.0)
        assert abs(t - 0.3675) < 0.005


class TestKelly:
    def test_no_edge_no_stake(self):
        assert kelly_stake(0.0, 2.5) == 0.0
        assert kelly_stake(-0.05, 2.5) == 0.0

    def test_positive_edge(self):
        s = kelly_stake(0.15, 2.5, fraction=0.25, bankroll=1000)
        assert s > 0
        assert s <= 30  # max 3 units at 10/unit

    def test_capped_at_max_units(self):
        s = kelly_stake(0.50, 2.5, fraction=1.0, bankroll=1000, max_units=3.0)
        assert s <= 30.0
