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
        if data.get("success") != 1:
            log.warning("API returned success=%s", data.get("success"))
            return []
        result = data.get("result", [])
        if isinstance(result, list):
            log.debug("api-tennis returned %d live events", len(result))
            return result
        return []

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw
