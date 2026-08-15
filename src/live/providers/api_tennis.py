"""api-tennis.com provider — existing behavior, extracted."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import LiveProvider

log = logging.getLogger(__name__)


class ApiTennisProvider(LiveProvider):
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def fetch_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "method": "get_livescore",
            "APIkey": self.api_key,
        }
        resp = await client.get(self.base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        success = data.get("success")
        if success not in (1, "1", True):
            log.warning("API returned success=%s (type=%s), keys=%s",
                        success, type(success).__name__, list(data.keys()))
            if isinstance(data.get("result"), list) and data["result"]:
                log.info("Result present despite success=%s, using it", success)
            else:
                return []
        error_msg = data.get("error")
        if error_msg:
            log.info("API error field: %s", error_msg)

        result = data.get("result", [])
        if isinstance(result, list):
            events = []
            for ev in result:
                if not isinstance(ev, dict):
                    continue
                if "event_key" not in ev:
                    log.info("Skipping non-event item: %s", ev)
                    continue
                events.append(ev)
                name = (ev.get("event_first_player", "") or ev.get("event_home_team", ""))
                name += " vs " + (ev.get("event_second_player", "") or ev.get("event_away_team", ""))
                log.info("  -> %s [%s] %s", name, ev.get("event_key", "?"), ev.get("event_status", ""))
            log.info("api-tennis: %d events (%d raw items)", len(events), len(result))
            return events
        return []

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw
