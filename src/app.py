import logging
import urllib.request
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, ip_address
from logging.handlers import TimedRotatingFileHandler
from os import environ
from pathlib import Path
from sys import exit

from ipget.alchemy import get_database
from ipget.healthchecks import get_healthcheck
from ipget.notifications import get_discord

log = logging.getLogger("ipget")


def setup_logging():
    """Setup file and console logging."""
    log_dir = Path("/app/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        log_dir / "ipget.log",
        when="W0",
        backupCount=4,
        encoding="utf8",
    )
    file_handler.setFormatter(logging.Formatter(""))
    log.addHandler(file_handler)
    log.critical("")
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-19s[%(lineno)3d]%(levelname)7s: %(message)s"
        )
    )
    level = environ.get("IPGET_LOG_LEVEL", "INFO")
    log.setLevel(level.upper() if isinstance(level, str) else level)
    console_handler = logging.StreamHandler()
    log.addHandler(console_handler)
    console_handler.setFormatter(
        logging.Formatter("%(name)-19s[%(lineno)3d] %(levelname)7s: %(message)s")
    )


def get_current_ip() -> IPv4Address | IPv6Address:
    "Returns the current public ip address"
    log.debug("Retrieving current IP from https://ident.me")
    ip_str = urllib.request.urlopen("https://ident.me").read().decode("utf8")
    return ip_address(ip_str)


def main() -> int:
    setup_logging()
    db = get_database()

    if not db.created_new_table:
        last = db.get_last()
        previous_ip = last[2] if last else None
        if previous_ip:
            log.info(f"Previous IP: {previous_ip}")
        else:
            log.warning("Error retrieving previous IP address")
    else:
        log.warning("First run on new database, previous IP is unknown")
        previous_ip = "Unknown"

    current_ip = None
    error_list = []
    notify = get_discord()
    try:
        current_ip = get_current_ip()
        log.info(f"Current IP: {current_ip}")
        db.write_data(datetime.now(timezone.utc), current_ip)
    except Exception as e:
        log.exception(e)
        if notify:
            notify.notify_error([e])
        error_list.append(e)

    hc = get_healthcheck()
    if current_ip:
        if hc:
            hc.success({"ip": current_ip})
        if current_ip != previous_ip:
            if previous_ip:
                log.info(f"IP address has changed: '{previous_ip}' → '{current_ip}'")
            if notify:
                notify.notify_success(previous_ip, current_ip)
        else:
            log.info("IP address has not changed")
    elif hc:
        hc.fail()

    if error_list:
        if notify:
            notify.notify_error(error_list)
        log.debug("Exit code 1")
        return 1
    else:
        log.debug("Exit code 0")
        return 0


if __name__ == "__main__":
    exit(main())
