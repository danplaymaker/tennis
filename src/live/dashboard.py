"""Rich live dashboard showing all tracked matches and their market stats."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ..core.math import compute_break_ev, compute_ev
from .scanner import LiveScanner


def print_dashboard(scanner: LiveScanner, console: Console | None = None) -> None:
    if console is None:
        console = Console()

    cfg = scanner.cfg

    table = Table(
        title="Tennis Flash Scanner — Live Matches",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("Match", style="white", min_width=30)
    table.add_column("Set", justify="center")
    table.add_column("Games", justify="center")
    table.add_column("Deuces", justify="center")
    table.add_column("Hold A", justify="center")
    table.add_column("Hold B", justify="center")
    table.add_column("Serving", justify="center")
    table.add_column("Rate", justify="right")
    table.add_column("d(est)", justify="right")
    table.add_column("P(YES)", justify="right")
    table.add_column("EV Y/N", justify="right")
    table.add_column("Signal", justify="center", style="bold")
    table.add_column("Status", justify="center")

    if not scanner.matches:
        table.add_row("No live matches", *["—"] * 12)
    else:
        for state in sorted(scanner.matches.values(), key=lambda s: s.match_id):
            est = state.estimate_deuce_rates(
                d_floor=cfg.scanner.d_floor, d_ceil=cfg.scanner.d_ceil,
            )
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

            is_set1 = state.current_set == 1
            long_rate = state.windowed_deuce_rate(cfg.scanner.win_long)
            cum_rate = state.cumulative_deuce_rate
            short_deuces = state.windowed_deuce_count(cfg.scanner.win_short)

            # Deuce conviction check (mirrors _evaluate logic)
            conv_yes = conv_no = False
            if is_set1:
                if state.total_games >= cfg.scanner.set1_min_games and cum_rate is not None:
                    if cum_rate <= cfg.scanner.no_set1_max:
                        conv_no = True
                    if cum_rate >= cfg.scanner.yes_set1_min:
                        conv_yes = True
            else:
                if long_rate is not None:
                    if long_rate <= cfg.scanner.no_post_max:
                        conv_no = True
                    if long_rate >= cfg.scanner.yes_post_min:
                        conv_yes = True
                if short_deuces is not None and short_deuces >= 2:
                    conv_no = False

            # Break market signal
            break_signal = ""
            if cfg.break_market.enabled:
                best = state.estimate_break_rates(
                    b_floor=cfg.break_market.b_floor, b_ceil=cfg.break_market.b_ceil,
                )
                if state.next_server == "A":
                    b_next, b_after = best.b_a, best.b_b
                else:
                    b_next, b_after = best.b_b, best.b_a

                bresult = compute_break_ev(
                    b_next, b_after,
                    cfg.break_market.default_odds_yes,
                    cfg.break_market.default_odds_no,
                    0.0,
                )

                bcfg = cfg.break_market
                bconv_yes = bconv_no = False
                if is_set1:
                    if state.total_games >= bcfg.set1_min_games:
                        bcum = state.cumulative_break_rate
                        if bcum is not None:
                            if bcum <= bcfg.no_set1_max:
                                bconv_no = True
                            if bcum >= bcfg.yes_set1_min:
                                bconv_yes = True
                else:
                    blong = state.windowed_break_rate(cfg.scanner.win_long)
                    if blong is not None:
                        if blong <= bcfg.no_post_max:
                            bconv_no = True
                        if blong >= bcfg.yes_post_min:
                            bconv_yes = True
                    bshort = state.windowed_break_count(cfg.scanner.win_short)
                    if bshort is not None and bshort >= 2:
                        bconv_no = False

                if bresult.ev_no >= bcfg.enter_margin and bconv_no:
                    break_signal = " [bold magenta]BK:NO[/bold magenta]"
                elif bresult.ev_yes >= bcfg.enter_margin and bconv_yes:
                    break_signal = " [bold blue]BK:YES[/bold blue]"

            # Deuce signal
            signal = "—"
            signal_style = ""
            if result.ev_no >= cfg.scanner.enter_margin and conv_no:
                signal = "NO·S1" if is_set1 else "NO"
                signal_style = "bold red"
            elif result.ev_yes >= cfg.scanner.enter_margin and conv_yes:
                signal = "YES·S1" if is_set1 else "YES"
                signal_style = "bold green"

            signal_str = f"[{signal_style}]{signal}[/{signal_style}]" if signal_style else signal
            signal_str += break_signal

            ev_yes_str = f"{result.ev_yes:+.1%}"
            ev_no_str = f"{result.ev_no:+.1%}"
            ev_combined = f"[green]{ev_yes_str}[/green]" if result.ev_yes > 0 else ev_yes_str
            ev_combined += " / "
            ev_combined += f"[green]{ev_no_str}[/green]" if result.ev_no > 0 else ev_no_str

            # Rate: show relevant phase rate
            if is_set1:
                rate_str = f"S1:{cum_rate:.0%}" if cum_rate is not None else "—"
            else:
                rate_str = f"W:{long_rate:.0%}" if long_rate is not None else "—"

            total_deuces = state.deuces_a + state.deuces_b
            deuce_str = f"{total_deuces}/{state.total_games}"
            d_est_str = f"{est.d_match:.0%}"

            hold_a_str = _format_hold(state, "A")
            hold_b_str = _format_hold(state, "B")

            status_parts = []
            if state.yes_state.halted:
                status_parts.append("dY:HALT")
            elif state.yes_state.loss_streak > 0:
                status_parts.append(f"dY:L{state.yes_state.loss_streak}")
            if state.no_state.halted:
                status_parts.append("dN:HALT")
            elif state.no_state.loss_streak > 0:
                status_parts.append(f"dN:L{state.no_state.loss_streak}")
            if state.break_yes_state.halted:
                status_parts.append("bY:HALT")
            elif state.break_yes_state.loss_streak > 0:
                status_parts.append(f"bY:L{state.break_yes_state.loss_streak}")
            if state.break_no_state.halted:
                status_parts.append("bN:HALT")
            elif state.break_no_state.loss_streak > 0:
                status_parts.append(f"bN:L{state.break_no_state.loss_streak}")
            if state.match_net_pnl != 0:
                status_parts.append(f"£{state.match_net_pnl:+.0f}")
            status_str = " ".join(status_parts) if status_parts else "—"

            match_label = f"{state.player_a} vs {state.player_b}"
            if has_alert:
                match_label = f"[bold yellow]* {match_label}[/bold yellow]"

            table.add_row(
                match_label,
                str(state.current_set),
                f"{state.total_games} ({est.games_a}A/{est.games_b}B)",
                deuce_str,
                hold_a_str,
                hold_b_str,
                serving,
                rate_str,
                d_est_str,
                f"{result.p_yes:.1%}",
                ev_combined,
                signal_str,
                status_str,
            )

        scanner.alert_match_ids.clear()

    console.print(table)
    console.print(
        f"[dim]Deuce: EV≥{cfg.scanner.enter_margin:.0%} | "
        f"S1: NO={cfg.scanner.no_set1_max:.0%} YES>{cfg.scanner.yes_set1_min:.0%} (≥{cfg.scanner.set1_min_games}g) | "
        f"Post: NO<{cfg.scanner.no_post_max:.0%} YES>{cfg.scanner.yes_post_min:.0%} (W{cfg.scanner.win_long}) | "
        f"Veto: ≥2d in {cfg.scanner.win_short}g[/dim]"
    )
    if cfg.break_market.enabled:
        bcfg = cfg.break_market
        console.print(
            f"[dim]Break: EV≥{bcfg.enter_margin:.0%} | "
            f"S1: NO={bcfg.no_set1_max:.0%} YES>{bcfg.yes_set1_min:.0%} | "
            f"Post: NO<{bcfg.no_post_max:.0%} YES>{bcfg.yes_post_min:.0%}[/dim]"
        )
    console.print(
        "[dim]Hold: L=love 15/30/40=returner max score D=deuce BK=broken | "
        "%=clean service games (held to ≤30)[/dim]"
    )


def _format_hold(state, server: str) -> str:
    """Compact hold quality string: 'L3 15:1 30:1 (75%)'."""
    q = state.hold_quality(server)
    total = sum(q.values())
    if total == 0:
        return "—"

    parts = []
    labels = [("love", "L"), ("15", "15"), ("30", "30"), ("40", "40"), ("deuce", "D"), ("broken", "BK")]
    for key, short in labels:
        if q[key] > 0:
            parts.append(f"{short}:{q[key]}")

    csp = state.clean_service_pct(server)
    csp_str = f" [bold green]{csp:.0%}[/bold green]" if csp is not None and csp >= 0.7 else f" {csp:.0%}" if csp is not None else ""

    return " ".join(parts) + csp_str
