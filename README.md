# Tennis Deuce Scanner

Live scanner for the bet365 "deuce in next two games" in-play market. Monitors live tennis matches via API, estimates per-server deuce probabilities using Bayesian shrinkage, and alerts when EV clears a configurable safety margin.

See [BRIEF.md](BRIEF.md) for full strategy details.

## Quick Start

```bash
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Live scanner (requires API key)
deuce-scanner --api-key YOUR_KEY --margin 0.10

# Backtest (requires Sackmann CSV data)
pip install -e ".[backtest]"
deuce-backtest --data-dir ./tennis_atp --surface hard --year-from 2018
```

## Project Structure

```
src/
  core/
    math.py      # Deuce probability, EV, Kelly, odds conversion
    model.py     # Bayesian shrinkage estimator, match state
    config.py    # YAML config loader
  live/
    scanner.py   # Live polling loop, per-match state, EV evaluation
  backtest/
    runner.py    # Historical simulation using Sackmann CSVs
  alerts/
    dispatcher.py  # Console + Telegram alert routing
  cli.py         # CLI entry point
config/
  default.yaml   # Default configuration
tests/
  test_math.py   # 20 tests verifying formulae from BRIEF.md
  test_model.py  # 5 tests for estimation model
```

## Configuration

Copy `config/default.yaml` and edit, or use env vars:
- `TENNIS_API_KEY` — API key for tennis data provider
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — for Telegram alerts

## Key Parameters

| Parameter | Default | Description |
|---|---|---|
| `margin` | 0.10 | Min EV to trigger alert (10%) |
| `min_set` | 2 | Only alert from set 2 onward |
| `min_games_for_alert` | 8 | Min games before first alert |
| `alert_cooldown_seconds` | 300 | Debounce between alerts per match |
| `kelly_fraction` | 0.25 | Quarter-Kelly staking |
