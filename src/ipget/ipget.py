import logging
import urllib.request
from ipaddress import IPv4Address, IPv6Address, ip_address

log = logging.getLogger(__name__)


def get_current_ip() -> IPv4Address | IPv6Address:
    "Returns the current public ip address"
    log.debug("Retrieving current IP from https://ident.me")
    ip_str = urllib.request.urlopen("https://ident.me").read().decode("utf8")
    return ip_address(ip_str)
