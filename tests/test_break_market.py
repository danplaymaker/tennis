"""Tests for break market math and model tracking."""

from src.core.math import break_prob_from_p, hold_prob_from_p, compute_break_ev, p_break_yes_two_games
from src.core.model import MatchState, PendingBet, PlayerPrior


class TestBreakMath:
    def test_hold_plus_break_equals_one(self):
        for p in (0.5, 0.6, 0.65, 0.7, 0.55):
            assert abs(hold_prob_from_p(p) + break_prob_from_p(p) - 1.0) < 1e-10

    def test_dominant_server_rarely_broken(self):
        assert break_prob_from_p(0.70) < 0.10

    def test_weak_server_often_broken(self):
        assert break_prob_from_p(0.50) > 0.30

    def test_p50_is_symmetric(self):
        assert abs(hold_prob_from_p(0.5) - 0.5) < 1e-10

    def test_break_yes_two_games(self):
        b_a, b_b = 0.2, 0.3
        expected = 1.0 - (1.0 - b_a) * (1.0 - b_b)
        assert abs(p_break_yes_two_games(b_a, b_b) - expected) < 1e-10

    def test_compute_break_ev_no_signal(self):
        result = compute_break_ev(0.15, 0.15, 1.6667, 1.6667, 0.10)
        assert result.p_yes < 0.4

    def test_compute_break_ev_returns_side(self):
        result = compute_break_ev(0.05, 0.05, 1.6667, 1.6667, 0.0)
        assert result.ev_no > 0


class TestBreakTracking:
    def test_break_counted(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=-1, server_held=False)
        assert state.breaks_a == 1
        assert state.breaks_b == 0

    def test_hold_not_counted_as_break(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=0, server_held=True)
        assert state.breaks_a == 0

    def test_unknown_margin_not_counted(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=-99, server_held=False)
        assert state.breaks_a == 0

    def test_empirical_break_rate(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("A", False, hold_margin=-1, server_held=False)
        assert abs(state.empirical_break_a - 0.5) < 0.001
        assert state.empirical_break_b is None

    def test_cumulative_break_rate(self):
        state = MatchState()
        for _ in range(8):
            state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("A", False, hold_margin=-1, server_held=False)
        state.record_game("B", False, hold_margin=-1, server_held=False)
        assert abs(state.cumulative_break_rate - 0.2) < 0.001

    def test_windowed_break_rate(self):
        state = MatchState()
        for _ in range(5):
            state.record_game("A", False, hold_margin=0, server_held=True)
        for _ in range(5):
            state.record_game("B", False, hold_margin=-1, server_held=False)
        rate = state.windowed_break_rate(10)
        assert abs(rate - 0.5) < 0.001

    def test_windowed_break_rate_returns_none_below_window(self):
        state = MatchState()
        for _ in range(3):
            state.record_game("A", False, hold_margin=0, server_held=True)
        assert state.windowed_break_rate(5) is None


class TestBreakEstimation:
    def test_prior_break_rate(self):
        # A: strong server, B: weak server, same returner strength
        state = MatchState(
            prior_a=PlayerPrior(spw=0.68, rpw=0.38),
            prior_b=PlayerPrior(spw=0.58, rpw=0.38),
        )
        best = state.estimate_break_rates()
        assert best.b_a > 0
        assert best.b_b > 0
        assert best.b_a < best.b_b  # stronger server broken less

    def test_shrinkage_toward_empirical(self):
        state = MatchState(
            prior_a=PlayerPrior(spw=0.65, rpw=0.35),
            prior_b=PlayerPrior(spw=0.60, rpw=0.40),
        )
        est_before = state.estimate_break_rates()

        for _ in range(10):
            state.record_game("A", False, hold_margin=-1, server_held=False)

        est_after = state.estimate_break_rates()
        assert est_after.b_a > est_before.b_a

    def test_floor_ceil(self):
        state = MatchState(prior_a=PlayerPrior(spw=0.70))
        for _ in range(20):
            state.record_game("A", False, hold_margin=0, server_held=True)
        est = state.estimate_break_rates(b_floor=0.05, b_ceil=0.50)
        assert est.b_a >= 0.05


class TestBreakBetSettlement:
    def test_settle_break_yes_win(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(
            side="YES", fired_at_game=0, odds=1.6667, stake=10.0, market="break",
        ))
        state.record_game("A", False, hold_margin=-1, server_held=False)
        state.record_game("B", False, hold_margin=0, server_held=True)
        settled = state.settle_pending_bets()
        assert len(settled) == 1
        assert settled[0][1] is True

    def test_settle_break_no_win(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(
            side="NO", fired_at_game=0, odds=1.6667, stake=10.0, market="break",
        ))
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("B", False, hold_margin=1, server_held=True)
        settled = state.settle_pending_bets()
        assert len(settled) == 1
        assert settled[0][1] is True

    def test_settle_break_yes_loss(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(
            side="YES", fired_at_game=0, odds=1.6667, stake=10.0, market="break",
        ))
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("B", False, hold_margin=0, server_held=True)
        settled = state.settle_pending_bets()
        assert settled[0][1] is False

    def test_break_loss_streak_tracked_separately(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(
            side="NO", fired_at_game=0, odds=1.6667, stake=10.0, market="break",
        ))
        state.record_game("A", False, hold_margin=-1, server_held=False)
        state.record_game("B", False, hold_margin=0, server_held=True)
        state.settle_pending_bets()
        assert state.break_no_state.loss_streak == 1
        assert state.no_state.loss_streak == 0  # deuce NO unaffected
