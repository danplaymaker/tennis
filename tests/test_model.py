"""Tests for the deuce rate estimation model."""

from src.core.model import MatchState, PlayerPrior


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
