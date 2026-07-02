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
    table.add_column("Deuces", justify="center")
    table.add_column("Serving", justify="center")
    table.add_column("W(L10)", justify="right")
    table.add_column("W(S6)", justify="right")
    table.add_column("P(YES)", justify="right")
    table.add_column("EV Y/N", justify="right")
    table.add_column("Signal", justify="center", style="bold")
    table.add_column("Status", justify="center")

    t_no = d_threshold_no(cfg.scanner.default_odds_no, cfg.scanner.enter_margin)
    t_yes = d_threshold_yes(cfg.scanner.default_odds_yes, cfg.scanner.enter_margin)

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
                0.0,
            )

            long_rate = state.windowed_deuce_rate(cfg.scanner.win_long)
            short_rate = state.windowed_deuce_rate(cfg.scanner.win_short)

            signal = "—"
            signal_style = ""
            if long_rate is not None and short_rate is not None and state.current_set >= cfg.scanner.min_set:
                if long_rate <= t_no and short_rate <= t_no:
                    signal = "NO"
                    signal_style = "bold red"
                elif long_rate >= t_yes and short_rate >= t_yes:
                    signal = "YES"
                    signal_style = "bold green"

            ev_yes_str = f"{result.ev_yes:+.1%}"
            ev_no_str = f"{result.ev_no:+.1%}"
            ev_combined = f"[green]{ev_yes_str}[/green]" if result.ev_yes > 0 else ev_yes_str
            ev_combined += " / "
            ev_combined += f"[green]{ev_no_str}[/green]" if result.ev_no > 0 else ev_no_str

            long_str = f"{long_rate:.0%}" if long_rate is not None else "—"
            short_str = f"{short_rate:.0%}" if short_rate is not None else "—"

            status_parts = []
            if state.yes_state.halted:
                status_parts.append("Y:HALT")
            elif state.yes_state.loss_streak > 0:
                status_parts.append(f"Y:L{state.yes_state.loss_streak}")
            if state.no_state.halted:
                status_parts.append("N:HALT")
            elif state.no_state.loss_streak > 0:
                status_parts.append(f"N:L{state.no_state.loss_streak}")
            if state.match_net_pnl != 0:
                status_parts.append(f"£{state.match_net_pnl:+.0f}")
            status_str = " ".join(status_parts) if status_parts else "—"

            match_label = f"{state.player_a} vs {state.player_b}"
            if has_alert:
                match_label = f"[bold yellow]* {match_label}[/bold yellow]"

            total_deuces = state.deuces_a + state.deuces_b
            deuce_str = f"{total_deuces}/{state.total_games}"

            table.add_row(
                match_label,
                str(state.current_set),
                f"{state.total_games} ({est.games_a}A/{est.games_b}B)",
                deuce_str,
                serving,
                long_str,
                short_str,
                f"{result.p_yes:.1%}",
                ev_combined,
                f"[{signal_style}]{signal}[/{signal_style}]" if signal_style else signal,
                status_str,
            )

        scanner.alert_match_ids.clear()

    console.print(table)
    console.print(
        f"[dim]Windows: L{cfg.scanner.win_long}/S{cfg.scanner.win_short} | "
        f"NO when d < {t_no:.1%} | YES when d > {t_yes:.1%} | "
        f"Odds: YES={cfg.scanner.default_odds_yes:.4f} NO={cfg.scanner.default_odds_no:.4f} | "
        f"Halt after {cfg.scanner.loss_streak_halt} losses[/dim]"
    )
