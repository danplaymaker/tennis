# tennis

## Discord channel forwarder

`discord_forwarder.py` watches one or more Discord channels and reposts every new
message into a destination channel of your own, in real time. Relayed messages
keep the original author's display name and avatar, so the destination channel
reads like a mirror of the source.

### What it handles

- Live forwarding over the Discord gateway (no polling, no cron)
- Original author name + avatar via webhook impersonation
- Attachments re-uploaded so they outlive Discord's expiring CDN links
  (anything over `MAX_ATTACHMENT_BYTES` is forwarded as a link instead)
- Replies quoted with the message they answer, plus a jump link back to the original
- Messages over 2000 characters split on line/word boundaries
- Stickers and rich embeds
- Rate-limit backoff, automatic gateway reconnects, and loop protection so the
  bot can never forward its own output

Mentions in forwarded text are neutered (`allowed_mentions: parse: []`), so a
relayed `@everyone` will not ping your destination server.

### Setup

**1. Create the bot**

At <https://discord.com/developers/applications>: New Application → **Bot** →
Reset Token and copy it. On that same page enable the **Message Content Intent**
under *Privileged Gateway Intents* — without it Discord delivers empty message
bodies and everything forwards blank.

**2. Invite the bot to the source server**

*OAuth2 → URL Generator*, scope `bot`, permissions **View Channels** and
**Read Message History**. Open the generated URL and add it to the server you
want to read. You need permission to add a bot to that server; if it is someone
else's server, ask an admin.

**3. Create the destination webhook**

In the channel you want messages delivered to: *Channel Settings → Integrations
→ Webhooks → New Webhook → Copy Webhook URL*. This is where you have full
control — your own server, or a DM-like private channel only you can see.

**4. Configure and run**

```bash
cp .env.example .env       # then fill in the three required values
pip install -r requirements.txt
python discord_forwarder.py
```

Get channel IDs by enabling *Settings → Advanced → Developer Mode* in Discord,
then right-clicking a channel → **Copy Channel ID**.

Expected startup output:

```
INFO  forwarder: Destination webhook 'relay' resolved to channel 987654321
INFO  forwarder: Connected as Relay#1234 (112233445566)
INFO  forwarder: Watching #general (111222333444)
```

### Configuration

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `DISCORD_BOT_TOKEN` | yes | — | Bot token |
| `SOURCE_CHANNEL_IDS` | yes | — | Comma-separated channel IDs to read |
| `DESTINATION_WEBHOOK_URL` | yes | — | Webhook to post into |
| `FORWARD_BOTS` | no | `false` | Also forward other bots' messages |
| `RELAY_IDENTITY` | no | `true` | Use the author's name/avatar |
| `SHOW_SOURCE` | no | auto | Prepend `[Server / #channel]`; on when watching >1 channel |
| `FORWARD_EDITS` | no | `false` | Repost a message when it is edited |
| `FORWARD_EMBEDS` | no | `true` | Copy rich embeds |
| `MAX_ATTACHMENT_BYTES` | no | `8388608` | Re-upload cap; larger files become links |
| `MESSAGE_PREFIX` | no | — | Text prepended to every forwarded message |
| `LOG_LEVEL` | no | `INFO` | Set `DEBUG` for verbose logs |

### Running it continuously

The script is a long-lived process — it reconnects on its own, but it needs
something to restart it if the host reboots. A systemd unit:

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
`discord.com` and `gateway.discord.gg`.

### Tests

```bash
pip install pytest && python -m pytest
```

Covers config parsing/validation, message chunking, and username sanitizing.

### A note on scope

This uses a **bot** account, which is the supported way to read a channel.
Automating a personal user account to read channels (a "selfbot") is against
Discord's Terms of Service and risks the account, so this script does not do
that — it only reads channels a bot has been legitimately invited to. Bear in
mind that forwarding other people's messages out of a server may still be
against that server's rules even when it is technically permitted.
