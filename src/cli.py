"""CLI entry point for the live deuce scanner."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from .alerts.dispatcher import AlertDispatcher
from .core.config import load_config
from .live.scanner import LiveScanner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tennis Deuce-in-Next-Two-Games Live Scanner"
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="Path to YAML config file"
    )
    parser.add_argument(
        "--margin", type=float, default=None, help="Override EV safety margin"
    )
    parser.add_argument(
        "--api-key", type=str, default=None, help="API key for tennis data provider"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Show live dashboard table"
    )
    parser.add_argument(
        "--dashboard-interval", type=int, default=30,
        help="Dashboard refresh interval in seconds (default: 30)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    if args.margin is not None:
        config.scanner.margin = args.margin
    if args.api_key:
        config.api.api_key = args.api_key

    if not config.api.api_key:
        logging.error("No API key set. Use --api-key, config file, or TENNIS_API_KEY env var.")
        sys.exit(1)

    dispatcher = AlertDispatcher(config.alerts)
    scanner = LiveScanner(config, dispatcher)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown(sig: int, frame: object) -> None:
        logging.info("Shutting down...")
        scanner.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if args.dashboard:
        try:
            loop.run_until_complete(_run_with_dashboard(scanner, args.dashboard_interval))
        finally:
            loop.close()
    else:
        try:
            loop.run_until_complete(scanner.run())
        finally:
            loop.close()


async def _run_with_dashboard(scanner: LiveScanner, interval: int) -> None:
    from rich.console import Console
    from .live.dashboard import print_dashboard

    console = Console()
    scanner._running = True

    async def dashboard_loop() -> None:
        while scanner._running:
            console.clear()
            print_dashboard(scanner, console)
            await asyncio.sleep(interval)

    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        poll_task = asyncio.create_task(_poll_loop(scanner, client))
        dash_task = asyncio.create_task(dashboard_loop())
        await asyncio.gather(poll_task, dash_task)


async def _poll_loop(scanner: LiveScanner, client: "httpx.AsyncClient") -> None:
    while scanner._running:
        try:
            await scanner._poll(client)
        except Exception:
            logging.getLogger(__name__).exception("Poll cycle error")
        await asyncio.sleep(scanner.cfg.api.poll_interval_seconds)


if __name__ == "__main__":
    main()
