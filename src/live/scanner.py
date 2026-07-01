"""Live match scanner — polls live data providers, maintains per-match state, triggers alerts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ..alerts.dispatcher import AlertDispatcher
from ..core.config import Config
from ..core.math import compute_ev, d_threshold_no, d_threshold_yes, kelly_stake
from ..core.model import MatchState, PendingBet, PlayerPrior
from .providers.base import LiveProvider

log = logging.getLogger(__name__)


def create_provider(config: Config) -> LiveProvider:
    """Factory: create the right provider from config."""
    from .providers.api_tennis import ApiTennisProvider
    return ApiTennisProvider(config.api.base_url, config.api.api_key)


class LiveScanner:
    def __init__(self, config: Config, dispatcher: AlertDispatcher,
                 provider: LiveProvider | None = None) -> None:
        self.cfg = config
        self.dispatcher = dispatcher
        self.provider = provider or create_provider(config)
        self.matches: dict[str, MatchState] = {}
        self.alert_match_ids: set[str] = set()
        self._running = False

    async def run(self) -> None:
        self._running = True
        log.info("Live scanner started (provider=%s, poll every %ds)",
                 type(self.provider).__name__, self.cfg.api.poll_interval_seconds)
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
        events = await self.provider.fetch_events(client)
        for event in events:
            match_id = str(event.get("event_key", ""))
            if not match_id:
                continue
            state = self.matches.get(match_id)
            if state is None:
                state = self._init_match(event)
                self.matches[match_id] = state
                log.info("Tracking: %s vs %s [%s]", state.player_a, state.player_b, match_id)
                print("\a", end="", flush=True)
            self._update_state(state, event)
            self._evaluate(state)
        self._prune_finished(events)

    def _init_match(self, event: dict[str, Any]) -> MatchState:
        home = _player_name(event, "first")
        away = _player_name(event, "second")

        first_key = str(event.get("first_player_key", ""))
        second_key = str(event.get("second_player_key", ""))

        spw_home, spw_away = _extract_spw_from_stats(
            event.get("statistics", []), first_key, second_key
        )
        if spw_home == 0.62 and spw_away == 0.62:
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

        games = _collapse_pbp_games(pbp)
        for game_key, game_data, is_tb in games:
            if game_key in state._seen_game_keys:
                continue
            if not _game_is_complete(game_data):
                continue

            state._seen_game_keys.add(game_key)
            served = str(game_data.get("player_served", "")).lower()
            server = "A" if "first" in served else "B"
            was_deuce = _game_had_deuce(game_data)
            state.record_game(server, was_deuce, is_tiebreak=is_tb)

    def _evaluate(self, state: MatchState) -> None:
        cfg = self.cfg

        settled = state.settle_pending_bets()
        for bet, won in settled:
            side_state = state.yes_state if bet.side == "YES" else state.no_state
            result_str = "WON" if won else "LOST"
            log.info("Settled %s %s: %s (streak=%d) [%s]",
                     bet.side, result_str, f"£{bet.stake:.2f}",
                     side_state.loss_streak, state.match_id)
            if side_state.loss_streak >= cfg.scanner.loss_streak_halt:
                side_state.halted = True
                log.info("Circuit breaker: %s halted for %s (streak=%d)",
                         bet.side, state.match_id, side_state.loss_streak)

        if state.current_set < cfg.scanner.min_set:
            return

        long_rate = state.windowed_deuce_rate(cfg.scanner.win_long)
        short_rate = state.windowed_deuce_rate(cfg.scanner.win_short)
        if long_rate is None or short_rate is None:
            return

        no_max = d_threshold_no(cfg.scanner.default_odds_no, cfg.scanner.enter_margin)
        yes_min = d_threshold_yes(cfg.scanner.default_odds_yes, cfg.scanner.enter_margin)

        window_side = None
        if long_rate <= no_max and short_rate <= no_max:
            window_side = "NO"
        elif long_rate >= yes_min and short_rate >= yes_min:
            window_side = "YES"

        est = state.estimate_deuce_rates()
        if state.next_server == "A":
            d_next, d_after = est.d_a, est.d_b
        else:
            d_next, d_after = est.d_b, est.d_a

        result = compute_ev(
            d_next, d_after,
            cfg.scanner.default_odds_yes,
            cfg.scanner.default_odds_no,
            0.0,
        )

        for check_side in ("YES", "NO"):
            side_state = state.yes_state if check_side == "YES" else state.no_state
            ev = result.ev_yes if check_side == "YES" else result.ev_no

            if side_state.hot and ev < cfg.scanner.exit_margin:
                side_state.hot = False
                side_state.armed = True

            if (window_side != check_side or
                    not side_state.armed or
                    side_state.halted or
                    ev < cfg.scanner.enter_margin):
                continue

            if -state.match_net_pnl >= cfg.staking.match_loss_cap:
                log.info("Match loss cap reached for %s (P&L=%.2f)",
                         state.match_id, state.match_net_pnl)
                continue

            odds = cfg.scanner.default_odds_yes if check_side == "YES" else cfg.scanner.default_odds_no
            b = odds - 1.0
            if b <= 0:
                continue
            p = (ev + 1.0) / odds
            full_kelly = (p * b - (1 - p)) / b
            taper = cfg.scanner.loss_taper ** side_state.loss_streak
            stake = cfg.staking.kelly_fraction * full_kelly * taper * cfg.staking.bankroll
            stake = min(stake, cfg.staking.max_stake_units * cfg.staking.bankroll / 100)

            if stake < cfg.staking.min_stake:
                continue

            side_state.armed = False
            side_state.hot = True
            state.match_total_staked += stake
            state.pending_bets.append(PendingBet(
                side=check_side,
                fired_at_game=state.total_games,
                odds=odds,
                stake=stake,
            ))

            self.alert_match_ids.add(state.match_id)

            self.dispatcher.send(
                match=f"{state.player_a} vs {state.player_b}",
                match_id=state.match_id,
                side=check_side,
                d_a=est.d_a,
                d_b=est.d_b,
                games_a=est.games_a,
                games_b=est.games_b,
                p_yes=result.p_yes,
                ev=ev,
                odds=odds,
                stake=stake,
                set_num=state.current_set,
                total_games=state.total_games,
                long_rate=long_rate,
                short_rate=short_rate,
                loss_streak=side_state.loss_streak,
            )

    def _prune_finished(self, live_events: list[dict[str, Any]]) -> None:
        live_ids = {str(e.get("event_key", "")) for e in live_events}
        finished = [mid for mid in self.matches if mid not in live_ids]
        for mid in finished:
            log.info("Match %s finished, removing state", mid)
            del self.matches[mid]


def _collapse_pbp_games(pbp: list) -> list:
    """Group flat pbp entries into logical games.

    Returns [(game_key, merged_game_data, is_tiebreak), ...].
    Tiebreak points sharing the same (set_number, number_game) are merged
    into a single game entry.  Entries without set/game numbers fall back
    to index-based keys.
    """
    from collections import OrderedDict

    groups: OrderedDict[str, dict] = OrderedDict()
    tb_keys: set[str] = set()

    for i, entry in enumerate(pbp):
        if not isinstance(entry, dict):
            continue

        set_num = str(entry.get("set_number", "")).strip()
        game_num = str(entry.get("number_game", "")).strip()

        if set_num and game_num:
            key = f"{set_num}:{game_num}"
        else:
            key = f"idx:{i}"

        is_tb = _is_tiebreak_entry(entry)

        if key not in groups:
            groups[key] = dict(entry)
            if is_tb:
                tb_keys.add(key)
        else:
            existing = groups[key]
            ep = existing.get("points", [])
            np_ = entry.get("points", [])
            if isinstance(ep, list) and isinstance(np_, list):
                existing["points"] = ep + np_
            for f in ("serve_winner", "serve_lost", "result", "player_served"):
                if not existing.get(f) and entry.get(f):
                    existing[f] = entry[f]
            if is_tb:
                tb_keys.add(key)

    result = []
    for key, data in groups.items():
        result.append((key, data, key in tb_keys))
    return result


def _is_tiebreak_entry(entry: dict[str, Any]) -> bool:
    """Detect tiebreak from game number or point scoring pattern."""
    num = str(entry.get("number_game", "")).lower().strip()
    if "tb" in num or "tie" in num:
        return True
    try:
        if int(num) >= 13:
            return True
    except ValueError:
        pass
    points = entry.get("points", [])
    if isinstance(points, list) and len(points) >= 2:
        for p in points[:3]:
            score = str(p.get("score", "") if isinstance(p, dict) else p).strip()
            parts = score.replace(" - ", "-").split("-")
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                try:
                    l, r = int(left), int(right)
                    if l + r >= 1 and l <= 7 and r <= 7 and left not in ("15", "30", "40"):
                        return True
                except ValueError:
                    pass
    return False


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


def _extract_spw_from_stats(
    statistics: Any, first_key: str, second_key: str
) -> tuple[float, float]:
    """Derive SPW from api-tennis statistics array."""
    if not isinstance(statistics, list) or not statistics:
        return 0.62, 0.62

    first_won = first_total = 0
    second_won = second_total = 0

    for stat in statistics:
        if not isinstance(stat, dict):
            continue
        name = str(stat.get("stat_name", "")).lower()
        pkey = str(stat.get("player_key", ""))
        period = str(stat.get("stat_period", "")).lower()

        if period not in ("", "all", "match", "total"):
            continue

        won = _safe_int(stat.get("stat_won", stat.get("stat_value", 0)))
        total = _safe_int(stat.get("stat_total", 0))

        if "service points won" in name or "serve points won" in name:
            if pkey == first_key:
                first_won, first_total = won, total
            elif pkey == second_key:
                second_won, second_total = won, total

    spw_first = first_won / first_total if first_total >= 10 else 0.62
    spw_second = second_won / second_total if second_total >= 10 else 0.62

    return spw_first, spw_second


def _extract_spw_from_pbp(pbp: Any) -> tuple[float, float]:
    """Derive SPW from point-by-point data (flat list of game dicts)."""
    if not isinstance(pbp, list) or not pbp:
        return 0.62, 0.62

    first_serve_pts = 0
    first_serve_won = 0
    second_serve_pts = 0
    second_serve_won = 0

    for game in pbp:
        if not isinstance(game, dict):
            continue
        if not _game_is_complete(game):
            continue

        served = str(game.get("player_served", "")).lower()
        is_first = "first" in served

        points = game.get("points", [])
        if not isinstance(points, list) or not points:
            continue

        n_points = len(points)
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
    """Count server points won by tracking score progression."""
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


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _detect_surface(event: dict[str, Any]) -> str:
    for field in ("league_name", "tournament_name"):
        name = str(event.get(field, "")).lower()
        if any(t in name for t in ("wimbledon", "halle", "queen", "s-hertogenbosch", "mallorca", "eastbourne", "stuttgart grass")):
            return "grass"
        if any(t in name for t in ("roland garros", "rome", "madrid", "barcelona", "monte carlo", "buenos aires", "rio", "hamburg", "lyon")):
            return "clay"
    return "hard"
