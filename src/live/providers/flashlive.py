"""FlashLive Sports (RapidAPI) provider — broad Challenger/ITF coverage.

Requires a free RapidAPI key: https://rapidapi.com/tipsters/api/flashlive-sports
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .base import LiveProvider

log = logging.getLogger(__name__)

HOST = "flashlive-sports.p.rapidapi.com"
BASE = f"https://{HOST}"
TENNIS_SPORT_ID = "2"


class FlashLiveProvider(LiveProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": HOST,
        }

    async def fetch_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await client.get(
            f"{BASE}/v1/events/live",
            params={"sport_id": TENNIS_SPORT_ID, "locale": "en_INT"},
            headers=self._headers(),
        )
        resp.raise_for_status()
        data = resp.json()

        raw_events = []
        top = data.get("DATA", [])
        if isinstance(top, list):
            for item in top:
                if isinstance(item, dict):
                    events = item.get("EVENTS", [])
                    if isinstance(events, list):
                        for e in events:
                            e["_tournament_name"] = item.get("NAME", "")
                            e["_country_name"] = item.get("COUNTRY_NAME", "")
                            raw_events.append(e)
                    elif "EVENT_ID" in item or "HOME_NAME" in item:
                        raw_events.append(item)

        log.debug("FlashLive returned %d live tennis events", len(raw_events))

        normalized = []
        for e in raw_events:
            try:
                normalized.append(self.normalize(e))
            except Exception:
                log.debug("Failed to normalize FlashLive event %s",
                          e.get("EVENT_ID", e.get("id", "?")))
        return normalized

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert FlashLive event to api-tennis-shaped dict."""
        home = raw.get("HOME_PARTICIPANT_NAME_ONE", raw.get("HOME_NAME", ""))
        away = raw.get("AWAY_PARTICIPANT_NAME_ONE", raw.get("AWAY_NAME", ""))
        home_id = str(raw.get("HOME_PARTICIPANT_IDS", raw.get("HOME_ID", "")))
        away_id = str(raw.get("AWAY_PARTICIPANT_IDS", raw.get("AWAY_ID", "")))
        event_id = raw.get("EVENT_ID", raw.get("id", ""))

        scores = self._extract_scores(raw)

        serve = ""
        serving = raw.get("SERVING", raw.get("serving"))
        if serving == 1 or serving == "1":
            serve = "First Player"
        elif serving == 2 or serving == "2":
            serve = "Second Player"

        stage = raw.get("STAGE", raw.get("STATUS", ""))
        status_desc = str(raw.get("STAGE_TYPE", stage))
        if not status_desc or status_desc == "LIVE":
            current_set = len(scores) or 1
            status_desc = f"Set {current_set}"

        home_game = raw.get("HOME_SCORE_CURRENT_PART", raw.get("HOME_GAME_SCORE", ""))
        away_game = raw.get("AWAY_SCORE_CURRENT_PART", raw.get("AWAY_GAME_SCORE", ""))

        tournament = raw.get("_tournament_name", raw.get("TOURNAMENT_NAME", ""))
        category = raw.get("_country_name", raw.get("CATEGORY_NAME", ""))

        return {
            "event_key": f"fl_{event_id}",
            "event_first_player": home,
            "event_second_player": away,
            "first_player_key": home_id,
            "second_player_key": away_id,
            "event_status": status_desc,
            "event_live": "1",
            "event_serve": serve,
            "event_game_result": f"{home_game} - {away_game}",
            "scores": scores,
            "tournament_name": tournament,
            "league_name": f"{category} - {tournament}" if category else tournament,
            "statistics": [],
            "pointbypoint": [],
            "_flashlive_id": event_id,
            "_flashlive_raw": raw,
        }

    def _extract_scores(self, raw: dict[str, Any]) -> list[dict[str, str]]:
        """Pull set scores from FlashLive fields."""
        scores = []
        for i in range(1, 6):
            h = raw.get(f"HOME_SCORE_PART_{i}")
            a = raw.get(f"AWAY_SCORE_PART_{i}")
            if h is not None or a is not None:
                scores.append({
                    "score_first": str(h or 0),
                    "score_second": str(a or 0),
                    "score_set": str(i),
                })
        if not scores:
            result = raw.get("RESULT", raw.get("result"))
            if isinstance(result, list):
                for i, r in enumerate(result):
                    if isinstance(r, dict):
                        scores.append({
                            "score_first": str(r.get("home", r.get("HOME", 0))),
                            "score_second": str(r.get("away", r.get("AWAY", 0))),
                            "score_set": str(i + 1),
                        })
        return scores

    async def enrich_event(self, client: httpx.AsyncClient, event: dict[str, Any]) -> None:
        """Fetch statistics for a single event."""
        fl_id = event.get("_flashlive_id")
        if not fl_id:
            return

        await asyncio.sleep(0.3)

        try:
            resp = await client.get(
                f"{BASE}/v1/events/statistics",
                params={"event_id": fl_id, "locale": "en_INT"},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                stat_data = resp.json().get("DATA", [])
                event["statistics"] = _stats_to_api_format(
                    stat_data,
                    event.get("first_player_key", ""),
                    event.get("second_player_key", ""),
                )
        except Exception:
            log.debug("Failed to fetch statistics for %s", fl_id)

        await asyncio.sleep(0.3)

        try:
            resp = await client.get(
                f"{BASE}/v1/events/summary-incidents",
                params={"event_id": fl_id, "locale": "en_INT"},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                inc_data = resp.json().get("DATA", [])
                event["pointbypoint"] = _incidents_to_pbp(inc_data)
        except Exception:
            log.debug("Failed to fetch incidents for %s", fl_id)


def _stats_to_api_format(stat_stages: list, first_key: str, second_key: str) -> list:
    """Convert FlashLive statistics to api-tennis stat format."""
    result = []
    for stage in stat_stages:
        if not isinstance(stage, dict):
            continue
        period = stage.get("STAGE_NAME", "ALL")
        for group in stage.get("GROUPS", []):
            if not isinstance(group, dict):
                continue
            for item in group.get("ITEMS", []):
                if not isinstance(item, dict):
                    continue
                name = str(item.get("INCIDENT_NAME", "")).lower()
                if "serve points won" in name or "service points won" in name:
                    for pkey, val in [(first_key, item.get("VALUE_HOME", "")),
                                     (second_key, item.get("VALUE_AWAY", ""))]:
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


def _incidents_to_pbp(stages: list) -> list:
    """Convert FlashLive summary-incidents to game dicts."""
    games: list[dict] = []
    set_num = 0

    for stage in stages:
        if not isinstance(stage, dict):
            continue
        set_num += 1
        for item in stage.get("ITEMS", []):
            if not isinstance(item, dict):
                continue
            team = item.get("INCIDENT_TEAM", 0)
            server = "First Player" if team == 1 else "Second Player"
            games.append({
                "set_number": f"Set {set_num}",
                "number_game": str(len(games) + 1),
                "player_served": server,
                "points": [],
                "serve_winner": server,
            })

    return games
