from datetime import datetime
from ipaddress import IPv4Address
from os import environ

import pytest
from pytest import MonkeyPatch

from ipget.alchemy import MySQL, SQLite, get_database
from ipget.errors import ConfigurationError

MYSQL_REQUIRES = [
    environ.get("IPGET_MYSQL_USERNAME"),
    environ.get("IPGET_MYSQL_PASSWORD"),
    environ.get("IPGET_MYSQL_HOST"),
    environ.get("IPGET_MYSQL_PORT"),
    environ.get("IPGET_MYSQL_DATABASE"),
]


def return_none(*args, **kwargs):
    return None


class TestGetDatabase:
    def test_get_mysql(self, monkeypatch: MonkeyPatch):
        # sourcery skip: class-extract-method
        monkeypatch.setattr(MySQL, "__init__", return_none)
        db = get_database("MySQL")
        assert isinstance(db, MySQL)

    def test_get_sqlite(self, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(SQLite, "__init__", return_none)
        db = get_database("SQLite")
        assert isinstance(db, SQLite)

    def test_invalid_db(self):
        with pytest.raises(ConfigurationError):
            get_database("invalid")


@pytest.mark.skipif(
    condition=not all(MYSQL_REQUIRES),
    reason="MySQL requirements not given in .env",
)
class TestMySQL:
    def test_write_data(self, ip_data_static: tuple[datetime, IPv4Address]):
        db = MySQL()
        db.write_data(*ip_data_static)

    def test_missing_env_vars(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv("IPGET_MYSQL_HOST")
        with pytest.raises(ConfigurationError):
            MySQL()

    def test_get_last(self, ip_data_random: tuple[datetime, IPv4Address]):
        db = MySQL()
        new_id = db.write_data(*ip_data_random)
        last = db.get_last()
        assert last is not None
        last_id, last_datetime, last_ip = last
        assert last_id == new_id
        assert last_datetime == ip_data_random[0].replace(tzinfo=None)
        assert last_ip == ip_data_random[1]


class TestSQLite:
    def test_write_data(
        self, ip_data_static: tuple[datetime, IPv4Address], sqlite_in_memory: SQLite
    ):
        new_id = sqlite_in_memory.write_data(*ip_data_static)
        assert isinstance(new_id, int)
        assert new_id > -1

    def test_missing_env_var(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv("IPGET_SQLITE_DATABASE", raising=False)
        monkeypatch.setattr(SQLite, "create_engine", return_none)
        monkeypatch.setattr(SQLite, "create_table", return_none)
        assert SQLite().database_name == "public_ip.db"

    def test_in_memory_db(self, monkeypatch: MonkeyPatch):
        monkeypatch.setenv("IPGET_SQLITE_DATABASE", ":memory:")
        assert SQLite().database_name == ":memory:"

    def test_get_last(
        self, ip_data_random: tuple[datetime, IPv4Address], sqlite_in_memory: SQLite
    ):
        db = sqlite_in_memory
        new_id = db.write_data(*ip_data_random)
        last = db.get_last()
        assert last is not None
        last_id, last_datetime, last_ip = last
        assert last_id == new_id
        assert last_datetime == ip_data_random[0].replace(tzinfo=None)
        assert last_ip == ip_data_random[1]
