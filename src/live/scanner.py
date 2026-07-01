"""Live match scanner — polls api-tennis.com, maintains per-match state, triggers alerts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ..alerts.dispatcher import AlertDispatcher
from ..core.config import Config
from ..core.math import compute_ev, kelly_stake
from ..core.model import MatchState, PlayerPrior

log = logging.getLogger(__name__)


class LiveScanner:
    def __init__(self, config: Config, dispatcher: AlertDispatcher) -> None:
        self.cfg = config
        self.dispatcher = dispatcher
        self.matches: dict[str, MatchState] = {}
        self._running = False

    async def run(self) -> None:
        self._running = True
        log.info("Live scanner started (poll every %ds)", self.cfg.api.poll_interval_seconds)
        async with httpx.AsyncClient(timeout=15) as client:
            while self._running:
                try:
                    await self._poll(client)
                except Exception:
                    log.exception("Poll cycle error")
                await asyncio.sleep(self.cfg.api.poll_interval_seconds)

    def stop(self) -> None:
        self._running = False

    async def _poll(self, client: httpx.AsyncClient) -> None:
        events = await self._fetch_live_events(client)
        for event in events:
            match_id = str(event.get("event_key", ""))
            if not match_id:
                continue
            state = self.matches.get(match_id)
            if state is None:
                state = self._init_match(event)
                self.matches[match_id] = state
                log.info("Tracking: %s vs %s [%s]", state.player_a, state.player_b, match_id)
            self._update_state(state, event)
            self._evaluate(state)
        self._prune_finished(events)

    async def _fetch_live_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "method": "get_events",
            "event_type": "live",
            "APIkey": self.cfg.api.api_key,
        }
        resp = await client.get(self.cfg.api.base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") != 1:
            log.warning("API returned success=%s", data.get("success"))
            return []
        result = data.get("result", [])
        if isinstance(result, list):
            log.debug("API returned %d live events", len(result))
            return result
        log.debug("API result is not a list: %s", type(result).__name__)
        return []

    def _init_match(self, event: dict[str, Any]) -> MatchState:
        home = _player_name(event, "first")
        away = _player_name(event, "second")

        spw_home, spw_away = _extract_spw_from_pbp(event.get("pointbypoint", []))

        return MatchState(
            match_id=str(event.get("event_key", "")),
            player_a=home,
            player_b=away,
            prior_a=PlayerPrior(spw=spw_home, rpw=1 - spw_away),
            prior_b=PlayerPrior(spw=spw_away, rpw=1 - spw_home),
            surface=_detect_surface(event),
        )

    def _update_state(self, state: MatchState, event: dict[str, Any]) -> None:
        state.current_set = _current_set(event)

        service = event.get("event_serve", "")
        if "first" in str(service).lower():
            state.next_server = "A"
        elif "second" in str(service).lower():
            state.next_server = "B"

        pbp = event.get("pointbypoint", [])
        if not isinstance(pbp, list):
            return

        game_counter = 0
        for set_data in pbp:
            if not isinstance(set_data, dict):
                continue
            games = set_data.get("games", [])
            if not isinstance(games, list):
                games = []
            for game_data in games:
                if not isinstance(game_data, dict):
                    continue
                game_counter += 1
                if game_counter <= state.total_games:
                    continue
                if not _game_is_complete(game_data):
                    continue

                served = str(game_data.get("player_served", "")).lower()
                server = "A" if "first" in served else "B"
                was_deuce = _game_had_deuce(game_data)
                state.record_game(server, was_deuce)

    def _evaluate(self, state: MatchState) -> None:
        if state.current_set < self.cfg.scanner.min_set:
            return
        if state.total_games < self.cfg.scanner.min_games_for_alert:
            return
        if state.total_games - state.last_alert_game < 2:
            return

        est = state.estimate_deuce_rates()

        if state.next_server == "A":
            d_next, d_after = est.d_a, est.d_b
        else:
            d_next, d_after = est.d_b, est.d_a

        result = compute_ev(
            d_next,
            d_after,
            self.cfg.scanner.default_odds_yes,
            self.cfg.scanner.default_odds_no,
            self.cfg.scanner.margin,
        )

        if result.side is None:
            return

        odds = (
            self.cfg.scanner.default_odds_yes
            if result.side == "YES"
            else self.cfg.scanner.default_odds_no
        )
        stake = kelly_stake(
            result.margin_cleared,
            odds,
            self.cfg.staking.kelly_fraction,
            self.cfg.staking.bankroll,
            self.cfg.staking.max_stake_units,
        )

        state.last_alert_game = state.total_games

        self.dispatcher.send(
            match=f"{state.player_a} vs {state.player_b}",
            match_id=state.match_id,
            side=result.side,
            d_a=est.d_a,
            d_b=est.d_b,
            games_a=est.games_a,
            games_b=est.games_b,
            p_yes=result.p_yes,
            ev=result.margin_cleared,
            odds=odds,
            stake=stake,
            set_num=state.current_set,
            total_games=state.total_games,
        )

    def _prune_finished(self, live_events: list[dict[str, Any]]) -> None:
        live_ids = {str(e.get("event_key", "")) for e in live_events}
        finished = [mid for mid in self.matches if mid not in live_ids]
        for mid in finished:
            log.info("Match %s finished, removing state", mid)
            del self.matches[mid]


def _player_name(event: dict[str, Any], which: str) -> str:
    """Extract player name, trying both naming conventions."""
    return (
        event.get(f"event_{which}_player")
        or event.get(f"event_{'home' if which == 'first' else 'away'}_team")
        or f"Player {'A' if which == 'first' else 'B'}"
    )


def _game_had_deuce(game_data: dict[str, Any]) -> bool:
    """Check if a completed game reached deuce (40-40)."""
    points = game_data.get("points", [])
    if isinstance(points, list):
        for p in points:
            score = str(p.get("score", "") if isinstance(p, dict) else p)
            if "40 - 40" in score or "40-40" in score or "deuce" in score.lower():
                return True
    if isinstance(points, str):
        return "40 - 40" in points or "40-40" in points
    return False


def _game_is_complete(game_data: dict[str, Any]) -> bool:
    """A game is complete if it has a serve_winner or result."""
    if game_data.get("serve_winner"):
        return True
    if game_data.get("serve_lost"):
        return True
    if game_data.get("result"):
        return True
    points = game_data.get("points", [])
    if isinstance(points, list) and points:
        last = points[-1]
        last_str = str(last.get("score", "") if isinstance(last, dict) else last).lower()
        return "game" in last_str
    return False


def _current_set(event: dict[str, Any]) -> int:
    status = str(event.get("event_status", ""))
    if "set" in status.lower():
        for part in status.split():
            try:
                return int(part)
            except ValueError:
                continue

    scores = event.get("scores", [])
    if isinstance(scores, list):
        return len(scores) + (1 if event.get("event_live") == "1" else 0)
    if isinstance(scores, dict):
        set_keys = [k for k in scores if k != "game"]
        return len(set_keys)
    return 1


def _extract_spw_from_pbp(pbp: Any) -> tuple[float, float]:
    """Derive serve-point-won rates from point-by-point data.

    Counts points won on serve for each player across all completed games.
    Falls back to defaults if insufficient data.
    """
    if not isinstance(pbp, list) or not pbp:
        return 0.62, 0.62

    first_serve_pts = 0
    first_serve_won = 0
    second_serve_pts = 0
    second_serve_won = 0

    for set_data in pbp:
        if not isinstance(set_data, dict):
            continue
        games = set_data.get("games", [])
        if not isinstance(games, list):
            continue
        for game in games:
            if not isinstance(game, dict):
                continue
            if not _game_is_complete(game):
                continue

            served = str(game.get("player_served", "")).lower()
            is_first = "first" in served
            winner = str(game.get("serve_winner", "") or "").lower()
            held = bool(winner)

            points = game.get("points", [])
            if not isinstance(points, list):
                continue

            n_points = len(points)
            if n_points == 0:
                continue

            if is_first:
                first_serve_pts += n_points
                first_serve_won += _count_server_points_won(points, is_first_server=True)
            else:
                second_serve_pts += n_points
                second_serve_won += _count_server_points_won(points, is_first_server=False)

    spw_first = first_serve_won / first_serve_pts if first_serve_pts >= 10 else 0.62
    spw_second = second_serve_won / second_serve_pts if second_serve_pts >= 10 else 0.62

    return spw_first, spw_second


def _count_server_points_won(points: list, is_first_server: bool) -> int:
    """Count how many points the server won by tracking score progression."""
    won = 0
    prev_server_score = 0
    score_map = {"0": 0, "15": 1, "30": 2, "40": 3, "ad": 4, "game": 99}

    for p in points:
        score_str = str(p.get("score", "") if isinstance(p, dict) else p).lower().strip()

        if "game" in score_str:
            won += 1
            continue

        parts = score_str.replace(" - ", "-").split("-")
        if len(parts) != 2:
            continue

        left = parts[0].strip()
        right = parts[1].strip()

        if is_first_server:
            cur = score_map.get(left, -1)
        else:
            cur = score_map.get(right, -1)

        if cur > prev_server_score:
            won += 1
        prev_server_score = max(cur, 0)

    return won


def _parse_pct(val: str) -> float:
    val = val.strip().rstrip("%")
    try:
        v = float(val)
        return v / 100 if v > 1 else v
    except (TypeError, ValueError):
        return 0.0


def _detect_surface(event: dict[str, Any]) -> str:
    for field in ("league_name", "tournament_name"):
        name = str(event.get(field, "")).lower()
        if any(t in name for t in ("wimbledon", "halle", "queen", "s-hertogenbosch", "mallorca", "eastbourne", "stuttgart grass")):
            return "grass"
        if any(t in name for t in ("roland garros", "rome", "madrid", "barcelona", "monte carlo", "buenos aires", "rio", "hamburg", "lyon")):
            return "clay"
    return "hard"
