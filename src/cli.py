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

    try:
        loop.run_until_complete(scanner.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
