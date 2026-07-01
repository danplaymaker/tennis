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
            return result
        return []

    def _init_match(self, event: dict[str, Any]) -> MatchState:
        home = event.get("event_home_team", "Player A")
        away = event.get("event_away_team", "Player B")

        spw_home, spw_away = _extract_spw(event.get("statistics", []))

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

        service = event.get("event_service", "")
        if service == "home":
            state.next_server = "A"
        elif service == "away":
            state.next_server = "B"

        spw_home, spw_away = _extract_spw(event.get("statistics", []))
        if spw_home != 0.62:
            state.prior_a = PlayerPrior(spw=spw_home, rpw=1 - spw_away)
        if spw_away != 0.62:
            state.prior_b = PlayerPrior(spw=spw_away, rpw=1 - spw_home)

        pbp = event.get("pointbypoint", [])
        if not isinstance(pbp, list):
            return

        game_counter = 0
        for set_data in pbp:
            if not isinstance(set_data, dict):
                continue
            games = set_data.get("games", [])
            if not isinstance(games, list):
                continue
            for game_data in games:
                game_counter += 1
                if game_counter <= state.total_games:
                    continue
                if not _game_is_complete(game_data):
                    continue

                server = "A" if game_data.get("serve") == "home" else "B"
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


def _game_had_deuce(game_data: dict[str, Any]) -> bool:
    points = game_data.get("points", [])
    if isinstance(points, list):
        return any("40-40" in str(p) for p in points)
    if isinstance(points, str):
        return "40-40" in points
    return False


def _game_is_complete(game_data: dict[str, Any]) -> bool:
    if game_data.get("result"):
        return True
    points = game_data.get("points", [])
    if isinstance(points, list) and points:
        last = str(points[-1]).lower()
        return "game" in last or last == ""
    return False


def _current_set(event: dict[str, Any]) -> int:
    status = str(event.get("event_status", ""))
    if "set" in status.lower():
        for part in status.split():
            try:
                return int(part)
            except ValueError:
                continue

    scores = event.get("scores", {})
    if isinstance(scores, dict):
        set_keys = [k for k in scores if k != "game"]
        return len(set_keys)
    return 1


def _extract_spw(statistics: Any) -> tuple[float, float]:
    """Derive serve-point-won rate from api-tennis statistics array."""
    if not isinstance(statistics, list):
        return 0.62, 0.62

    first_pct_h = first_pct_a = 0.0
    first_won_h = first_won_a = 0.0
    second_won_h = second_won_a = 0.0

    for stat in statistics:
        if not isinstance(stat, dict):
            continue
        stype = str(stat.get("type", "")).lower()
        home = str(stat.get("home", "0"))
        away = str(stat.get("away", "0"))

        if "1st serve %" in stype and "won" not in stype:
            first_pct_h = _parse_pct(home)
            first_pct_a = _parse_pct(away)
        elif "1st serve won" in stype:
            first_won_h = _parse_pct(home)
            first_won_a = _parse_pct(away)
        elif "2nd serve won" in stype:
            second_won_h = _parse_pct(home)
            second_won_a = _parse_pct(away)

    if first_pct_h > 0 and first_won_h > 0:
        spw_h = first_pct_h * first_won_h + (1 - first_pct_h) * second_won_h
    else:
        spw_h = 0.62

    if first_pct_a > 0 and first_won_a > 0:
        spw_a = first_pct_a * first_won_a + (1 - first_pct_a) * second_won_a
    else:
        spw_a = 0.62

    return spw_h, spw_a


def _parse_pct(val: str) -> float:
    val = val.strip().rstrip("%")
    try:
        v = float(val)
        return v / 100 if v > 1 else v
    except (TypeError, ValueError):
        return 0.0


def _detect_surface(event: dict[str, Any]) -> str:
    league = str(event.get("league_name", "")).lower()
    if "wimbledon" in league or "halle" in league or "queen" in league or "s-hertogenbosch" in league:
        return "grass"
    if "roland garros" in league or "rome" in league or "madrid" in league or "barcelona" in league or "monte carlo" in league:
        return "clay"
    return "hard"
