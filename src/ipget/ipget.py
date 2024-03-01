import logging
import urllib.error
import urllib.request
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Literal

from pydantic import HttpUrl

from ipget.alchemy import AlchemyDB
from ipget.errors import IPRetrievalError
from ipget.settings import URLSettings

log = logging.getLogger(__name__)


def get_ip_from_url(url: str) -> IPv4Address | IPv6Address | None:
    """
    Returns the current public IP address.

    This function retrieves the current public IP address by making a request to https://ident.me.
    It returns the IP address as an instance of either IPv4Address or IPv6Address.

    Returns:
        IPv4Address | IPv6Address: The current public IP address.
    """
    log.debug(f"Retrieving current IP from {url}")
    try:
        ip_str = urllib.request.urlopen("https://ident.me").read().decode("utf8")
        return ip_address(ip_str)
    except urllib.error.URLError:
        log.warning(
            f"Failed to retrieve IP address from {url}",
            exc_info=log.level == logging.DEBUG,
        )
    return None


def get_current_ip() -> IPv4Address | IPv6Address:
    """
    Retrieves the current IP address from a list of URLs.

    Returns:
        The current IP address as an instance of either IPv4Address or IPv6Address.

    Raises:
        Exception: If the current IP address cannot be retrieved from any source.
    """
    # TODO: Make list of URLs a configuration option
    config = URLSettings()
    http_urls: list[HttpUrl] = config.urls
    urls: list[str] = [str(url) for url in http_urls]
    for url in urls:
        current_ip = get_ip_from_url(url)
        if current_ip:
            log.info(f"Current IP: {current_ip}")
            return current_ip
    raise IPRetrievalError(urls)


def get_previous_ip(
    db: AlchemyDB,
) -> IPv4Address | IPv6Address | Literal["Unknown"] | None:
    """
    Returns the previous public IP address.

    Args:
        db (AlchemyDB): The database object used to retrieve the previous IP address.

    Returns:
        IPv4Address | IPv6Address | Literal["Unknown"] | None: The previous IP address,
        if available, "Unknown" if the database was just created, or None
        if there was an error retrieving the previous IP address.
    """
    log.debug("Retrieving previous IP from database")

    # If the database was only just created, there is no previous IP
    if db.created_new_table:
        log.warning("First run on new database, previous IP is unknown")
        return "Unknown"

    last = db.get_last()
    previous_ip = last[2] if last else None
    if previous_ip:
        log.info(f"Previous IP: {previous_ip}")
    else:
        log.warning("Error retrieving previous IP address")
    return previous_ip
