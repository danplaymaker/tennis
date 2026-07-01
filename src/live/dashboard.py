"""Rich live dashboard showing all tracked matches and their deuce stats."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ..core.math import compute_ev, d_threshold_no, d_threshold_yes
from .scanner import LiveScanner


def print_dashboard(scanner: LiveScanner, console: Console | None = None) -> None:
    if console is None:
        console = Console()

    cfg = scanner.cfg

    table = Table(
        title="Deuce Scanner — Live Matches",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("Match", style="white", min_width=30)
    table.add_column("Set", justify="center")
    table.add_column("Games", justify="center")
    table.add_column("Serving", justify="center")
    table.add_column("d_A", justify="right")
    table.add_column("d_B", justify="right")
    table.add_column("P(YES)", justify="right")
    table.add_column("EV YES", justify="right")
    table.add_column("EV NO", justify="right")
    table.add_column("Signal", justify="center", style="bold")

    t_no = d_threshold_no(cfg.scanner.default_odds_no, cfg.scanner.margin)
    t_yes = d_threshold_yes(cfg.scanner.default_odds_yes, cfg.scanner.margin)

    if not scanner.matches:
        table.add_row("No live matches", *["—"] * 9)
    else:
        for state in sorted(scanner.matches.values(), key=lambda s: s.match_id):
            est = state.estimate_deuce_rates()
            has_alert = state.match_id in scanner.alert_match_ids

            if state.next_server == "A":
                d_next, d_after = est.d_a, est.d_b
                serving = state.player_a.split()[-1]
            else:
                d_next, d_after = est.d_b, est.d_a
                serving = state.player_b.split()[-1]

            result = compute_ev(
                d_next, d_after,
                cfg.scanner.default_odds_yes,
                cfg.scanner.default_odds_no,
                cfg.scanner.margin,
            )

            signal = "—"
            signal_style = ""
            if state.current_set >= cfg.scanner.min_set and state.total_games >= cfg.scanner.min_games_for_alert:
                if result.side == "YES":
                    signal = "YES"
                    signal_style = "bold green"
                elif result.side == "NO":
                    signal = "NO"
                    signal_style = "bold red"

            ev_yes_str = f"{result.ev_yes:+.1%}"
            ev_no_str = f"{result.ev_no:+.1%}"

            match_label = f"{state.player_a} vs {state.player_b}"
            if has_alert:
                match_label = f"[bold yellow]* {match_label}[/bold yellow]"

            table.add_row(
                match_label,
                str(state.current_set),
                f"{state.total_games} ({est.games_a}A/{est.games_b}B)",
                serving,
                f"{est.d_a:.1%}",
                f"{est.d_b:.1%}",
                f"{result.p_yes:.1%}",
                f"[green]{ev_yes_str}[/green]" if result.ev_yes > 0 else ev_yes_str,
                f"[green]{ev_no_str}[/green]" if result.ev_no > 0 else ev_no_str,
                f"[{signal_style}]{signal}[/{signal_style}]" if signal_style else signal,
            )

        scanner.alert_match_ids.clear()

    console.print(table)
    console.print(
        f"[dim]Thresholds at m={cfg.scanner.margin:.0%}: "
        f"NO when d < {t_no:.1%} | YES when d > {t_yes:.1%} | "
        f"Odds: YES={cfg.scanner.default_odds_yes:.4f} NO={cfg.scanner.default_odds_no:.4f}[/dim]"
    )
