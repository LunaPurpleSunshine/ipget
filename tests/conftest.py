import urllib.request as req
from datetime import datetime, timezone
from ipaddress import IPv4Address
from random import randint

import pytest
from discord_webhook import DiscordWebhook
from pytest import MonkeyPatch

from ipget.alchemy import SQLite


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code: int = status_code

    def getcode(self):
        return self.status_code


@pytest.fixture
def mock_discord_response(monkeypatch: MonkeyPatch):
    def response_200(*args, **kwargs):
        return FakeResponse(200)

    monkeypatch.setenv("IPGET_DISCORD_WEBHOOK", "https://test.example.com")
    monkeypatch.setattr(DiscordWebhook, "execute", response_200)


@pytest.fixture
def mock_healthcheck_response(monkeypatch: MonkeyPatch):
    def response_200(*args, **kwargs):
        return FakeResponse(200)

    monkeypatch.setenv("IPGET_HEALTHCHECK_SERVER", "https://hc.example.com")
    monkeypatch.setenv("IPGET_HEALTHCHECK_UUID", "test-uuid")
    monkeypatch.setattr(req, "urlopen", response_200)


@pytest.fixture
def sqlite_in_memory(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("IPGET_SQLITE_DATABASE", ":memory:")
    return SQLite()


@pytest.fixture
def ip_data_static() -> tuple[datetime, IPv4Address]:
    return (datetime(1963, 11, 23, 17, 16), IPv4Address("10.10.10.0"))


def generate_random_ipv4_address() -> IPv4Address:
    """Returns a completely random ipaddress.IPv4Address

    In this function, random.randint() is used to generate a random integer
    within the valid range of IPv4 addresses (from 0 to 2^32 - 1),
    the integer is converted to an IPv4Address object using ipaddress.IPv4Address()
    """
    ip_int = randint(0, 2**32 - 1)
    return IPv4Address(ip_int)


@pytest.fixture
def ip_data_random() -> tuple[datetime, IPv4Address]:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    ip = generate_random_ipv4_address()
    return dt, ip
