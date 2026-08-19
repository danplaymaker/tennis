#!/usr/bin/env python3
"""Forward new Discord messages from one or more source channels to a destination channel.

Reads the source channel(s) live over the Discord gateway and reposts each new
message through a webhook in the destination channel, so the relayed message
keeps the original author's display name and avatar.

Works with either a user token (ACCOUNT_TYPE=user) or a bot token
(ACCOUNT_TYPE=bot). The gateway protocol is implemented directly on aiohttp
rather than through discord.py, which refuses user tokens outright.

Configuration is entirely through environment variables; see .env.example.
Run with:  python discord_forwarder.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import random
import re
import signal
import sys
from dataclasses import dataclass

import aiohttp

LOG = logging.getLogger("forwarder")

API_BASE = "https://discord.com/api/v10"
CDN_BASE = "https://cdn.discordapp.com"

# Discord API limits.
MESSAGE_LIMIT = 2000
USERNAME_LIMIT = 80
EMBED_LIMIT = 10

# Gateway opcodes.
OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_RESUME = 6
OP_RECONNECT = 7
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

# Close codes that will never succeed on retry, so we exit instead of looping.
FATAL_CLOSE_CODES = {
    4004: "authentication failed - the token is wrong, expired, or was reset",
    4010: "invalid shard",
    4011: "sharding required",
    4012: "invalid API version",
    4013: "invalid gateway intents",
    4014: "disallowed gateway intents - enable the Message Content intent for this bot",
}

# GUILDS | GUILD_MESSAGES | DIRECT_MESSAGES | MESSAGE_CONTENT
BOT_INTENTS = 1 | 512 | 4096 | 32768

# Message types we relay; everything else is a join/pin/system notice.
RELAYABLE_TYPES = {0, 19}

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Trailing query string is allowed so a "?thread_id=..." webhook URL still works.
WEBHOOK_URL_RE = re.compile(
    r"^https://(?:\w+\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/(\d+)/([\w-]+)(?:\?\S*)?$"
)

# Discord rejects webhook usernames containing these substrings.
FORBIDDEN_NAME_PARTS = ("discord", "clyde", "everyone", "here")

USER_MENTION_RE = re.compile(r"<@!?(\d+)>")


class ConfigError(Exception):
    """Raised when the environment is missing or has an invalid setting."""


class FatalGatewayError(Exception):
    """Raised when the gateway rejects us in a way retrying cannot fix."""


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
    account_type: str = "user"
    forward_bots: bool = False
    forward_own: bool = False
    relay_identity: bool = True
    show_source: bool = True
    forward_edits: bool = False
    forward_embeds: bool = True
    max_attachment_bytes: int = 8 * 1024 * 1024
    prefix: str = ""
    # Filled in at startup from the webhook metadata, used for loop protection.
    webhook_id: int = 0
    destination_channel_id: int = 0

    @property
    def is_user_account(self) -> bool:
        return self.account_type == "user"

    @property
    def auth_header(self) -> str:
        """User tokens are sent raw; bot tokens carry the 'Bot ' prefix."""
        return self.token if self.is_user_account else f"Bot {self.token}"

    @classmethod
    def from_env(cls) -> "Config":
        account_type = os.environ.get("ACCOUNT_TYPE", "user").strip().lower() or "user"
        if account_type not in ("user", "bot"):
            raise ConfigError(f"ACCOUNT_TYPE must be 'user' or 'bot', got {account_type!r}")

        token = os.environ.get("DISCORD_TOKEN", "").strip()
        if not token:
            raise ConfigError("DISCORD_TOKEN is required")
        if token.lower().startswith("bot "):
            raise ConfigError(
                "DISCORD_TOKEN should not include the 'Bot ' prefix; "
                "set ACCOUNT_TYPE=bot instead"
            )

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
            account_type=account_type,
            forward_bots=_env_bool("FORWARD_BOTS", False),
            forward_own=_env_bool("FORWARD_OWN", False),
            relay_identity=_env_bool("RELAY_IDENTITY", True),
            show_source=_env_bool("SHOW_SOURCE", len(source_ids) > 1),
            forward_edits=_env_bool("FORWARD_EDITS", False),
            forward_embeds=_env_bool("FORWARD_EMBEDS", True),
            max_attachment_bytes=max_bytes,
            prefix=os.environ.get("MESSAGE_PREFIX", "").strip(),
            webhook_id=int(match.group(1)),
        )


def super_properties() -> dict:
    """The client fingerprint a real Discord web client sends on IDENTIFY."""
    return {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": BROWSER_UA,
        "browser_version": "120.0.0.0",
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": 260000,
        "client_event_source": None,
    }


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


def display_name(author: dict) -> str:
    return author.get("global_name") or author.get("username") or "unknown"


def avatar_url(author: dict) -> str:
    """Build a CDN URL for the author's avatar, falling back to Discord's default set."""
    user_id = author.get("id", "0")
    avatar = author.get("avatar")
    if avatar:
        ext = "gif" if str(avatar).startswith("a_") else "png"
        return f"{CDN_BASE}/avatars/{user_id}/{avatar}.{ext}?size=128"
    try:
        index = (int(user_id) >> 22) % 6
    except (TypeError, ValueError):
        index = 0
    return f"{CDN_BASE}/embed/avatars/{index}.png"


def jump_url(message: dict) -> str:
    guild = message.get("guild_id") or "@me"
    return f"https://discord.com/channels/{guild}/{message.get('channel_id')}/{message.get('id')}"


def clean_content(message: dict) -> str:
    """Replace raw user-mention markup with readable @names."""
    content = message.get("content") or ""
    if not content:
        return ""
    names = {
        str(user.get("id")): display_name(user)
        for user in message.get("mentions") or []
        if isinstance(user, dict)
    }
    return USER_MENTION_RE.sub(
        lambda match: "@" + names.get(match.group(1), "unknown"), content
    )


class DiscordHTTP:
    """Small REST helper: webhook posting plus the lookups used for labelling."""

    def __init__(self, cfg: Config, session: aiohttp.ClientSession) -> None:
        self.cfg = cfg
        self.session = session
        self._channel_names: dict[int, str] = {}
        self._guild_names: dict[int, str] = {}

    def _api_headers(self) -> dict:
        headers = {"Authorization": self.cfg.auth_header, "User-Agent": BROWSER_UA}
        if self.cfg.is_user_account:
            headers["X-Super-Properties"] = base64.b64encode(
                json.dumps(super_properties()).encode()
            ).decode()
        return headers

    async def fetch_webhook_metadata(self) -> dict:
        """Validate the webhook URL and learn which channel it posts into."""
        async with self.session.get(self.cfg.webhook_url) as resp:
            if resp.status in (401, 404):
                raise ConfigError(
                    "DESTINATION_WEBHOOK_URL was rejected by Discord "
                    f"(HTTP {resp.status}) - check that the webhook still exists"
                )
            resp.raise_for_status()
            return await resp.json()

    async def verify_token(self) -> dict:
        """Confirm the token works and return the account it belongs to."""
        async with self.session.get(
            f"{API_BASE}/users/@me", headers=self._api_headers()
        ) as resp:
            if resp.status == 401:
                raise ConfigError(
                    "Discord rejected DISCORD_TOKEN (HTTP 401). For a user account the "
                    "token is invalidated whenever you change your password or log out, "
                    "so it may simply need re-copying."
                )
            if resp.status == 403:
                body = await resp.text()
                raise ConfigError(f"Discord refused the token request (HTTP 403): {body[:300]}")
            resp.raise_for_status()
            return await resp.json()

    async def channel_label(self, channel_id: int) -> str:
        if channel_id in self._channel_names:
            return self._channel_names[channel_id]
        label = f"channel {channel_id}"
        try:
            async with self.session.get(
                f"{API_BASE}/channels/{channel_id}", headers=self._api_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("name"):
                        label = f"#{data['name']}"
        except aiohttp.ClientError as exc:
            LOG.debug("Could not look up channel %s: %s", channel_id, exc)
        self._channel_names[channel_id] = label
        return label

    async def guild_label(self, guild_id: int | None) -> str:
        if not guild_id:
            return "DM"
        if guild_id in self._guild_names:
            return self._guild_names[guild_id]
        label = f"guild {guild_id}"
        try:
            async with self.session.get(
                f"{API_BASE}/guilds/{guild_id}", headers=self._api_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("name"):
                        label = data["name"]
        except aiohttp.ClientError as exc:
            LOG.debug("Could not look up guild %s: %s", guild_id, exc)
        self._guild_names[guild_id] = label
        return label

    async def post_webhook(
        self, payload: dict, files: list[tuple[str, bytes, str]] | None = None
    ) -> None:
        """POST one webhook message, retrying on rate limits and transient failures."""
        attempt = 0
        while True:
            attempt += 1
            if files:
                form = aiohttp.FormData()
                form.add_field(
                    "payload_json", json.dumps(payload), content_type="application/json"
                )
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
                    delay = min(2**attempt, 30)
                    LOG.warning("Discord returned %s, retrying in %ss", resp.status, delay)
                    await asyncio.sleep(delay)
                    continue
                if resp.status >= 400:
                    detail = await resp.text()
                    LOG.error("Webhook post failed (HTTP %s): %s", resp.status, detail[:500])
                    return
                return

    async def download(self, url: str) -> bytes | None:
        """Fetch an attachment from the CDN. No auth header - these URLs are pre-signed."""
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    LOG.warning("Attachment download failed (HTTP %s)", resp.status)
                    return None
                return await resp.read()
        except aiohttp.ClientError as exc:
            LOG.warning("Attachment download failed: %s", exc)
            return None


class Relay:
    """Turns raw MESSAGE_CREATE payloads into webhook posts."""

    def __init__(self, cfg: Config, http: DiscordHTTP) -> None:
        self.cfg = cfg
        self.http = http
        self._lock = asyncio.Lock()

    async def render(self, message: dict, *, edited: bool = False) -> str:
        header_bits: list[str] = []
        if self.cfg.prefix:
            header_bits.append(self.cfg.prefix)
        if self.cfg.show_source:
            guild_id = message.get("guild_id")
            guild = await self.http.guild_label(int(guild_id) if guild_id else None)
            channel = await self.http.channel_label(int(message["channel_id"]))
            header_bits.append(f"[{guild} / {channel}]")
        if not self.cfg.relay_identity:
            header_bits.append(f"**{display_name(message.get('author') or {})}**")
        if edited:
            header_bits.append("*(edited)*")

        lines: list[str] = []
        if header_bits:
            lines.append(" ".join(header_bits))

        reference = message.get("referenced_message")
        if isinstance(reference, dict):
            quoted = " ".join(clean_content(reference).split())
            if len(quoted) > 120:
                quoted = quoted[:117] + "..."
            if quoted:
                author = display_name(reference.get("author") or {})
                lines.append(f"> replying to **{author}**: {quoted}")

        body = clean_content(message).strip()
        if body:
            lines.append(body)

        for sticker in message.get("sticker_items") or []:
            name = sticker.get("name", "sticker")
            lines.append(f"[sticker: {name}] {CDN_BASE}/stickers/{sticker.get('id')}.png")

        lines.append(f"\n<{jump_url(message)}>")
        return "\n".join(lines).strip()

    async def _collect_attachments(
        self, message: dict
    ) -> tuple[list[tuple[str, bytes, str]], list[str]]:
        """Re-upload small attachments; fall back to links for anything too large.

        Discord's own attachment URLs are signed and expire, so copying the bytes
        keeps the relayed message useful after that window.
        """
        files: list[tuple[str, bytes, str]] = []
        leftover: list[str] = []
        for attachment in message.get("attachments") or []:
            filename = attachment.get("filename", "file")
            url = attachment.get("url", "")
            size = attachment.get("size", 0)
            if not url:
                continue
            if size > self.cfg.max_attachment_bytes:
                leftover.append(f"[attachment: {filename}] {url}")
                continue
            data = await self.http.download(url)
            if data is None:
                leftover.append(f"[attachment: {filename}] {url}")
                continue
            files.append(
                (filename, data, attachment.get("content_type") or "application/octet-stream")
            )
        return files, leftover

    async def send(self, message: dict, *, edited: bool = False) -> None:
        content = await self.render(message, edited=edited)
        files, leftover_urls = await self._collect_attachments(message)
        if leftover_urls:
            content = "\n".join([content, *leftover_urls]).strip()

        embeds: list[dict] = []
        if self.cfg.forward_embeds:
            embeds = [
                embed
                for embed in (message.get("embeds") or [])
                if embed.get("type") == "rich"
            ][:EMBED_LIMIT]

        chunks = chunk_content(content) or [""]
        author = message.get("author") or {}
        base: dict = {"allowed_mentions": {"parse": []}}
        if self.cfg.relay_identity:
            base["username"] = sanitize_username(display_name(author))
            base["avatar_url"] = avatar_url(author)

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
                    await self.http.post_webhook(payload, files)
                elif chunk or (is_last and embeds):
                    await self.http.post_webhook(payload)


class GatewayClient:
    """Maintains the websocket connection and dispatches message events."""

    def __init__(self, cfg: Config, http: DiscordHTTP, relay: Relay) -> None:
        self.cfg = cfg
        self.http = http
        self.relay = relay
        self.user_id: int | None = None
        self._seq: int | None = None
        self._session_id: str | None = None
        self._resume_url: str | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._ack = True
        self._heartbeat_task: asyncio.Task | None = None
        self._closing = False

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.http.session

    async def close(self) -> None:
        self._closing = True
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()

    async def _gateway_url(self) -> str:
        if self._resume_url:
            return f"{self._resume_url}/?v=10&encoding=json"
        try:
            async with self.session.get(f"{API_BASE}/gateway") as resp:
                resp.raise_for_status()
                data = await resp.json()
                return f"{data['url']}/?v=10&encoding=json"
        except aiohttp.ClientError as exc:
            LOG.warning("Could not fetch gateway URL (%s), using the default", exc)
            return "wss://gateway.discord.gg/?v=10&encoding=json"

    def _identify_payload(self) -> dict:
        if self.cfg.is_user_account:
            # A user account must look like a client: no intents, browser fingerprint.
            return {
                "op": OP_IDENTIFY,
                "d": {
                    "token": self.cfg.token,
                    "properties": super_properties(),
                    "presence": {
                        "status": "online",
                        "since": 0,
                        "activities": [],
                        "afk": False,
                    },
                    "compress": False,
                    "client_state": {
                        "guild_versions": {},
                        "highest_last_message_id": "0",
                        "read_state_version": 0,
                        "user_guild_settings_version": -1,
                        "user_settings_version": -1,
                        "private_channels_version": "0",
                        "api_code_version": 0,
                    },
                },
            }
        return {
            "op": OP_IDENTIFY,
            "d": {
                "token": self.cfg.token,
                "intents": BOT_INTENTS,
                "properties": {
                    "os": sys.platform,
                    "browser": "discord-forwarder",
                    "device": "discord-forwarder",
                },
            },
        }

    async def _heartbeat_loop(self, interval_ms: int, ws) -> None:
        interval = interval_ms / 1000
        await asyncio.sleep(interval * random.random())  # jitter on the first beat
        while not ws.closed:
            if not self._ack:
                LOG.warning("No heartbeat ACK from Discord, reconnecting")
                await ws.close(code=4000)
                return
            self._ack = False
            try:
                await ws.send_json({"op": OP_HEARTBEAT, "d": self._seq})
            except (ConnectionResetError, aiohttp.ClientError):
                return
            await asyncio.sleep(interval)

    async def _handle_dispatch(self, event: str, data: dict) -> None:
        if event == "READY":
            user = data.get("user") or {}
            self.user_id = int(user["id"]) if user.get("id") else None
            self._session_id = data.get("session_id")
            self._resume_url = data.get("resume_gateway_url")
            LOG.info(
                "Connected as %s (%s)",
                display_name(user),
                self.user_id if self.user_id else "?",
            )
            for channel_id in sorted(self.cfg.source_channel_ids):
                LOG.info("Watching %s (%s)", await self.http.channel_label(channel_id), channel_id)
        elif event == "RESUMED":
            LOG.info("Session resumed")
        elif event == "MESSAGE_CREATE":
            if self._should_forward(data):
                await self._forward(data)
        elif event == "MESSAGE_UPDATE":
            # Edits arrive as partial objects; only relay ones carrying real content.
            if self.cfg.forward_edits and data.get("content") and self._should_forward(data):
                await self._forward(data, edited=True)

    def _should_forward(self, message: dict) -> bool:
        try:
            channel_id = int(message.get("channel_id", 0))
        except (TypeError, ValueError):
            return False
        if channel_id not in self.cfg.source_channel_ids:
            return False
        if channel_id == self.cfg.destination_channel_id:
            return False
        webhook_id = message.get("webhook_id")
        if webhook_id and int(webhook_id) == self.cfg.webhook_id:
            return False  # our own relayed message
        author = message.get("author") or {}
        author_id = author.get("id")
        if author_id and self.user_id and int(author_id) == self.user_id:
            if not self.cfg.forward_own:
                return False
        if author.get("bot") and not self.cfg.forward_bots:
            return False
        if message.get("type", 0) not in RELAYABLE_TYPES:
            return False
        if not (
            message.get("content")
            or message.get("attachments")
            or message.get("embeds")
            or message.get("sticker_items")
        ):
            return False
        return True

    async def _forward(self, message: dict, *, edited: bool = False) -> None:
        try:
            await self.relay.send(message, edited=edited)
        except Exception:
            LOG.exception("Failed to forward message %s", message.get("id"))

    async def _run_once(self) -> None:
        url = await self._gateway_url()
        headers = {"User-Agent": BROWSER_UA}
        async with self.session.ws_connect(url, headers=headers, heartbeat=None) as ws:
            self._ws = ws
            resuming = bool(self._session_id and self._seq is not None)

            async for raw in ws:
                if raw.type is not aiohttp.WSMsgType.TEXT:
                    break
                payload = json.loads(raw.data)
                op = payload.get("op")
                if payload.get("s") is not None:
                    self._seq = payload["s"]

                if op == OP_HELLO:
                    interval = payload["d"]["heartbeat_interval"]
                    self._ack = True
                    self._heartbeat_task = asyncio.create_task(
                        self._heartbeat_loop(interval, ws)
                    )
                    if resuming:
                        LOG.info("Resuming previous session")
                        await ws.send_json(
                            {
                                "op": OP_RESUME,
                                "d": {
                                    "token": self.cfg.token,
                                    "session_id": self._session_id,
                                    "seq": self._seq,
                                },
                            }
                        )
                    else:
                        await ws.send_json(self._identify_payload())
                elif op == OP_HEARTBEAT:
                    await ws.send_json({"op": OP_HEARTBEAT, "d": self._seq})
                elif op == OP_HEARTBEAT_ACK:
                    self._ack = True
                elif op == OP_RECONNECT:
                    LOG.info("Discord asked us to reconnect")
                    await ws.close()
                    break
                elif op == OP_INVALID_SESSION:
                    resumable = bool(payload.get("d"))
                    LOG.info("Session invalidated (resumable=%s)", resumable)
                    if not resumable:
                        self._session_id = None
                        self._seq = None
                        self._resume_url = None
                    await asyncio.sleep(1 + random.random() * 4)
                    await ws.close()
                    break
                elif op == OP_DISPATCH:
                    await self._handle_dispatch(payload.get("t") or "", payload.get("d") or {})

            code = ws.close_code
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
            if code in FATAL_CLOSE_CODES:
                raise FatalGatewayError(f"gateway closed {code}: {FATAL_CLOSE_CODES[code]}")
            if code is not None and code != 1000:
                LOG.warning("Gateway closed with code %s", code)

    async def run(self) -> None:
        backoff = 1.0
        while not self._closing:
            try:
                await self._run_once()
                backoff = 1.0
            except FatalGatewayError:
                raise
            except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as exc:
                LOG.warning("Connection problem: %s", exc)
            if self._closing:
                break
            LOG.info("Reconnecting in %.1fs", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60.0)


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
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


async def run(cfg: Config) -> int:
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=90)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        http = DiscordHTTP(cfg, session)
        try:
            metadata = await http.fetch_webhook_metadata()
            cfg.destination_channel_id = int(metadata.get("channel_id", 0))
            if cfg.destination_channel_id in cfg.source_channel_ids:
                raise ConfigError(
                    "The destination webhook posts into one of the SOURCE_CHANNEL_IDS, "
                    "which would forward messages back into themselves. "
                    "Use a different channel."
                )
            LOG.info(
                "Destination webhook %r resolved to channel %s",
                metadata.get("name", "webhook"),
                cfg.destination_channel_id,
            )
            account = await http.verify_token()
            LOG.info(
                "Authenticated as %s (%s account)",
                display_name(account),
                cfg.account_type,
            )
        except ConfigError as exc:
            LOG.error("Configuration error: %s", exc)
            return 2
        except aiohttp.ClientError as exc:
            LOG.error("Could not reach Discord: %s", exc)
            return 1

        client = GatewayClient(cfg, http, Relay(cfg, http))

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(client.close()))
            except NotImplementedError:  # Windows
                pass

        try:
            await client.run()
        except FatalGatewayError as exc:
            LOG.error("%s", exc)
            return 2
        return 0


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

    if cfg.is_user_account:
        LOG.warning(
            "Running against a USER account. Automating a personal account is against "
            "Discord's Terms of Service and can get the account terminated."
        )

    try:
        return asyncio.run(run(cfg))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
