"""Live match scanner — polls API, maintains per-match state, triggers alerts."""

from __future__ import annotations

import asyncio
import logging
import time
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
            match_id = str(event.get("id", ""))
            if not match_id:
                continue
            state = self.matches.get(match_id)
            if state is None:
                state = self._init_match(event)
                self.matches[match_id] = state
            self._update_state(state, event)
            self._evaluate(state)
        self._prune_finished(events)

    async def _fetch_live_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        params: dict[str, str] = {"method": "get_events", "event_type": "live"}
        if self.cfg.api.api_key:
            params["APIkey"] = self.cfg.api.api_key

        resp = await client.get(self.cfg.api.base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("result", [])
        if isinstance(result, list):
            return result
        return []

    def _init_match(self, event: dict[str, Any]) -> MatchState:
        home = event.get("event_home_team", "Player A")
        away = event.get("event_away_team", "Player B")

        home_stats = event.get("home_stats", {})
        away_stats = event.get("away_stats", {})

        return MatchState(
            match_id=str(event.get("id", "")),
            player_a=home,
            player_b=away,
            prior_a=PlayerPrior(
                spw=_pct(home_stats.get("spw", 62)),
                rpw=_pct(home_stats.get("rpw", 38)),
            ),
            prior_b=PlayerPrior(
                spw=_pct(away_stats.get("spw", 62)),
                rpw=_pct(away_stats.get("rpw", 38)),
            ),
            surface=event.get("surface", "hard").lower(),
        )

    def _update_state(self, state: MatchState, event: dict[str, Any]) -> None:
        scores = event.get("scores", {})
        set_num = _count_sets(scores)
        state.current_set = max(state.current_set, set_num)

        timeline = event.get("timeline", event.get("pointbypoint", []))
        if not isinstance(timeline, list):
            return

        for point in timeline:
            game_num = point.get("game", 0)
            if game_num <= state.total_games:
                continue

            server = "A" if point.get("server", "home") == "home" else "B"
            score_text = str(point.get("score", ""))
            was_deuce = "40-40" in score_text or "deuce" in score_text.lower()

            if point.get("game_complete", False) or point.get("result"):
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
        live_ids = {str(e.get("id", "")) for e in live_events}
        finished = [mid for mid in self.matches if mid not in live_ids]
        for mid in finished:
            log.info("Match %s finished, removing state", mid)
            del self.matches[mid]


def _pct(val: Any) -> float:
    try:
        v = float(val)
        return v / 100 if v > 1 else v
    except (TypeError, ValueError):
        return 0.62


def _count_sets(scores: Any) -> int:
    if isinstance(scores, dict):
        return len(scores)
    if isinstance(scores, list):
        return len(scores)
    return 1
