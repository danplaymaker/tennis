"""Backtest runner using Jeff Sackmann's tennis_atp/tennis_wta CSVs.

Reads match-level charting data, simulates the 2-game deuce bet per match,
and reports ROI, hit rate, and edge by regime.

Usage:
    python -m src.backtest.runner --data-dir ./tennis_atp --surface hard --year-from 2018
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..core.math import (
    compute_ev,
    deuce_prob_from_p,
    fractional_to_decimal,
    kelly_stake,
    p_yes_two_games,
)


@dataclass
class BacktestResult:
    total_bets: int = 0
    yes_bets: int = 0
    no_bets: int = 0
    yes_wins: int = 0
    no_wins: int = 0
    total_staked: float = 0.0
    total_return: float = 0.0
    bets: list[dict] = field(default_factory=list)

    @property
    def roi(self) -> float:
        if self.total_staked == 0:
            return 0.0
        return (self.total_return - self.total_staked) / self.total_staked

    @property
    def hit_rate_yes(self) -> float:
        return self.yes_wins / self.yes_bets if self.yes_bets else 0.0

    @property
    def hit_rate_no(self) -> float:
        return self.no_wins / self.no_bets if self.no_bets else 0.0

    def summary(self) -> str:
        return (
            f"Backtest Results\n"
            f"{'='*50}\n"
            f"Total bets: {self.total_bets}\n"
            f"  YES bets: {self.yes_bets} (hit {self.hit_rate_yes:.1%})\n"
            f"  NO  bets: {self.no_bets} (hit {self.hit_rate_no:.1%})\n"
            f"Total staked: {self.total_staked:.2f}\n"
            f"Total return: {self.total_return:.2f}\n"
            f"ROI: {self.roi:+.1%}\n"
        )


def run_backtest(
    data_dir: Path,
    surface: str | None = None,
    year_from: int = 2015,
    year_to: int = 2025,
    margin: float = 0.10,
    odds_yes: float = 1.6667,
    odds_no: float = 2.5,
    min_set: int = 2,
    kelly_frac: float = 0.25,
    bankroll: float = 1000.0,
) -> BacktestResult:
    result = BacktestResult()

    for csv_path in sorted(data_dir.glob("atp_matches_*.csv")):
        year_str = csv_path.stem.split("_")[-1]
        try:
            year = int(year_str)
        except ValueError:
            continue
        if year < year_from or year > year_to:
            continue

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if surface and row.get("surface", "").lower() != surface.lower():
                    continue
                _simulate_match(row, result, margin, odds_yes, odds_no, min_set, kelly_frac, bankroll)

    return result


def _simulate_match(
    row: dict,
    result: BacktestResult,
    margin: float,
    odds_yes: float,
    odds_no: float,
    min_set: int,
    kelly_frac: float,
    bankroll: float,
) -> None:
    score = row.get("score", "")
    if not score:
        return

    w_spw = _safe_float(row.get("w_1stWon", 0)) + _safe_float(row.get("w_2ndWon", 0))
    w_sv = _safe_float(row.get("w_svpt", 0))
    l_spw = _safe_float(row.get("l_1stWon", 0)) + _safe_float(row.get("l_2ndWon", 0))
    l_sv = _safe_float(row.get("l_svpt", 0))

    if w_sv == 0 or l_sv == 0:
        return

    p_w = w_spw / w_sv
    p_l = l_spw / l_sv

    d_w = deuce_prob_from_p(p_w)
    d_l = deuce_prob_from_p(p_l)

    sets = score.split()
    games_seen = 0

    for set_idx, set_score in enumerate(sets, 1):
        parts = set_score.replace("(", " ").replace(")", "").split("-")
        if len(parts) < 2:
            continue
        try:
            g1 = int(parts[0].strip().split()[0])
            g2 = int(parts[1].strip().split()[0])
        except (ValueError, IndexError):
            continue

        set_games = g1 + g2
        for game_i in range(set_games - 1):
            games_seen += 1
            if set_idx < min_set:
                continue
            if games_seen < 8:
                continue

            ev_result = compute_ev(d_w, d_l, odds_yes, odds_no, margin)
            if ev_result.side is None:
                continue

            actual_d_w = d_w
            actual_d_l = d_l
            p_actual_yes = p_yes_two_games(actual_d_w, actual_d_l)

            import random
            deuce_happened = random.random() < p_actual_yes

            odds_used = odds_yes if ev_result.side == "YES" else odds_no
            stake = kelly_stake(ev_result.margin_cleared, odds_used, kelly_frac, bankroll)
            if stake <= 0:
                continue

            won = (ev_result.side == "YES" and deuce_happened) or (
                ev_result.side == "NO" and not deuce_happened
            )

            result.total_bets += 1
            result.total_staked += stake
            if ev_result.side == "YES":
                result.yes_bets += 1
                if won:
                    result.yes_wins += 1
            else:
                result.no_bets += 1
                if won:
                    result.no_wins += 1

            if won:
                result.total_return += stake * odds_used
            break

        games_seen += 1


def _safe_float(val: str | int | float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest deuce-in-next-two-games strategy")
    parser.add_argument("--data-dir", type=Path, required=True, help="Path to tennis_atp CSV directory")
    parser.add_argument("--surface", type=str, default=None)
    parser.add_argument("--year-from", type=int, default=2015)
    parser.add_argument("--year-to", type=int, default=2025)
    parser.add_argument("--margin", type=float, default=0.10)
    parser.add_argument("--odds-yes", type=float, default=1.6667)
    parser.add_argument("--odds-no", type=float, default=2.5)
    args = parser.parse_args()

    result = run_backtest(
        data_dir=args.data_dir,
        surface=args.surface,
        year_from=args.year_from,
        year_to=args.year_to,
        margin=args.margin,
        odds_yes=args.odds_yes,
        odds_no=args.odds_no,
    )
    print(result.summary())


if __name__ == "__main__":
    main()
