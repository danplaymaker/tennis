"""Configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ScannerConfig:
    margin: float = 0.10
    min_games_for_alert: int = 8
    alert_cooldown_seconds: int = 300
    default_odds_yes: float = 1.6667
    default_odds_no: float = 1.6667
    win_long: int = 10
    win_short: int = 6
    enter_margin: float = 0.10
    exit_margin: float = 0.00
    loss_streak_halt: int = 3
    loss_taper: float = 0.5
    # v2: two-phase selection thresholds
    set1_min_games: int = 8
    no_set1_max: float = 0.00
    yes_set1_min: float = 0.50
    no_post_max: float = 0.10
    yes_post_min: float = 0.40
    d_floor: float = 0.08
    d_ceil: float = 0.42
    set1_stake_factor: float = 0.5


@dataclass
class BreakConfig:
    enabled: bool = True
    default_odds_yes: float = 1.6667
    default_odds_no: float = 1.6667
    enter_margin: float = 0.10
    exit_margin: float = 0.00
    # Conviction: break markets use inverse logic to deuce —
    # high break rate = YES conviction, low = NO conviction
    set1_min_games: int = 8
    no_set1_max: float = 0.00     # cumulative break rate for NO (no breaks → NO)
    yes_set1_min: float = 0.30    # cumulative break rate for YES
    no_post_max: float = 0.10     # windowed break rate for NO
    yes_post_min: float = 0.30    # windowed break rate for YES
    b_floor: float = 0.05
    b_ceil: float = 0.50
    loss_streak_halt: int = 3
    loss_taper: float = 0.5
    set1_stake_factor: float = 0.5


@dataclass
class APIConfig:
    provider: str = "api-tennis"
    base_url: str = "https://api.api-tennis.com/tennis/"
    api_key: str = ""
    poll_interval_seconds: int = 5


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class AlertConfig:
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    console_enabled: bool = True


@dataclass
class StakingConfig:
    kelly_fraction: float = 0.25
    max_stake_units: float = 3.0
    bankroll: float = 500.0
    min_stake: float = 2.0
    match_loss_cap: float = 20.0


@dataclass
class Config:
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    break_market: BreakConfig = field(default_factory=BreakConfig)
    api: APIConfig = field(default_factory=APIConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    staking: StakingConfig = field(default_factory=StakingConfig)


def load_config(path: str | Path | None = None) -> Config:
    if path is None:
        path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    path = Path(path)

    if not path.exists():
        return Config()

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    cfg = Config()

    if s := raw.get("scanner"):
        cfg.scanner = ScannerConfig(**{k: v for k, v in s.items() if v is not None})

    if bk := raw.get("break_market"):
        cfg.break_market = BreakConfig(**{k: v for k, v in bk.items() if v is not None})

    if a := raw.get("api"):
        key = a.get("api_key") or os.environ.get("TENNIS_API_KEY", "")
        cfg.api = APIConfig(
            provider=a.get("provider", "api-tennis"),
            base_url=a.get("base_url", cfg.api.base_url),
            api_key=key,
            poll_interval_seconds=a.get("poll_interval_seconds", 5),
        )

    if al := raw.get("alerts"):
        tg = al.get("telegram", {})
        cfg.alerts = AlertConfig(
            telegram=TelegramConfig(
                enabled=tg.get("enabled", False),
                bot_token=tg.get("bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN", ""),
                chat_id=tg.get("chat_id") or os.environ.get("TELEGRAM_CHAT_ID", ""),
            ),
            console_enabled=al.get("console", {}).get("enabled", True),
        )

    if st := raw.get("staking"):
        cfg.staking = StakingConfig(**{k: v for k, v in st.items() if v is not None})

    return cfg
