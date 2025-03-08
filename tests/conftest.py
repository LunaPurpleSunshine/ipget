import urllib.request as req
from datetime import datetime, timezone
from ipaddress import IPv4Address
from os import environ
from pathlib import Path
from random import randint

import pytest
from discord_webhook import DiscordWebhook  # type: ignore[import-untyped]
from dotenv import load_dotenv
from pytest import MonkeyPatch

from ipget.alchemy import SQLite
from ipget.healthchecks import HealthCheck
from ipget.settings import (
    DISCORD_WEBHOOK_ENV,
    HEALTHCHECK_SERVER_ENV,
    HEALTHCHECK_UUID_ENV,
    AppSettings,
    GenericDatabaseSettings,
    HealthcheckSettings,
    NotificationSettings,
    SQLiteDatabaseSettings,
)

load_dotenv(".env.test", verbose=True, override=True)


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code: int = status_code

    def getcode(self):
        return self.status_code


@pytest.fixture
def mock_discord_with_response(monkeypatch: MonkeyPatch):
    def response_200(*args, **kwargs):
        return FakeResponse(200)

    monkeypatch.setenv(DISCORD_WEBHOOK_ENV, "https://test.example.com")
    monkeypatch.setattr(DiscordWebhook, "execute", response_200)


@pytest.fixture
def ip_data_static() -> tuple[datetime, IPv4Address]:
    return (datetime(1963, 11, 23, 17, 16), IPv4Address("10.10.10.0"))


def generate_random_ipv4_address() -> IPv4Address:
    """Returns a completely random ipaddress.IPv4Address

    Uses, random.randint() to generate a random integer within
    the valid range of IPv4 addresses (from 0 to 2^32 - 1).
    This is then converted to an IPv4Address object using ipaddress.IPv4Address()
    """
    ip_int = randint(0, 2**32 - 1)
    return IPv4Address(ip_int)


@pytest.fixture
def ip_data_random() -> tuple[datetime, IPv4Address]:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    ip = generate_random_ipv4_address()
    return dt, ip


@pytest.fixture(scope="function")
def env_valid_app_settings() -> AppSettings:
    return AppSettings(db_type="sqlite")


@pytest.fixture(scope="function")
def env_test_sqlite_settings() -> SQLiteDatabaseSettings:
    db_name = environ.get("IPGET_TEST_SQLITE_DATABASE") or ":memory:"
    return SQLiteDatabaseSettings(database_file_path=Path(db_name))


@pytest.fixture
def sqlite_in_memory():
    return SQLite(SQLiteDatabaseSettings(database_file_path=Path(":memory:")))


@pytest.fixture(scope="function")
def env_testing_mysql_settings() -> GenericDatabaseSettings:
    test_user = environ.get("IPGET_TEST_MYSQL_USERNAME")
    test_password = environ.get("IPGET_TEST_MYSQL_PASSWORD")
    test_host = environ.get("IPGET_TEST_MYSQL_HOST")
    port = environ.get("IPGET_TEST_MYSQL_PORT")
    test_port = int(port) if port else None
    test_database = environ.get("IPGET_TEST_MYSQL_DATABASE")
    return GenericDatabaseSettings(
        username=test_user,
        password=test_password,
        host=test_host,
        port=test_port,
        database_name=test_database,
    )


@pytest.fixture(scope="function")
def env_testing_postgres_settings() -> GenericDatabaseSettings:
    test_user = environ.get("IPGET_TEST_POSTGRES_USERNAME")
    test_password = environ.get("IPGET_TEST_POSTGRES_PASSWORD")
    test_host = environ.get("IPGET_TEST_POSTGRES_HOST")
    port = environ.get("IPGET_TEST_POSTGRES_PORT")
    test_port = int(port) if port else None
    test_database = environ.get("IPGET_TEST_POSTGRES_DATABASE")
    return GenericDatabaseSettings(
        username=test_user,
        password=test_password,
        host=test_host,
        port=test_port,
        database_name=test_database,
    )


@pytest.fixture(scope="function")
def env_testing_healthcheck_settings():
    test_server = environ.get("IPGET_TEST_HEALTHCHECK_SERVER") or "https://hc-ping.com"
    test_uuid = environ.get("IPGET_TEST_HEALTHCHECK_UUID")
    return HealthcheckSettings(server=test_server, uuid=test_uuid)


@pytest.fixture(scope="function")
def dummy_healthcheck(monkeypatch):
    monkeypatch.setenv(HEALTHCHECK_SERVER_ENV, "https://pytest_dummy_healthcheck")
    monkeypatch.setenv(HEALTHCHECK_UUID_ENV, "pytest_dummy_healthcheck")
    return HealthCheck()


@pytest.fixture
def mock_healthcheck_with_response(monkeypatch: MonkeyPatch):
    def response_200(*args, **kwargs):
        return FakeResponse(200)

    monkeypatch.setenv(HEALTHCHECK_SERVER_ENV, "https://pytest.example.com")
    monkeypatch.setenv(HEALTHCHECK_UUID_ENV, "pytest-uuid")
    monkeypatch.setattr(req, "urlopen", response_200)


@pytest.fixture(scope="function")
def env_testing_notification_settings() -> NotificationSettings:
    test_webhook = environ.get("IPGET_TEST_DISCORD_WEBHOOK")
    return NotificationSettings(discord_webhook=test_webhook)
