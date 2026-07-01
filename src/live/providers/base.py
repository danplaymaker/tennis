"""Base class for live data providers."""

from __future__ import annotations

from typing import Any

import httpx


class LiveProvider:
    """Abstract base for fetching live tennis events."""

    async def fetch_events(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        raise NotImplementedError

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert provider-specific format to the canonical event dict
        expected by LiveScanner (api-tennis shaped)."""
        raise NotImplementedError
