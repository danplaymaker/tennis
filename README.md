# tennis

## Discord channel forwarder

`discord_forwarder.py` watches one or more Discord channels and reposts every new
message into a destination channel of your own, in real time. Relayed messages
keep the original author's display name and avatar, so the destination channel
reads like a mirror of the source.

It reads with either a **personal account** (`ACCOUNT_TYPE=user`, the default) or
a **bot account** (`ACCOUNT_TYPE=bot`). Read the warning below before using a
personal account.

### Read this before using a personal account

Automating a personal account — a "self-bot" — is against
[Discord's Terms of Service](https://discord.com/terms). Discord does enforce
this, and the enforcement lands on the account: termination, usually without
warning and without appeal. Points worth knowing:

- **Your user token is equivalent to your password**, except it bypasses 2FA.
  Anyone who obtains it can read your DMs and act as you. Keep it in `.env`
  (gitignored here), never in a commit, a screenshot, or a paste.
- **The token rotates** whenever you change your password or log out, so the
  script will need a fresh one after either.
- Point this at an account you can afford to lose, and prefer a bot account for
  any channel where that option exists.

The script logs a warning at startup in user mode so this stays visible.

### What it handles

- Live forwarding over the Discord gateway (no polling, no cron)
- Original author name + avatar via webhook impersonation
- Attachments re-uploaded so they outlive Discord's expiring CDN links
  (anything over `MAX_ATTACHMENT_BYTES` is forwarded as a link instead)
- Replies quoted with the message they answer, plus a jump link back to the original
- Messages over 2000 characters split on line/word boundaries
- Stickers, rich embeds, and `@mention` markup resolved to readable names
- Rate-limit backoff, automatic reconnect with session RESUME, and loop
  protection so the relay can never forward its own output

Mentions in forwarded text are neutered (`allowed_mentions: parse: []`), so a
relayed `@everyone` will not ping your destination server.

### Setup

**1. Get a token**

*Personal account* — open Discord **in a browser** (the desktop app has
DevTools disabled), press F12, go to the **Network** tab, send or load any
message, click any request to `discord.com/api`, and copy the `Authorization`
request header. That value is your token. Do not include any prefix.

*Bot account* — at <https://discord.com/developers/applications>: New
Application → **Bot** → Reset Token. Enable the **Message Content Intent** under
*Privileged Gateway Intents*, then invite the bot via *OAuth2 → URL Generator*
with the `bot` scope and **View Channels** + **Read Message History**. Set
`ACCOUNT_TYPE=bot`.

A personal account needs no invite step — it already sees every channel you are
in, including DMs and servers where you cannot add a bot. That is the practical
reason to use one.

**2. Create the destination webhook**

In the channel you want messages delivered to: *Channel Settings → Integrations
→ Webhooks → New Webhook → Copy Webhook URL*. This should be a channel you
control — your own server works well.

**3. Configure and run**

```bash
cp .env.example .env       # then fill in the token, source IDs, and webhook URL
pip install -r requirements.txt
python discord_forwarder.py
```

Get channel IDs by enabling *Settings → Advanced → Developer Mode* in Discord,
then right-clicking a channel → **Copy Channel ID**.

Expected startup output:

```
WARNING forwarder: Running against a USER account. Automating a personal account ...
INFO    forwarder: Destination webhook 'relay' resolved to channel 987654321
INFO    forwarder: Authenticated as Me (user account)
INFO    forwarder: Connected as Me (112233445566)
INFO    forwarder: Watching #general (111222333444)
```

### Configuration

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DISCORD_TOKEN` | yes | — | User or bot token, no `Bot ` prefix |
| `SOURCE_CHANNEL_IDS` | yes | — | Comma-separated channel IDs to read |
| `DESTINATION_WEBHOOK_URL` | yes | — | Webhook to post into |
| `ACCOUNT_TYPE` | no | `user` | `user` or `bot` |
| `FORWARD_BOTS` | no | `false` | Also forward bots' and webhooks' messages |
| `FORWARD_OWN` | no | `false` | Also forward your own messages |
| `RELAY_IDENTITY` | no | `true` | Use the author's name/avatar |
| `SHOW_SOURCE` | no | auto | Prepend `[Server / #channel]`; on when watching >1 channel |
| `FORWARD_EDITS` | no | `false` | Repost a message when it is edited |
| `FORWARD_EMBEDS` | no | `true` | Copy rich embeds |
| `MAX_ATTACHMENT_BYTES` | no | `8388608` | Re-upload cap; larger files become links |
| `MESSAGE_PREFIX` | no | — | Text prepended to every forwarded message |
| `LOG_LEVEL` | no | `INFO` | Set `DEBUG` for verbose logs |

### Implementation note

The gateway protocol is implemented directly on `aiohttp` rather than through
`discord.py`, which rejects user tokens by design. The only dependency is
`aiohttp`. Avoiding a self-bot fork of `discord.py` also sidesteps a packaging
trap: those forks install under the same `discord` import name, so they cannot
coexist with `discord.py` in one environment.

In user mode the client sends the browser fingerprint (`X-Super-Properties`,
matching user agent) and omits gateway intents, because a user IDENTIFY that
carries intents is rejected.

### Running it continuously

The script is a long-lived process — it reconnects and resumes on its own, but
needs something to restart it if the host reboots. A systemd unit:

```ini
[Unit]
Description=Discord channel forwarder
After=network-online.target

[Service]
WorkingDirectory=/opt/discord-forwarder
ExecStart=/usr/bin/python3 discord_forwarder.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

If you run it in a sandboxed or firewalled environment, allow egress to
`discord.com`, `gateway.discord.gg`, and `cdn.discordapp.com`.

### Tests

```bash
pip install pytest && python -m pytest
```

26 tests. `test_discord_forwarder.py` covers config parsing, chunking, name and
URL building, and the forwarding filter (including loop protection).
`test_gateway_integration.py` runs the client against a local fake Discord
websocket to verify the HELLO/IDENTIFY handshake, RESUME after a dropped
connection, heartbeat replies, and abort-on-fatal-close-code.
