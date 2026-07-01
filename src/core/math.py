"""Core probability and EV calculations for deuce-in-next-two-games betting."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DeuceEstimate:
    d_a: float  # P(deuce) when player A serves
    d_b: float  # P(deuce) when player B serves
    games_a: int  # service games observed for A
    games_b: int  # service games observed for B

    @property
    def d_match(self) -> float:
        total = self.games_a + self.games_b
        if total == 0:
            return (self.d_a + self.d_b) / 2
        return (self.d_a * self.games_a + self.d_b * self.games_b) / total


@dataclass(frozen=True)
class EVResult:
    p_yes: float
    p_no: float
    ev_yes: float
    ev_no: float
    side: str | None  # "YES", "NO", or None
    margin_cleared: float


def deuce_prob_from_p(p: float) -> float:
    """Probability a single game reaches deuce given server point-win prob p.

    Uses the exact formula: d = 20 * p^3 * (1-p)^3.
    Peaks at ~31% when p=0.5, falls off for dominant servers.
    """
    return 20.0 * p**3 * (1 - p) ** 3


def server_point_win_prob(server_spw: float, returner_rpw: float) -> float:
    """Blend server SPW with returner RPW for adjusted point-win probability."""
    return (server_spw + (1 - returner_rpw)) / 2


def p_yes_two_games(d_a: float, d_b: float) -> float:
    """P(at least one deuce in next two games) = 1 - (1-d_A)(1-d_B)."""
    return 1.0 - (1.0 - d_a) * (1.0 - d_b)


def p_no_two_games(d_a: float, d_b: float) -> float:
    return (1.0 - d_a) * (1.0 - d_b)


def fractional_to_decimal(num: int, den: int) -> float:
    """Convert fractional odds (e.g. 4/6) to decimal (e.g. 1.6667)."""
    return 1.0 + num / den


def decimal_to_implied(decimal_odds: float) -> float:
    """Decimal odds to implied probability."""
    return 1.0 / decimal_odds


def compute_ev(
    d_a: float,
    d_b: float,
    odds_yes: float,
    odds_no: float,
    margin: float = 0.10,
) -> EVResult:
    """Compute EV for YES and NO sides. Returns which side (if any) clears margin."""
    p_y = p_yes_two_games(d_a, d_b)
    p_n = p_no_two_games(d_a, d_b)

    ev_y = p_y * odds_yes - 1.0
    ev_n = p_n * odds_no - 1.0

    side = None
    cleared = 0.0

    if ev_y >= margin and ev_y >= ev_n:
        side = "YES"
        cleared = ev_y
    elif ev_n >= margin:
        side = "NO"
        cleared = ev_n

    return EVResult(
        p_yes=p_y,
        p_no=p_n,
        ev_yes=ev_y,
        ev_no=ev_n,
        side=side,
        margin_cleared=cleared,
    )


def kelly_stake(
    edge: float,
    odds: float,
    fraction: float = 0.25,
    bankroll: float = 1000.0,
    max_units: float = 3.0,
) -> float:
    """Fractional Kelly stake. Returns stake amount."""
    if edge <= 0:
        return 0.0
    b = odds - 1.0
    if b <= 0:
        return 0.0
    p = (edge + 1.0) / odds
    full_kelly = (p * b - (1 - p)) / b
    stake = fraction * full_kelly * bankroll
    unit = bankroll / 100
    return min(stake, max_units * unit)


def d_threshold_no(odds_no: float, margin: float) -> float:
    """Max single-game deuce rate for NO to clear margin. d < this → bet NO."""
    return 1.0 - math.sqrt((1 + margin) / odds_no)


def d_threshold_yes(odds_yes: float, margin: float) -> float:
    """Min single-game deuce rate for YES to clear margin. d > this → bet YES."""
    return 1.0 - math.sqrt(1.0 - (1 + margin) / odds_yes)
