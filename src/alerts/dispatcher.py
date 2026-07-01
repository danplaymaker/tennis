"""Alert dispatcher — routes alerts to configured channels."""

from __future__ import annotations

import logging
from typing import Any

from ..core.config import AlertConfig

log = logging.getLogger(__name__)


class AlertDispatcher:
    def __init__(self, config: AlertConfig) -> None:
        self.config = config
        self._backends: list[AlertBackend] = []
        if config.console_enabled:
            self._backends.append(ConsoleBackend())
        if config.telegram.enabled:
            self._backends.append(TelegramBackend(config.telegram.bot_token, config.telegram.chat_id))

    def send(self, **kwargs: Any) -> None:
        msg = format_alert(**kwargs)
        for backend in self._backends:
            try:
                backend.send(msg)
            except Exception:
                log.exception("Alert backend %s failed", type(backend).__name__)


class AlertBackend:
    def send(self, message: str) -> None:
        raise NotImplementedError


class ConsoleBackend(AlertBackend):
    def send(self, message: str) -> None:
        try:
            from rich.console import Console
            from rich.panel import Panel
            console = Console()
            console.print(Panel(message, title="[bold red]DEUCE ALERT[/bold red]", border_style="red"))
        except ImportError:
            print(f"\n{'='*60}\n  DEUCE ALERT\n{'='*60}\n{message}\n{'='*60}\n")


class TelegramBackend(AlertBackend):
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: str) -> None:
        import httpx
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        httpx.post(url, json={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"})


def format_alert(
    match: str,
    side: str,
    d_a: float,
    d_b: float,
    games_a: int,
    games_b: int,
    p_yes: float,
    ev: float,
    odds: float,
    stake: float,
    set_num: int,
    total_games: int,
    long_rate: float = 0.0,
    short_rate: float = 0.0,
    loss_streak: int = 0,
    **_: Any,
) -> str:
    taper_note = f" (taper: streak {loss_streak})" if loss_streak > 0 else ""
    return (
        f"Match: {match}\n"
        f"Set {set_num} | {total_games} games played\n"
        f"---\n"
        f"Side: {side} (deuce in next 2 games)\n"
        f"d_A: {d_a:.1%} ({games_a} service games)\n"
        f"d_B: {d_b:.1%} ({games_b} service games)\n"
        f"Window: {long_rate:.1%} (L10) / {short_rate:.1%} (S6)\n"
        f"P(YES): {p_yes:.1%}\n"
        f"Assumed odds: {odds:.4f}\n"
        f"EV: {ev:+.1%}\n"
        f"Suggested stake: £{stake:.2f}{taper_note}\n"
        f"---\n"
        f"Verify bet365 price before placing!"
    )
