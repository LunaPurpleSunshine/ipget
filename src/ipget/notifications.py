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
    """Class for sending notifications to Discord."""

    def __init__(self) -> None:
        """Initialize the Discord notification object.

        Raises:
            ConfigurationError: If the IPGET_DISCORD_WEBHOOK
            environment variable is not set.
        """
        if webhook_url := environ.get("IPGET_DISCORD_WEBHOOK"):
            self.webhook_url = webhook_url
        else:
            raise ConfigurationError("IPGET_DISCORD_WEBHOOK")

    def _send_basic_message(self, message: str) -> Response:
        """Send a basic (non-embed) message to the Discord webhook.

        Args:
            message (str): The message content to be sent.

        Returns:
            Response: The response object received after executing the webhook.
        """
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
        """Send a notification to the Discord webhook, if the public IP has changed.

        Args:
            previous_ip (IPv4Address | IPv6Address | "Unknown"): Previous IP address.
            current_ip (IPv4Address | IPv6Address): Current IP address value.

        Returns:
            Response: The response object received after executing the webhook.
        """
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
        """Send an error notification to the Discord webhook.

        Args:
            errors (list[Exception]): A list of Exception objects
            representing the encountered errors.

        Returns:
            Response: The response object received after executing the webhook.
        """
        log.debug("Sending errors to Discord webhook")
        message = "**Encountered Errors:**\n" + "\n".join(str(e) for e in errors)
        return self._send_basic_message(message).status_code


def get_discord() -> Discord | None:
    """Get an instance of the Discord notification object or return None.

    Returns:
        Discord | None: An instance of the Discord class if the configuration is valid.
        Otherwise, returns None.

    Raises:
        ConfigurationError: If the Discord object cannot be created.
    """
    try:
        return Discord()
    except ConfigurationError as e:
        log.warning(f"{e}. Discord notifications disabled")
        return None
