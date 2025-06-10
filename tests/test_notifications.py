from datetime import datetime, timezone
from ipaddress import IPv4Address
from os import environ

import pytest
from pytest import MonkeyPatch
from requests import ConnectionError, HTTPError, Response  # noqa: A004

from ipget.environment import DISCORD_WEBHOOK_ENV
from ipget.errors import ConfigurationError
from ipget.notifications import Discord


class TestDiscord:
    def test_load_settings(self, monkeypatch: MonkeyPatch):
        test_value = "pytest-discord-webhook"
        monkeypatch.setenv(DISCORD_WEBHOOK_ENV, test_value)
        discord = Discord()
        assert discord.webhook_url == test_value

    def test_notify_changed_no_previous(self, mock_discord_with_response):
        # sourcery skip: class-extract-method
        discord = Discord()
        response = discord.notify_success(
            previous_ip=None, current_ip=IPv4Address("10.10.10.42")
        )
        assert response == 200
        assert isinstance(discord._webhook.content, str)
        assert "Error retrieving previous IP address" in discord._webhook.content

    def test_notify_changed_previous_unknown(self, mock_discord_with_response):
        discord = Discord()
        response = discord.notify_success(
            previous_ip="Unknown", current_ip=IPv4Address("10.10.10.42")
        )
        assert response == 200
        assert isinstance(discord._webhook.content, str)
        assert "Previous: Unknown" in discord._webhook.content

    def test_notify_changed(self, mock_discord_with_response):
        discord = Discord()
        response = discord.notify_success(
            previous_ip=IPv4Address("192.168.1.42"),
            current_ip=IPv4Address("10.10.10.42"),
        )
        assert response == 200
        assert isinstance(discord._webhook.content, str)
        assert "Previous: 192.168.1.42" in discord._webhook.content
        assert "New: 10.10.10.42" in discord._webhook.content

    def test_no_webhook(self, monkeypatch: MonkeyPatch, mock_discord_with_response):
        monkeypatch.delenv(DISCORD_WEBHOOK_ENV, raising=False)
        with pytest.raises(ConfigurationError):
            Discord()

    def test_notify_error(self, mock_discord_with_response):
        discord = Discord()
        response = discord.notify_error(
            [
                ConfigurationError("IPGET_TEST_NOTIFICATION_1"),
                ConfigurationError("IPGET_TEST_NOTIFICATION_2"),
            ]
        )
        assert response == 200
        assert isinstance(discord._webhook.content, str)
        assert "IPGET_TEST_NOTIFICATION_1" in discord._webhook.content
        assert "IPGET_TEST_NOTIFICATION_2" in discord._webhook.content

    @pytest.mark.skipif(
        condition=not environ.get("IPGET_TEST_DISCORD_WEBHOOK"),
        reason="Discord webhook not given in .env.test",
    )
    def test_real_notification(self, env_testing_notification_settings):
        message = "\n".join(
            [
                "**IPget pytest**",
                "Test sending a real notification",
                datetime.now(timezone.utc).isoformat(timespec="minutes"),
            ]
        )
        try:
            discord = Discord(env_testing_notification_settings)
            response = discord._send_basic_message(message)
        except (ConnectionError, HTTPError) as e:
            pytest.skip(reason=f"Encountered HTTP Error {e.response}")
        assert isinstance(response, Response)
