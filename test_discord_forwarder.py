"""Tests for the pure helpers in discord_forwarder."""

import os

import pytest

import discord_forwarder as fw

WEBHOOK = "https://discord.com/api/webhooks/999/tok"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith(
            ("DISCORD_", "ACCOUNT_", "SOURCE_", "DESTINATION_", "FORWARD_",
             "RELAY_", "SHOW_", "MAX_ATTACHMENT", "MESSAGE_PREFIX")
        ):
            monkeypatch.delenv(key, raising=False)


def base_env(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "token")
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", WEBHOOK)
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111")


# ---- chunking ----

def test_chunk_content_leaves_short_text_alone():
    assert fw.chunk_content("hello") == ["hello"]
    assert fw.chunk_content("") == []


def test_chunk_content_splits_on_newlines():
    text = "\n".join(["x" * 90] * 30)
    chunks = fw.chunk_content(text, limit=200)
    assert all(len(chunk) <= 200 for chunk in chunks)
    assert "".join(c.replace("\n", "") for c in chunks) == text.replace("\n", "")


def test_chunk_content_splits_unbroken_text():
    text = "y" * 4500
    chunks = fw.chunk_content(text)
    assert all(len(chunk) <= fw.MESSAGE_LIMIT for chunk in chunks)
    assert "".join(chunks) == text


# ---- naming / URLs ----

def test_sanitize_username_handles_reserved_words_and_length():
    assert fw.sanitize_username("plain name") == "plain name"
    assert "discord" not in fw.sanitize_username("discord fan").lower()
    assert fw.sanitize_username("") == "unknown"
    assert len(fw.sanitize_username("z" * 200)) <= fw.USERNAME_LIMIT


def test_display_name_prefers_global_name():
    assert fw.display_name({"global_name": "Dan", "username": "dan_x"}) == "Dan"
    assert fw.display_name({"username": "dan_x"}) == "dan_x"
    assert fw.display_name({}) == "unknown"


def test_avatar_url_handles_custom_animated_and_default():
    assert fw.avatar_url({"id": "1", "avatar": "abc"}).endswith("abc.png?size=128")
    assert ".gif" in fw.avatar_url({"id": "1", "avatar": "a_abc"})
    assert "/embed/avatars/" in fw.avatar_url({"id": "12345678901234567890"})


def test_jump_url_covers_guild_and_dm():
    assert fw.jump_url({"guild_id": "1", "channel_id": "2", "id": "3"}).endswith("/1/2/3")
    assert "/@me/" in fw.jump_url({"channel_id": "2", "id": "3"})


def test_clean_content_resolves_user_mentions():
    message = {
        "content": "hey <@123> and <@!456> and <@999>",
        "mentions": [
            {"id": "123", "global_name": "Ann"},
            {"id": "456", "username": "bob"},
        ],
    }
    result = fw.clean_content(message)
    assert "@Ann" in result and "@bob" in result
    assert "<@123>" not in result
    assert "@unknown" in result  # unresolved mention degrades gracefully


# ---- config ----

def test_webhook_url_regex_accepts_known_forms():
    for url in (
        "https://discord.com/api/webhooks/123/abc-DEF_456",
        "https://discordapp.com/api/webhooks/123/abc",
        "https://discord.com/api/v10/webhooks/123/abc",
        "https://discord.com/api/webhooks/123/abc?thread_id=456",
    ):
        assert fw.WEBHOOK_URL_RE.match(url), url
    assert not fw.WEBHOOK_URL_RE.match("https://example.com/api/webhooks/123/abc")
    assert not fw.WEBHOOK_URL_RE.match("https://discord.com/api/webhooks/abc/def")


def test_config_defaults_to_user_account(monkeypatch):
    base_env(monkeypatch)
    cfg = fw.Config.from_env()
    assert cfg.account_type == "user"
    assert cfg.is_user_account
    assert cfg.auth_header == "token"  # user tokens are sent bare
    assert cfg.webhook_id == 999
    assert cfg.source_channel_ids == {111}
    assert cfg.show_source is False  # single source channel


def test_config_bot_account_prefixes_auth(monkeypatch):
    base_env(monkeypatch)
    monkeypatch.setenv("ACCOUNT_TYPE", "bot")
    cfg = fw.Config.from_env()
    assert cfg.auth_header == "Bot token"
    assert not cfg.is_user_account


def test_config_show_source_defaults_on_for_multiple_channels(monkeypatch):
    base_env(monkeypatch)
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111, 222")
    cfg = fw.Config.from_env()
    assert cfg.source_channel_ids == {111, 222}
    assert cfg.show_source is True


def test_config_rejects_bad_input(monkeypatch):
    base_env(monkeypatch)
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "not-a-number")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()

    base_env(monkeypatch)
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", "https://example.com/hook")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()

    base_env(monkeypatch)
    monkeypatch.setenv("ACCOUNT_TYPE", "selfbot")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()


def test_config_rejects_bot_prefixed_token(monkeypatch):
    base_env(monkeypatch)
    monkeypatch.setenv("DISCORD_TOKEN", "Bot abc123")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()


def test_config_requires_token(monkeypatch):
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", WEBHOOK)
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()


# ---- identify payloads ----

def test_user_identify_omits_intents(monkeypatch):
    base_env(monkeypatch)
    cfg = fw.Config.from_env()
    client = fw.GatewayClient(cfg, http=None, relay=None)
    payload = client._identify_payload()["d"]
    assert "intents" not in payload  # user accounts must not send intents
    assert payload["properties"]["browser"] == "Chrome"
    assert payload["token"] == "token"


def test_bot_identify_includes_intents(monkeypatch):
    base_env(monkeypatch)
    monkeypatch.setenv("ACCOUNT_TYPE", "bot")
    cfg = fw.Config.from_env()
    client = fw.GatewayClient(cfg, http=None, relay=None)
    payload = client._identify_payload()["d"]
    assert payload["intents"] == fw.BOT_INTENTS


# ---- forwarding filter ----

def make_client(monkeypatch, **env):
    base_env(monkeypatch)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    cfg = fw.Config.from_env()
    cfg.destination_channel_id = 555
    client = fw.GatewayClient(cfg, http=None, relay=None)
    client.user_id = 42
    return client


def message(**overrides):
    payload = {
        "id": "1",
        "channel_id": "111",
        "type": 0,
        "content": "hello",
        "author": {"id": "7", "username": "someone"},
    }
    payload.update(overrides)
    return payload


def test_should_forward_accepts_plain_message(monkeypatch):
    assert make_client(monkeypatch)._should_forward(message()) is True


def test_should_forward_ignores_other_channels(monkeypatch):
    client = make_client(monkeypatch)
    assert client._should_forward(message(channel_id="999")) is False
    assert client._should_forward(message(channel_id="555")) is False


def test_should_forward_blocks_relay_loops(monkeypatch):
    client = make_client(monkeypatch)
    # A message posted by our own destination webhook must never come back around.
    assert client._should_forward(message(webhook_id="999")) is False


def test_should_forward_skips_own_and_bot_messages(monkeypatch):
    client = make_client(monkeypatch)
    assert client._should_forward(message(author={"id": "42"})) is False
    assert client._should_forward(message(author={"id": "7", "bot": True})) is False

    chatty = make_client(monkeypatch, FORWARD_OWN="true", FORWARD_BOTS="true")
    assert chatty._should_forward(message(author={"id": "42"})) is True
    assert chatty._should_forward(message(author={"id": "7", "bot": True})) is True


def test_should_forward_skips_system_and_empty_messages(monkeypatch):
    client = make_client(monkeypatch)
    assert client._should_forward(message(type=7)) is False  # join notice
    assert client._should_forward(message(content="")) is False
    assert client._should_forward(message(content="", attachments=[{"url": "x"}])) is True
