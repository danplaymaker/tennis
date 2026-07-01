"""Deuce rate estimation with Bayesian shrinkage toward a prior."""

from __future__ import annotations

from dataclasses import dataclass, field

from .math import DeuceEstimate, deuce_prob_from_p, server_point_win_prob


@dataclass
class PlayerPrior:
    spw: float = 0.62  # serve points won %
    rpw: float = 0.38  # return points won %
    surface: str = "hard"

    @property
    def point_win_prob(self) -> float:
        return self.spw

    @property
    def deuce_prior(self) -> float:
        return deuce_prob_from_p(self.spw)


SURFACE_SPW_ADJUSTMENT = {
    "hard": 0.0,
    "clay": -0.02,
    "grass": +0.03,
    "carpet": +0.02,
}


@dataclass
class MatchState:
    player_a: str = ""
    player_b: str = ""
    prior_a: PlayerPrior = field(default_factory=PlayerPrior)
    prior_b: PlayerPrior = field(default_factory=PlayerPrior)
    current_set: int = 1
    games_a_served: int = 0
    games_b_served: int = 0
    deuces_a: int = 0  # deuce games when A served
    deuces_b: int = 0  # deuce games when B served
    next_server: str = "A"
    total_games: int = 0
    last_alert_game: int = -10
    match_id: str = ""
    surface: str = "hard"

    @property
    def empirical_d_a(self) -> float | None:
        if self.games_a_served == 0:
            return None
        return self.deuces_a / self.games_a_served

    @property
    def empirical_d_b(self) -> float | None:
        if self.games_b_served == 0:
            return None
        return self.deuces_b / self.games_b_served

    def estimate_deuce_rates(self, prior_weight: float = 6.0) -> DeuceEstimate:
        """Shrinkage estimator blending prior with in-match observations.

        prior_weight: equivalent number of "prior games" — controls how fast
        the estimate moves away from the prior as real games accumulate.
        """
        adj = SURFACE_SPW_ADJUSTMENT.get(self.surface, 0.0)

        p_a = server_point_win_prob(
            self.prior_a.spw + adj, self.prior_b.rpw
        )
        p_b = server_point_win_prob(
            self.prior_b.spw + adj, self.prior_a.rpw
        )

        prior_d_a = deuce_prob_from_p(p_a)
        prior_d_b = deuce_prob_from_p(p_b)

        w_a = self.games_a_served
        w_b = self.games_b_served
        emp_a = self.empirical_d_a if self.empirical_d_a is not None else prior_d_a
        emp_b = self.empirical_d_b if self.empirical_d_b is not None else prior_d_b

        d_a = (prior_weight * prior_d_a + w_a * emp_a) / (prior_weight + w_a)
        d_b = (prior_weight * prior_d_b + w_b * emp_b) / (prior_weight + w_b)

        return DeuceEstimate(
            d_a=d_a, d_b=d_b, games_a=self.games_a_served, games_b=self.games_b_served
        )

    def record_game(self, server: str, was_deuce: bool) -> None:
        if server == "A":
            self.games_a_served += 1
            if was_deuce:
                self.deuces_a += 1
        else:
            self.games_b_served += 1
            if was_deuce:
                self.deuces_b += 1
        self.total_games += 1
        self.next_server = "B" if server == "A" else "A"
