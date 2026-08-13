"""Tests for the pure helpers in discord_forwarder."""

import os

import pytest

import discord_forwarder as fw


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("DISCORD_", "SOURCE_", "DESTINATION_", "FORWARD_", "RELAY_",
                           "SHOW_", "MAX_ATTACHMENT", "MESSAGE_PREFIX")):
            monkeypatch.delenv(key, raising=False)


def test_chunk_content_leaves_short_text_alone():
    assert fw.chunk_content("hello") == ["hello"]
    assert fw.chunk_content("") == []


def test_chunk_content_splits_on_newlines():
    text = "\n".join(["x" * 90] * 30)
    chunks = fw.chunk_content(text, limit=200)
    assert all(len(chunk) <= 200 for chunk in chunks)
    assert "".join(chunk.replace("\n", "") for chunk in chunks) == text.replace("\n", "")


def test_chunk_content_splits_unbroken_text():
    text = "y" * 4500
    chunks = fw.chunk_content(text)
    assert all(len(chunk) <= fw.MESSAGE_LIMIT for chunk in chunks)
    assert "".join(chunks) == text


def test_sanitize_username_handles_reserved_words_and_length():
    assert fw.sanitize_username("plain name") == "plain name"
    assert "discord" not in fw.sanitize_username("discord fan").lower()
    assert fw.sanitize_username("") == "unknown"
    assert len(fw.sanitize_username("z" * 200)) <= fw.USERNAME_LIMIT


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


def test_config_from_env_parses_settings(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "token")
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", "https://discord.com/api/webhooks/999/tok")
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111, 222")
    cfg = fw.Config.from_env()
    assert cfg.source_channel_ids == {111, 222}
    assert cfg.webhook_id == 999
    assert cfg.show_source is True  # defaults on with multiple sources
    assert cfg.forward_bots is False


def test_config_rejects_bad_input(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "token")
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", "https://discord.com/api/webhooks/999/tok")
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "not-a-number")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()

    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111")
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", "https://example.com/hook")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()


def test_config_requires_token(monkeypatch):
    monkeypatch.setenv("DESTINATION_WEBHOOK_URL", "https://discord.com/api/webhooks/999/tok")
    monkeypatch.setenv("SOURCE_CHANNEL_IDS", "111")
    with pytest.raises(fw.ConfigError):
        fw.Config.from_env()
