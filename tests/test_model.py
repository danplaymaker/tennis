"""Tests for the deuce rate estimation model."""

from src.core.model import GameRecord, MatchState, PendingBet, PlayerPrior, SideState


class TestMatchState:
    def test_initial_estimate_uses_prior(self):
        state = MatchState(
            prior_a=PlayerPrior(spw=0.65, rpw=0.35),
            prior_b=PlayerPrior(spw=0.60, rpw=0.40),
        )
        est = state.estimate_deuce_rates()
        assert est.d_a > 0
        assert est.d_b > 0
        assert est.games_a == 0
        assert est.games_b == 0

    def test_shrinkage_moves_toward_empirical(self):
        state = MatchState(
            prior_a=PlayerPrior(spw=0.65, rpw=0.35),
            prior_b=PlayerPrior(spw=0.60, rpw=0.40),
        )
        est_before = state.estimate_deuce_rates()

        for _ in range(10):
            state.record_game("A", was_deuce=True)

        est_after = state.estimate_deuce_rates()
        assert est_after.d_a > est_before.d_a

    def test_server_alternates(self):
        state = MatchState(next_server="A")
        state.record_game("A", False)
        assert state.next_server == "B"
        state.record_game("B", True)
        assert state.next_server == "A"
        assert state.deuces_b == 1
        assert state.deuces_a == 0

    def test_surface_adjustment(self):
        hard = MatchState(surface="hard", prior_a=PlayerPrior(spw=0.62))
        clay = MatchState(surface="clay", prior_a=PlayerPrior(spw=0.62))

        est_hard = hard.estimate_deuce_rates()
        est_clay = clay.estimate_deuce_rates()
        assert est_clay.d_a > est_hard.d_a

    def test_d_match_average(self):
        state = MatchState()
        for _ in range(4):
            state.record_game("A", True)
        for _ in range(6):
            state.record_game("B", False)

        est = state.estimate_deuce_rates()
        assert est.d_match == (est.d_a * 4 + est.d_b * 6) / 10

    def test_d_floor_ceil(self):
        state = MatchState(prior_a=PlayerPrior(spw=0.65, rpw=0.35))
        for _ in range(20):
            state.record_game("A", was_deuce=False)
        est = state.estimate_deuce_rates(d_floor=0.08, d_ceil=0.42)
        assert est.d_a >= 0.08

    def test_cumulative_deuce_rate(self):
        state = MatchState()
        for _ in range(3):
            state.record_game("A", True)
        for _ in range(7):
            state.record_game("B", False)
        assert abs(state.cumulative_deuce_rate - 0.3) < 0.001

    def test_cumulative_deuce_rate_none_when_empty(self):
        state = MatchState()
        assert state.cumulative_deuce_rate is None


class TestGameHistory:
    def test_record_game_appends_history(self):
        state = MatchState()
        state.record_game("A", True)
        state.record_game("B", False)
        assert len(state.game_history) == 2
        assert state.game_history[0].server == "A"
        assert state.game_history[0].was_deuce is True
        assert state.game_history[1].server == "B"
        assert state.game_history[1].was_deuce is False

    def test_tiebreak_recorded(self):
        state = MatchState()
        state.record_game("A", False, is_tiebreak=True)
        assert state.game_history[0].is_tiebreak is True
        assert state.total_games == 0
        assert state.games_a_served == 0


class TestWindowedRate:
    def test_returns_none_below_window(self):
        state = MatchState()
        for _ in range(5):
            state.record_game("A", False)
        assert state.windowed_deuce_rate(6) is None

    def test_exact_window(self):
        state = MatchState()
        for _ in range(4):
            state.record_game("A", True)
        for _ in range(6):
            state.record_game("B", False)
        rate = state.windowed_deuce_rate(10)
        assert abs(rate - 0.4) < 0.001

    def test_sliding_window(self):
        state = MatchState()
        for _ in range(6):
            state.record_game("A", False)
        for _ in range(6):
            state.record_game("B", True)
        rate = state.windowed_deuce_rate(6)
        assert abs(rate - 1.0) < 0.001

    def test_excludes_tiebreaks(self):
        state = MatchState()
        for _ in range(5):
            state.record_game("A", False)
        state.record_game("A", True, is_tiebreak=True)
        for _ in range(5):
            state.record_game("B", False)
        rate = state.windowed_deuce_rate(10)
        assert abs(rate - 0.0) < 0.001


class TestSettleBets:
    def test_settle_yes_win(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(side="YES", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", True)
        state.record_game("B", False)
        settled = state.settle_pending_bets()
        assert len(settled) == 1
        assert settled[0][1] is True  # won
        assert state.match_net_pnl > 0
        assert state.yes_state.loss_streak == 0

    def test_settle_yes_loss(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(side="YES", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", False)
        state.record_game("B", False)
        settled = state.settle_pending_bets()
        assert len(settled) == 1
        assert settled[0][1] is False  # lost
        assert state.match_net_pnl < 0
        assert state.yes_state.loss_streak == 1

    def test_settle_no_win(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(side="NO", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", False)
        state.record_game("B", False)
        settled = state.settle_pending_bets()
        assert settled[0][1] is True

    def test_settle_no_loss(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(side="NO", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", True)
        state.record_game("B", False)
        settled = state.settle_pending_bets()
        assert settled[0][1] is False
        assert state.no_state.loss_streak == 1

    def test_not_settled_until_two_games(self):
        state = MatchState()
        state.pending_bets.append(PendingBet(side="YES", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", True)
        settled = state.settle_pending_bets()
        assert len(settled) == 0
        assert len(state.pending_bets) == 1

    def test_loss_streak_accumulates(self):
        state = MatchState()
        for i in range(3):
            state.pending_bets.append(PendingBet(side="NO", fired_at_game=i * 2, odds=1.6667, stake=10.0))
            state.record_game("A", True)
            state.record_game("B", False)
        state.settle_pending_bets()
        assert state.no_state.loss_streak == 3

    def test_win_resets_streak(self):
        state = MatchState()
        state.no_state.loss_streak = 2
        state.pending_bets.append(PendingBet(side="NO", fired_at_game=0, odds=1.6667, stake=10.0))
        state.record_game("A", False)
        state.record_game("B", False)
        state.settle_pending_bets()
        assert state.no_state.loss_streak == 0


class TestHoldQuality:
    def test_hold_quality_counts(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("A", False, hold_margin=1, server_held=True)
        state.record_game("A", False, hold_margin=2, server_held=True)
        q = state.hold_quality("A")
        assert q["love"] == 2
        assert q["15"] == 1
        assert q["30"] == 1
        assert q["40"] == 0
        assert q["deuce"] == 0
        assert q["broken"] == 0

    def test_hold_quality_broken(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=-1, server_held=False)
        q = state.hold_quality("A")
        assert q["broken"] == 1

    def test_hold_quality_deuce(self):
        state = MatchState()
        state.record_game("B", True, hold_margin=4, server_held=True)
        q = state.hold_quality("B")
        assert q["deuce"] == 1

    def test_hold_quality_ignores_tiebreaks(self):
        state = MatchState()
        state.record_game("A", False, is_tiebreak=True, hold_margin=0, server_held=True)
        q = state.hold_quality("A")
        assert sum(q.values()) == 0

    def test_hold_quality_ignores_other_server(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("B", False, hold_margin=2, server_held=True)
        q = state.hold_quality("A")
        assert q["love"] == 1
        assert sum(q.values()) == 1

    def test_dominance_score(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=0, server_held=True)
        state.record_game("A", False, hold_margin=1, server_held=True)
        state.record_game("A", False, hold_margin=2, server_held=True)
        state.record_game("A", True, hold_margin=4, server_held=True)
        dom = state.dominance_score("A")
        assert abs(dom - 0.75) < 0.001

    def test_dominance_score_empty(self):
        state = MatchState()
        assert state.dominance_score("A") is None

    def test_dominance_ignores_unknown(self):
        state = MatchState()
        state.record_game("A", False, hold_margin=-99, server_held=True)
        state.record_game("A", False, hold_margin=0, server_held=True)
        dom = state.dominance_score("A")
        assert abs(dom - 1.0) < 0.001
