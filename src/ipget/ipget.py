import logging
import urllib.request
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Literal

from ipget.alchemy import AlchemyDB

log = logging.getLogger(__name__)


def get_current_ip() -> IPv4Address | IPv6Address:
    """
    Returns the current public IP address.

    This function retrieves the current public IP address by making a request to https://ident.me.
    It returns the IP address as an instance of either IPv4Address or IPv6Address.

    Returns:
        IPv4Address | IPv6Address: The current public IP address.
    """
    log.debug("Retrieving current IP from https://ident.me")
    ip_str = urllib.request.urlopen("https://ident.me").read().decode("utf8")
    return ip_address(ip_str)


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
