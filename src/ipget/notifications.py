import logging
from http.client import responses
from ipaddress import IPv4Address, IPv6Address
from os import environ
from typing import Literal

from discord_webhook import DiscordWebhook
from requests import Response

from ipget.errors import ConfigurationError

log = logging.getLogger(__name__)


class Discord:
    def __init__(self) -> None:
        if webhook_url := environ.get("IPGET_DISCORD_WEBHOOK"):
            self.webhook_url = webhook_url
        else:
            raise ConfigurationError("IPGET_DISCORD_WEBHOOK")

    def _send_basic_message(self, message) -> Response:
        self._webhook = DiscordWebhook(
            url=self.webhook_url,
            content=message,
            rate_limit_retry=True,
            # avatar_url="/app/assets/avatar.jpg"
        )
        response = self._webhook.execute()
        log.debug(
            f"Response: {response.status_code} {responses.get(response.status_code)}"
        )
        return response

    def notify_success(
        self,
        previous_ip: IPv4Address | IPv6Address | Literal["Unknown"] | None,
        current_ip: IPv4Address | IPv6Address,
    ) -> int:
        "Sends notification if the public ip has changed"
        log.debug("Sending message to Discord webhook")
        error = f"Error retrieving previous IP address\nCurrent IP: {current_ip}"
        success = (
            "**Public ip address has changed!**\n"
            f"Previous: {previous_ip}\n"
            f"New: {current_ip}"
        )
        message = success if previous_ip else error
        return self._send_basic_message(message).status_code

    def notify_error(self, errors: list[Exception]) -> int:
        log.debug("Sending errors to Discord webhook")
        message = "**Encountered Errors:**\n" + "\n".join(str(e) for e in errors)
        return self._send_basic_message(message).status_code


def get_discord() -> Discord | None:
    try:
        return Discord()
    except ConfigurationError as e:
        log.warning(f"{e}. Discord notifications disabled")
        return None
