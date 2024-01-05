import logging
from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address
from logging.handlers import TimedRotatingFileHandler
from typing import Literal

from ipget.alchemy import AlchemyDB, get_database
from ipget.healthchecks import get_healthcheck
from ipget.helpers import custom_namer
from ipget.ipget import get_current_ip, get_previous_ip
from ipget.notifications import get_discord
from ipget.settings import AppSettings, LoggerSettings

log = logging.getLogger("ipget")


def setup_logging() -> None:
    """Setup file and console logging."""
    log_settings = LoggerSettings()
    log_dir = log_settings.file_path
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        log_dir / "ipget.log",
        when="W0",
        backupCount=4,
        encoding="utf8",
    )
    file_handler.namer = custom_namer
    file_handler.setFormatter(logging.Formatter(""))
    log.addHandler(file_handler)
    log.critical("")
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-19s[%(lineno)3d]%(levelname)7s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    log_level = log_settings.level
    log.setLevel(log_level.upper() if isinstance(log_level, str) else log_level)
    console_handler = logging.StreamHandler()
    log.addHandler(console_handler)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-19s[%(lineno)3d] %(levelname)7s: %(message)s",
            "%H:%M:%S",
        )
    )


def main() -> int:
    setup_logging()
    config = AppSettings()

    db: AlchemyDB = get_database(mode=config.db_type)

    previous_ip: IPv4Address | IPv6Address | Literal[
        "Unknown"
    ] | None = get_previous_ip(db)

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
