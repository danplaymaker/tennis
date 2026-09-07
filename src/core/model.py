"""Deuce rate estimation with rolling windows and circuit breaker."""

from __future__ import annotations

from dataclasses import dataclass, field

from .math import (
    BreakEstimate,
    DeuceEstimate,
    break_prob_from_p,
    deuce_prob_from_p,
    server_point_win_prob,
)


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
class GameRecord:
    server: str  # "A" or "B"
    was_deuce: bool
    is_tiebreak: bool = False
    hold_margin: int = -99  # returner's max score: 0=love,1=15,2=30,3=40,4=deuce,-1=broken,-99=unknown
    server_held: bool = True


@dataclass
class PendingBet:
    side: str  # "YES" or "NO"
    fired_at_game: int  # total_games when alert fired
    odds: float
    stake: float
    market: str = "deuce"  # "deuce" or "break"


@dataclass
class SideState:
    armed: bool = True
    hot: bool = False  # EV crossed ENTER, waiting for EXIT to re-arm
    loss_streak: int = 0
    halted: bool = False


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
    game_history: list = field(default_factory=list)
    pending_bets: list = field(default_factory=list)
    yes_state: SideState = field(default_factory=SideState)
    no_state: SideState = field(default_factory=SideState)
    # Break market state
    breaks_a: int = 0  # times A was broken
    breaks_b: int = 0  # times B was broken
    break_yes_state: SideState = field(default_factory=SideState)
    break_no_state: SideState = field(default_factory=SideState)
    match_total_staked: float = 0.0
    match_net_pnl: float = 0.0
    _seen_game_keys: set = field(default_factory=set)

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

    @property
    def cumulative_deuce_rate(self) -> float | None:
        if self.total_games == 0:
            return None
        return (self.deuces_a + self.deuces_b) / self.total_games

    def windowed_deuce_rate(self, window: int) -> float | None:
        """Match-level deuce rate over last `window` non-tiebreak games."""
        non_tb = [g for g in self.game_history if not g.is_tiebreak]
        if len(non_tb) < window:
            return None
        recent = non_tb[-window:]
        return sum(1 for g in recent if g.was_deuce) / window

    def windowed_deuce_count(self, window: int) -> int | None:
        """Count of deuces in last `window` non-tiebreak games."""
        non_tb = [g for g in self.game_history if not g.is_tiebreak]
        if len(non_tb) < window:
            return None
        return sum(1 for g in non_tb[-window:] if g.was_deuce)

    def hold_quality(self, server: str) -> dict[str, int]:
        """Hold quality distribution for a server. Returns counts keyed by margin label."""
        counts = {"love": 0, "15": 0, "30": 0, "40": 0, "deuce": 0, "broken": 0}
        margin_labels = {0: "love", 1: "15", 2: "30", 3: "40", 4: "deuce", -1: "broken"}
        for g in self.game_history:
            if g.is_tiebreak or g.server != server or g.hold_margin == -99:
                continue
            label = margin_labels.get(g.hold_margin, "40")
            counts[label] += 1
        return counts

    def dominance_score(self, server: str) -> float | None:
        """Fraction of holds (excluding breaks) that were clean (love/15/30)."""
        quality = self.hold_quality(server)
        holds = quality["love"] + quality["15"] + quality["30"] + quality["40"] + quality["deuce"]
        if holds == 0:
            return None
        return (quality["love"] + quality["15"] + quality["30"]) / holds

    def clean_service_pct(self, server: str) -> float | None:
        """Fraction of all service games (including breaks) held cleanly."""
        quality = self.hold_quality(server)
        total = sum(quality.values())
        if total == 0:
            return None
        return (quality["love"] + quality["15"] + quality["30"]) / total

    # --- Break rate tracking ---

    @property
    def empirical_break_a(self) -> float | None:
        """Empirical break rate when A serves (how often A gets broken)."""
        if self.games_a_served == 0:
            return None
        return self.breaks_a / self.games_a_served

    @property
    def empirical_break_b(self) -> float | None:
        if self.games_b_served == 0:
            return None
        return self.breaks_b / self.games_b_served

    @property
    def cumulative_break_rate(self) -> float | None:
        if self.total_games == 0:
            return None
        return (self.breaks_a + self.breaks_b) / self.total_games

    def windowed_break_rate(self, window: int) -> float | None:
        """Break rate over last `window` non-tiebreak games."""
        non_tb = [g for g in self.game_history if not g.is_tiebreak]
        if len(non_tb) < window:
            return None
        return sum(1 for g in non_tb[-window:] if not g.server_held and g.hold_margin != -99) / window

    def windowed_break_count(self, window: int) -> int | None:
        """Count of breaks in last `window` non-tiebreak games."""
        non_tb = [g for g in self.game_history if not g.is_tiebreak]
        if len(non_tb) < window:
            return None
        return sum(1 for g in non_tb[-window:] if not g.server_held and g.hold_margin != -99)

    def estimate_break_rates(self, prior_weight: float = 4.0,
                             b_floor: float = 0.0, b_ceil: float = 1.0) -> BreakEstimate:
        """Shrinkage estimator for break probability per server."""
        adj = SURFACE_SPW_ADJUSTMENT.get(self.surface, 0.0)

        p_a = server_point_win_prob(
            self.prior_a.spw + adj, self.prior_b.rpw
        )
        p_b = server_point_win_prob(
            self.prior_b.spw + adj, self.prior_a.rpw
        )

        prior_b_a = break_prob_from_p(p_a)
        prior_b_b = break_prob_from_p(p_b)

        w_a = self.games_a_served
        w_b = self.games_b_served
        emp_a = self.empirical_break_a if self.empirical_break_a is not None else prior_b_a
        emp_b = self.empirical_break_b if self.empirical_break_b is not None else prior_b_b

        b_a = (prior_weight * prior_b_a + w_a * emp_a) / (prior_weight + w_a)
        b_b = (prior_weight * prior_b_b + w_b * emp_b) / (prior_weight + w_b)

        b_a = min(max(b_a, b_floor), b_ceil)
        b_b = min(max(b_b, b_floor), b_ceil)

        return BreakEstimate(
            b_a=b_a, b_b=b_b, games_a=self.games_a_served, games_b=self.games_b_served
        )

    def estimate_deuce_rates(self, prior_weight: float = 4.0,
                             d_floor: float = 0.0, d_ceil: float = 1.0) -> DeuceEstimate:
        """Shrinkage estimator blending prior with in-match observations."""
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

        d_a = min(max(d_a, d_floor), d_ceil)
        d_b = min(max(d_b, d_floor), d_ceil)

        return DeuceEstimate(
            d_a=d_a, d_b=d_b, games_a=self.games_a_served, games_b=self.games_b_served
        )

    def record_game(self, server: str, was_deuce: bool, is_tiebreak: bool = False,
                    hold_margin: int = -99, server_held: bool = True) -> None:
        self.game_history.append(GameRecord(
            server=server, was_deuce=was_deuce, is_tiebreak=is_tiebreak,
            hold_margin=hold_margin, server_held=server_held,
        ))
        if not is_tiebreak:
            if server == "A":
                self.games_a_served += 1
                if was_deuce:
                    self.deuces_a += 1
                if not server_held and hold_margin != -99:
                    self.breaks_a += 1
            else:
                self.games_b_served += 1
                if was_deuce:
                    self.deuces_b += 1
                if not server_held and hold_margin != -99:
                    self.breaks_b += 1
            self.total_games += 1
            self.next_server = "B" if server == "A" else "A"

    def settle_pending_bets(self) -> list:
        """Settle bets whose 2-game window has completed. Returns [(bet, won), ...]."""
        non_tb = [g for g in self.game_history if not g.is_tiebreak]
        settled = []
        remaining = []
        for bet in self.pending_bets:
            if self.total_games >= bet.fired_at_game + 2:
                idx1 = bet.fired_at_game
                idx2 = bet.fired_at_game + 1

                if bet.market == "break":
                    had_event = False
                    if idx1 < len(non_tb):
                        g = non_tb[idx1]
                        had_event = had_event or (not g.server_held and g.hold_margin != -99)
                    if idx2 < len(non_tb):
                        g = non_tb[idx2]
                        had_event = had_event or (not g.server_held and g.hold_margin != -99)
                else:
                    had_event = False
                    if idx1 < len(non_tb):
                        had_event = had_event or non_tb[idx1].was_deuce
                    if idx2 < len(non_tb):
                        had_event = had_event or non_tb[idx2].was_deuce

                won = (bet.side == "YES" and had_event) or (bet.side == "NO" and not had_event)
                payout = bet.stake * (bet.odds - 1) if won else -bet.stake
                self.match_net_pnl += payout

                side_state = self._side_state(bet.market, bet.side)
                if won:
                    side_state.loss_streak = 0
                else:
                    side_state.loss_streak += 1
                settled.append((bet, won))
            else:
                remaining.append(bet)
        self.pending_bets = remaining
        return settled

    def _side_state(self, market: str, side: str) -> SideState:
        """Get the SideState for a given market and side."""
        if market == "break":
            return self.break_yes_state if side == "YES" else self.break_no_state
        return self.yes_state if side == "YES" else self.no_state
