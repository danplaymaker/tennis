#!/usr/bin/env python3
"""Forward new Discord messages from one or more source channels to a destination channel.

Reads the source channel(s) live over the Discord gateway with a bot account and
reposts each new message through a webhook in the destination channel, so the
relayed message keeps the original author's display name and avatar.

Configuration is entirely through environment variables; see .env.example.
Run with:  python discord_forwarder.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import signal
import sys
from dataclasses import dataclass

import aiohttp
import discord

LOG = logging.getLogger("forwarder")

# Discord API limits.
MESSAGE_LIMIT = 2000
USERNAME_LIMIT = 80
EMBED_LIMIT = 10

# Trailing query string is allowed so a "?thread_id=..." webhook URL still works.
WEBHOOK_URL_RE = re.compile(
    r"^https://(?:\w+\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/(\d+)/([\w-]+)(?:\?\S*)?$"
)

# Discord rejects webhook usernames containing these substrings.
FORBIDDEN_NAME_PARTS = ("discord", "clyde", "everyone", "here")


class ConfigError(Exception):
    """Raised when the environment is missing or has an invalid setting."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name} must be a boolean (true/false), got {raw!r}")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass
class Config:
    token: str
    webhook_url: str
    source_channel_ids: set[int]
    forward_bots: bool = False
    relay_identity: bool = True
    show_source: bool = True
    forward_edits: bool = False
    forward_embeds: bool = True
    max_attachment_bytes: int = 8 * 1024 * 1024
    # Filled in at startup from the webhook metadata, used for loop protection.
    webhook_id: int = 0
    destination_channel_id: int = 0
    prefix: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
        if not token:
            raise ConfigError("DISCORD_BOT_TOKEN is required (bot token, not a user token)")

        webhook_url = os.environ.get("DESTINATION_WEBHOOK_URL", "").strip()
        if not webhook_url:
            raise ConfigError("DESTINATION_WEBHOOK_URL is required")
        match = WEBHOOK_URL_RE.match(webhook_url)
        if not match:
            raise ConfigError(
                "DESTINATION_WEBHOOK_URL does not look like a Discord webhook URL "
                "(expected https://discord.com/api/webhooks/<id>/<token>)"
            )

        raw_sources = os.environ.get("SOURCE_CHANNEL_IDS", "").strip()
        if not raw_sources:
            raise ConfigError("SOURCE_CHANNEL_IDS is required (comma-separated channel IDs)")
        source_ids: set[int] = set()
        for part in raw_sources.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                raise ConfigError(f"SOURCE_CHANNEL_IDS contains a non-numeric entry: {part!r}")
            source_ids.add(int(part))
        if not source_ids:
            raise ConfigError("SOURCE_CHANNEL_IDS did not contain any channel IDs")

        max_bytes = _env_int("MAX_ATTACHMENT_BYTES", 8 * 1024 * 1024)
        if max_bytes < 0:
            raise ConfigError("MAX_ATTACHMENT_BYTES must be >= 0")

        return cls(
            token=token,
            webhook_url=webhook_url,
            source_channel_ids=source_ids,
            forward_bots=_env_bool("FORWARD_BOTS", False),
            relay_identity=_env_bool("RELAY_IDENTITY", True),
            show_source=_env_bool("SHOW_SOURCE", len(source_ids) > 1),
            forward_edits=_env_bool("FORWARD_EDITS", False),
            forward_embeds=_env_bool("FORWARD_EMBEDS", True),
            max_attachment_bytes=max_bytes,
            webhook_id=int(match.group(1)),
            prefix=os.environ.get("MESSAGE_PREFIX", "").strip(),
        )


def sanitize_username(name: str) -> str:
    """Return a name Discord will accept as a webhook username.

    Discord rejects a handful of reserved substrings; a zero-width space after the
    first letter keeps the name readable while getting it past that check.
    """
    cleaned = name.strip() or "unknown"
    for part in FORBIDDEN_NAME_PARTS:
        cleaned = re.sub(
            re.escape(part),
            lambda match: match.group(0)[0] + "​" + match.group(0)[1:],
            cleaned,
            flags=re.IGNORECASE,
        )
    cleaned = cleaned[:USERNAME_LIMIT].strip()
    return cleaned or "unknown"


def chunk_content(content: str, limit: int = MESSAGE_LIMIT) -> list[str]:
    """Split content into Discord-sized pieces, preferring line then word boundaries."""
    if not content:
        return []
    if len(content) <= limit:
        return [content]

    chunks: list[str] = []
    remaining = content
    while len(remaining) > limit:
        window = remaining[:limit]
        split_at = window.rfind("\n")
        if split_at <= 0:
            split_at = window.rfind(" ")
        if split_at <= 0:
            split_at = limit
        chunk = remaining[:split_at].rstrip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].lstrip("\n ")
    if remaining:
        chunks.append(remaining)
    return chunks


def describe_channel(channel: discord.abc.Messageable) -> str:
    name = getattr(channel, "name", None)
    if name:
        return f"#{name}"
    return f"channel {getattr(channel, 'id', 'unknown')}"


def render_message(message: discord.Message, cfg: Config, *, edited: bool = False) -> str:
    """Build the text body for the relayed message."""
    header_bits: list[str] = []
    if cfg.prefix:
        header_bits.append(cfg.prefix)
    if cfg.show_source:
        guild = message.guild.name if message.guild else "DM"
        header_bits.append(f"[{guild} / {describe_channel(message.channel)}]")
    if not cfg.relay_identity:
        header_bits.append(f"**{message.author.display_name}**")
    if edited:
        header_bits.append("*(edited)*")

    lines: list[str] = []
    if header_bits:
        lines.append(" ".join(header_bits))

    reference = message.reference.resolved if message.reference else None
    if isinstance(reference, discord.Message):
        quoted = " ".join(reference.clean_content.split())
        if len(quoted) > 120:
            quoted = quoted[:117] + "..."
        if quoted:
            lines.append(f"> replying to **{reference.author.display_name}**: {quoted}")

    body = message.clean_content.strip()
    if body:
        lines.append(body)

    for sticker in message.stickers:
        lines.append(f"[sticker: {sticker.name}] {sticker.url}")

    lines.append(f"\n<{message.jump_url}>")
    return "\n".join(line for line in lines if line is not None).strip()


class Relay:
    """Posts messages to the destination webhook, one at a time, honouring rate limits."""

    def __init__(self, cfg: Config, session: aiohttp.ClientSession) -> None:
        self.cfg = cfg
        self.session = session
        self._lock = asyncio.Lock()

    async def fetch_metadata(self) -> dict:
        """Validate the webhook URL and learn which channel it posts into."""
        async with self.session.get(self.cfg.webhook_url) as resp:
            if resp.status == 401 or resp.status == 404:
                raise ConfigError(
                    "DESTINATION_WEBHOOK_URL was rejected by Discord "
                    f"(HTTP {resp.status}) - check that the webhook still exists"
                )
            resp.raise_for_status()
            return await resp.json()

    async def _post(self, payload: dict, files: list[tuple[str, bytes, str]] | None = None) -> None:
        """POST one webhook message, retrying on rate limits and transient failures."""
        attempt = 0
        while True:
            attempt += 1
            if files:
                form = aiohttp.FormData()
                form.add_field("payload_json", json.dumps(payload), content_type="application/json")
                for index, (filename, data, content_type) in enumerate(files):
                    form.add_field(
                        f"files[{index}]", data, filename=filename, content_type=content_type
                    )
                request = self.session.post(self.cfg.webhook_url, data=form)
            else:
                request = self.session.post(self.cfg.webhook_url, json=payload)

            async with request as resp:
                if resp.status == 429:
                    body = await resp.json(content_type=None) or {}
                    retry_after = float(body.get("retry_after", 1.0))
                    LOG.warning("Rate limited, retrying in %.2fs", retry_after)
                    await asyncio.sleep(retry_after + 0.1)
                    continue
                if resp.status >= 500 and attempt <= 5:
                    delay = min(2 ** attempt, 30)
                    LOG.warning("Discord returned %s, retrying in %ss", resp.status, delay)
                    await asyncio.sleep(delay)
                    continue
                if resp.status >= 400:
                    detail = await resp.text()
                    LOG.error("Webhook post failed (HTTP %s): %s", resp.status, detail[:500])
                    return
                return

    async def send(self, message: discord.Message, *, edited: bool = False) -> None:
        content = render_message(message, self.cfg, edited=edited)
        files, leftover_urls = await self._collect_attachments(message)
        if leftover_urls:
            content = "\n".join([content, *leftover_urls]).strip()

        embeds: list[dict] = []
        if self.cfg.forward_embeds:
            embeds = [
                embed.to_dict()
                for embed in message.embeds
                if embed.type == "rich"
            ][:EMBED_LIMIT]

        chunks = chunk_content(content) or [""]
        base: dict = {"allowed_mentions": {"parse": []}}
        if self.cfg.relay_identity:
            base["username"] = sanitize_username(message.author.display_name)
            base["avatar_url"] = message.author.display_avatar.url

        async with self._lock:
            for index, chunk in enumerate(chunks):
                is_last = index == len(chunks) - 1
                payload = dict(base)
                payload["content"] = chunk
                if is_last and embeds:
                    payload["embeds"] = embeds
                if is_last and files:
                    payload["attachments"] = [
                        {"id": i, "filename": name} for i, (name, _, _) in enumerate(files)
                    ]
                    await self._post(payload, files)
                elif chunk or (is_last and embeds):
                    await self._post(payload)

    async def _collect_attachments(
        self, message: discord.Message
    ) -> tuple[list[tuple[str, bytes, str]], list[str]]:
        """Re-upload small attachments; fall back to links for anything too large.

        Discord's own attachment URLs are signed and expire, so copying the bytes
        keeps the relayed message useful after that window.
        """
        files: list[tuple[str, bytes, str]] = []
        leftover: list[str] = []
        for attachment in message.attachments:
            if attachment.size > self.cfg.max_attachment_bytes:
                leftover.append(f"[attachment: {attachment.filename}] {attachment.url}")
                continue
            try:
                data = await attachment.read()
            except (discord.HTTPException, discord.NotFound) as exc:
                LOG.warning("Could not download %s: %s", attachment.filename, exc)
                leftover.append(f"[attachment: {attachment.filename}] {attachment.url}")
                continue
            files.append(
                (attachment.filename, data, attachment.content_type or "application/octet-stream")
            )
        return files, leftover


class ForwarderClient(discord.Client):
    def __init__(self, cfg: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.cfg = cfg
        self.relay: Relay | None = None
        self._session: aiohttp.ClientSession | None = None

    async def setup_hook(self) -> None:
        self._session = aiohttp.ClientSession()
        self.relay = Relay(self.cfg, self._session)
        metadata = await self.relay.fetch_metadata()
        self.cfg.destination_channel_id = int(metadata.get("channel_id", 0))
        if self.cfg.destination_channel_id in self.cfg.source_channel_ids:
            raise ConfigError(
                "The destination webhook posts into one of the SOURCE_CHANNEL_IDS, "
                "which would forward messages back into themselves. Use a different channel."
            )
        LOG.info(
            "Destination webhook %r resolved to channel %s",
            metadata.get("name", "webhook"),
            self.cfg.destination_channel_id,
        )

    async def close(self) -> None:
        await super().close()
        if self._session and not self._session.closed:
            await self._session.close()

    async def on_ready(self) -> None:
        LOG.info("Connected as %s (%s)", self.user, self.user.id if self.user else "?")
        for channel_id in sorted(self.cfg.source_channel_ids):
            channel = self.get_channel(channel_id)
            if channel is None:
                LOG.warning(
                    "Channel %s is not visible to this bot - invite it to that server "
                    "and give it View Channel + Read Message History",
                    channel_id,
                )
            else:
                LOG.info("Watching %s (%s)", describe_channel(channel), channel_id)

    def _should_forward(self, message: discord.Message) -> bool:
        if message.channel.id not in self.cfg.source_channel_ids:
            return False
        if message.channel.id == self.cfg.destination_channel_id:
            return False
        if message.webhook_id and int(message.webhook_id) == self.cfg.webhook_id:
            return False  # our own relayed message
        if self.user and message.author.id == self.user.id:
            return False
        if message.author.bot and not self.cfg.forward_bots:
            return False
        if message.type not in (discord.MessageType.default, discord.MessageType.reply):
            return False
        if not (message.content or message.attachments or message.embeds or message.stickers):
            return False
        return True

    async def on_message(self, message: discord.Message) -> None:
        if not self._should_forward(message):
            return
        assert self.relay is not None
        try:
            await self.relay.send(message)
        except Exception:
            LOG.exception("Failed to forward message %s", message.id)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not self.cfg.forward_edits:
            return
        if before.content == after.content:
            return
        if not self._should_forward(after):
            return
        assert self.relay is not None
        try:
            await self.relay.send(after, edited=True)
        except Exception:
            LOG.exception("Failed to forward edit of message %s", after.id)


def load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader so the script runs without extra dependencies."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ.setdefault(key, value)


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    load_dotenv()

    try:
        cfg = Config.from_env()
    except ConfigError as exc:
        LOG.error("Configuration error: %s", exc)
        return 2

    client = ForwarderClient(cfg)

    async def runner() -> int:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(client.close()))
            except NotImplementedError:  # Windows
                pass
        try:
            await client.start(cfg.token)
        except discord.LoginFailure:
            LOG.error("Discord rejected DISCORD_BOT_TOKEN - check the token is a bot token")
            return 2
        except discord.PrivilegedIntentsRequired:
            LOG.error(
                "This bot needs the MESSAGE CONTENT intent. Enable it under "
                "Bot > Privileged Gateway Intents in the Discord developer portal."
            )
            return 2
        except ConfigError as exc:
            LOG.error("Configuration error: %s", exc)
            return 2
        except (discord.HTTPException, aiohttp.ClientError) as exc:
            LOG.error("Could not reach Discord: %s", exc)
            return 1
        finally:
            if not client.is_closed():
                await client.close()
        return 0

    try:
        return asyncio.run(runner())
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
