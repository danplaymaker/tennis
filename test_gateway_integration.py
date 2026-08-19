"""End-to-end test of the gateway loop against a local fake Discord websocket.

Exercises the parts that cannot be unit tested in isolation: the HELLO ->
IDENTIFY handshake, heartbeat handling, event dispatch, and RESUME after a
dropped connection.
"""

import asyncio
import json
import os

import aiohttp
import pytest
from aiohttp import web

import discord_forwarder as fw


class FakeHTTP:
    """Stands in for DiscordHTTP: real session, no network calls."""

    def __init__(self, session):
        self.session = session

    async def channel_label(self, channel_id):
        return f"#chan-{channel_id}"

    async def guild_label(self, guild_id):
        return "TestGuild"


class RecordingRelay:
    def __init__(self):
        self.sent = []

    async def send(self, message, *, edited=False):
        self.sent.append((message, edited))


def make_config():
    env = {
        "DISCORD_TOKEN": "user-token",
        "DESTINATION_WEBHOOK_URL": "https://discord.com/api/webhooks/999/tok",
        "SOURCE_CHANNEL_IDS": "111",
        "ACCOUNT_TYPE": "user",
    }
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        return fw.Config.from_env()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


READY = {
    "op": 0,
    "s": 1,
    "t": "READY",
    "d": {
        "user": {"id": "42", "username": "me", "global_name": "Me"},
        "session_id": "sess-abc",
        "resume_gateway_url": None,
    },
}

MESSAGE = {
    "op": 0,
    "s": 2,
    "t": "MESSAGE_CREATE",
    "d": {
        "id": "5",
        "channel_id": "111",
        "type": 0,
        "content": "hello from the source channel",
        "author": {"id": "7", "username": "friend"},
    },
}


async def drive(handler, stop_after_messages=1):
    """Run the client against a local websocket server driven by `handler`."""
    received = {"payloads": [], "connections": 0}
    done = asyncio.Event()

    async def ws_handler(request):
        received["connections"] += 1
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await handler(ws, received)
        return ws

    app = web.Application()
    app.router.add_get("/gw", ws_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    cfg = make_config()
    relay = RecordingRelay()

    async with aiohttp.ClientSession() as session:
        client = fw.GatewayClient(cfg, FakeHTTP(session), relay)
        client._gateway_url = lambda: _resolve(f"ws://127.0.0.1:{port}/gw")

        original_send = relay.send

        async def send_and_maybe_stop(message, *, edited=False):
            await original_send(message, edited=edited)
            if len(relay.sent) >= stop_after_messages:
                done.set()

        relay.send = send_and_maybe_stop

        task = asyncio.create_task(client.run())
        try:
            await asyncio.wait_for(done.wait(), timeout=10)
        finally:
            await client.close()
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    await runner.cleanup()
    return relay, received


async def _resolve(value):
    return value


async def _expect_identify(ws, received):
    """Send HELLO, collect the client's first payload, then READY + a message."""
    await ws.send_json({"op": 10, "d": {"heartbeat_interval": 45000}})
    raw = await ws.receive()
    payload = json.loads(raw.data)
    received["payloads"].append(payload)
    await ws.send_json(READY)
    await ws.send_json(MESSAGE)
    await asyncio.sleep(0.2)


def test_handshake_identifies_and_forwards_a_message():
    relay, received = asyncio.run(drive(_expect_identify))

    identify = received["payloads"][0]
    assert identify["op"] == fw.OP_IDENTIFY
    assert identify["d"]["token"] == "user-token"
    assert "intents" not in identify["d"]  # user account

    assert len(relay.sent) == 1
    message, edited = relay.sent[0]
    assert message["content"] == "hello from the source channel"
    assert edited is False


def test_reconnect_resumes_with_stored_session():
    """After a dropped connection the client must RESUME, not re-IDENTIFY."""

    async def handler(ws, received):
        connection = received["connections"]
        await ws.send_json({"op": 10, "d": {"heartbeat_interval": 45000}})
        raw = await ws.receive()
        received["payloads"].append(json.loads(raw.data))
        if connection == 1:
            # First connection: hand out a session, then drop it mid-stream.
            await ws.send_json(READY)
            await ws.close(code=4000)
            return
        await ws.send_json({"op": 0, "s": 3, "t": "RESUMED", "d": {}})
        await ws.send_json(MESSAGE)
        await asyncio.sleep(0.2)

    relay, received = asyncio.run(drive(handler))

    assert received["connections"] == 2
    assert received["payloads"][0]["op"] == fw.OP_IDENTIFY
    resume = received["payloads"][1]
    assert resume["op"] == fw.OP_RESUME
    assert resume["d"]["session_id"] == "sess-abc"
    assert resume["d"]["seq"] == 1
    assert len(relay.sent) == 1


def test_fatal_close_code_stops_reconnecting():
    """A 4004 (bad token) must abort rather than spin in the reconnect loop."""

    async def handler(ws, received):
        await ws.send_json({"op": 10, "d": {"heartbeat_interval": 45000}})
        await ws.receive()
        await ws.close(code=4004)

    async def scenario():
        app = web.Application()

        async def ws_handler(request):
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            await handler(ws, {})
            return ws

        app.router.add_get("/gw", ws_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]

        cfg = make_config()
        async with aiohttp.ClientSession() as session:
            client = fw.GatewayClient(cfg, FakeHTTP(session), RecordingRelay())
            client._gateway_url = lambda: _resolve(f"ws://127.0.0.1:{port}/gw")
            with pytest.raises(fw.FatalGatewayError):
                await asyncio.wait_for(client.run(), timeout=10)
        await runner.cleanup()

    asyncio.run(scenario())


def test_heartbeat_request_is_answered():
    """Discord can ask for an immediate heartbeat (op 1); we must reply with op 1."""

    async def handler(ws, received):
        await ws.send_json({"op": 10, "d": {"heartbeat_interval": 45000}})
        await ws.receive()  # IDENTIFY
        await ws.send_json(READY)
        await ws.send_json({"op": 1, "d": None})
        raw = await ws.receive()
        received["payloads"].append(json.loads(raw.data))
        await ws.send_json(MESSAGE)
        await asyncio.sleep(0.2)

    relay, received = asyncio.run(drive(handler))
    beat = received["payloads"][-1]
    assert beat["op"] == fw.OP_HEARTBEAT
    assert beat["d"] == 1  # last sequence number seen
    assert len(relay.sent) == 1
