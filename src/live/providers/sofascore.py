"""SofaScore unofficial API provider."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .base import LiveProvider

log = logging.getLogger(__name__)

BASE = "https://api.sofascore.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


class SofaScoreProvider(LiveProvider):
    def __init__(self) -> None:
        self._last_fetch = 0.0

    async def fetch_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await client.get(
            f"{BASE}/sport/tennis/events/live",
            headers=HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        log.debug("SofaScore returned %d live events", len(events))

        normalized = []
        for e in events:
            try:
                normalized.append(self.normalize(e))
            except Exception:
                log.debug("Failed to normalize event %s", e.get("id"))
        return normalized

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert SofaScore event to api-tennis-shaped dict."""
        home = raw.get("homeTeam", {})
        away = raw.get("awayTeam", {})
        hs = raw.get("homeScore", {})
        aws = raw.get("awayScore", {})
        tournament = raw.get("tournament", {})
        category = tournament.get("category", {})
        status = raw.get("status", {})

        scores = []
        for i in range(1, 6):
            pk = f"period{i}"
            if pk in hs or pk in aws:
                scores.append({
                    "score_first": str(hs.get(pk, 0)),
                    "score_second": str(aws.get(pk, 0)),
                    "score_set": str(i),
                })

        serve = ""
        serve_idx = raw.get("serveIndex")
        if serve_idx == 0:
            serve = "First Player"
        elif serve_idx == 1:
            serve = "Second Player"

        status_desc = status.get("description", "")
        if not status_desc and status.get("type") == "inprogress":
            current_set = len(scores) or 1
            status_desc = f"Set {current_set}"

        event = {
            "event_key": f"ss_{raw.get('id', '')}",
            "event_first_player": home.get("name", ""),
            "event_second_player": away.get("name", ""),
            "first_player_key": str(home.get("id", "")),
            "second_player_key": str(away.get("id", "")),
            "event_status": status_desc,
            "event_live": "1",
            "event_serve": serve,
            "event_game_result": f"{hs.get('point', '')} - {aws.get('point', '')}",
            "scores": scores,
            "tournament_name": tournament.get("name", ""),
            "league_name": f"{category.get('name', '')} - {tournament.get('name', '')}",
            "statistics": [],
            "pointbypoint": [],
            "_sofascore_id": raw.get("id"),
            "_sofascore_raw": raw,
        }
        return event

    async def enrich_event(self, client: httpx.AsyncClient, event: dict[str, Any]) -> None:
        """Fetch incidents + statistics for a single event (call sparingly)."""
        ss_id = event.get("_sofascore_id")
        if not ss_id:
            return

        await asyncio.sleep(0.5)

        try:
            resp = await client.get(
                f"{BASE}/event/{ss_id}/incidents",
                headers=HEADERS,
            )
            if resp.status_code == 200:
                incidents = resp.json().get("incidents", [])
                event["pointbypoint"] = _incidents_to_pbp(incidents)
        except Exception:
            log.debug("Failed to fetch incidents for %s", ss_id)

        await asyncio.sleep(0.5)

        try:
            resp = await client.get(
                f"{BASE}/event/{ss_id}/statistics",
                headers=HEADERS,
            )
            if resp.status_code == 200:
                event["statistics"] = _stats_to_api_format(
                    resp.json().get("statistics", []),
                    event.get("first_player_key", ""),
                    event.get("second_player_key", ""),
                )
        except Exception:
            log.debug("Failed to fetch statistics for %s", ss_id)


def _incidents_to_pbp(incidents: list) -> list:
    """Convert SofaScore incidents to flat game dicts (api-tennis pbp shape)."""
    games = []
    current_game: dict[str, Any] | None = None
    set_num = 1

    for inc in incidents:
        inc_type = inc.get("incidentType") or inc.get("type", "")

        if inc_type == "period":
            text = str(inc.get("text", "")).lower()
            if "set" in text:
                try:
                    set_num = int("".join(c for c in text if c.isdigit()) or set_num)
                except ValueError:
                    pass
            if "game" in text or text.startswith("game"):
                if current_game and current_game.get("points"):
                    games.append(current_game)
                game_num = inc.get("homeScore", 0) + inc.get("awayScore", 0) + 1 if "game" not in text else len(games) + 1
                is_home = inc.get("isHome", True)
                current_game = {
                    "set_number": f"Set {set_num}",
                    "number_game": str(len(games) + 1),
                    "player_served": "First Player" if is_home else "Second Player",
                    "points": [],
                }
            continue

        if inc_type == "point":
            if current_game is None:
                is_home = inc.get("isHome", True)
                current_game = {
                    "set_number": f"Set {set_num}",
                    "number_game": str(len(games) + 1),
                    "player_served": "First Player" if is_home else "Second Player",
                    "points": [],
                }

            home_pt = inc.get("homeScore", inc.get("homePoint", ""))
            away_pt = inc.get("awayScore", inc.get("awayPoint", ""))
            score = f"{home_pt} - {away_pt}"

            current_game["points"].append({"score": score})

            if str(home_pt).lower() == "game" or str(away_pt).lower() == "game":
                winner = inc.get("server") or ("First Player" if inc.get("isHome") else "Second Player")
                current_game["serve_winner"] = winner
                games.append(current_game)
                current_game = None

    if current_game and current_game.get("points"):
        games.append(current_game)

    return games


def _stats_to_api_format(
    stat_groups: list, first_key: str, second_key: str
) -> list:
    """Convert SofaScore statistics to api-tennis stat format."""
    result = []
    for group in stat_groups:
        period = group.get("period", "ALL")
        for g in group.get("groups", []):
            for item in g.get("statisticsItems", []):
                name = item.get("name", "")
                home_val = item.get("home", "")
                away_val = item.get("away", "")

                if "serve points won" in name.lower() or "service points won" in name.lower():
                    for pkey, val in [(first_key, home_val), (second_key, away_val)]:
                        parts = str(val).split("/")
                        if len(parts) == 2:
                            result.append({
                                "player_key": pkey,
                                "stat_name": "Service Points Won",
                                "stat_won": parts[0].strip(),
                                "stat_total": parts[1].strip(),
                                "stat_period": period,
                                "stat_type": "",
                                "stat_value": parts[0].strip(),
                            })
    return result
