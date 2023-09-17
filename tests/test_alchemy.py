import os
from datetime import datetime
from ipaddress import IPv4Address
from os import environ

import pytest
from pytest import MonkeyPatch

from ipget.alchemy import MySQL, PostgreSQL, SQLite, get_database
from ipget.errors import ConfigurationError

MYSQL_POSTGRES_REQUIRES = [
    environ.get("IPGET_USERNAME"),
    environ.get("IPGET_PASSWORD"),
    environ.get("IPGET_HOST"),
    environ.get("IPGET_PORT"),
    environ.get("IPGET_DATABASE"),
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

    def test_get_postgres(self, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(PostgreSQL, "__init__", return_none)
        db = get_database("postgres")
        assert isinstance(db, PostgreSQL)

    def test_get_postgresql(self, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(PostgreSQL, "__init__", return_none)
        db = get_database("PostgreSQL")
        assert isinstance(db, PostgreSQL)

    def test_invalid_db(self):
        with pytest.raises(ConfigurationError):
            get_database("invalid")


class TestSQLite:
    @pytest.fixture(autouse=True)
    def get_test_env_vars(self, request, monkeypatch: MonkeyPatch):
        if request.node.get_closest_marker("no_test_env"):
            return None
        database_path = os.getenv("IPGET_TEST_SQLITE_DATABASE", "localhost")
        monkeypatch.setenv(name="IPGET_DATABASE", value=database_path)

    def test_write_data(
        self, ip_data_static: tuple[datetime, IPv4Address], sqlite_in_memory: SQLite
    ):
        new_id = sqlite_in_memory.write_data(*ip_data_static)
        assert isinstance(new_id, int)
        assert new_id > -1

    def test_missing_env_var(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv("IPGET_DATABASE", raising=False)
        monkeypatch.setattr(SQLite, "create_engine", return_none)
        monkeypatch.setattr(SQLite, "create_table", return_none)
        assert SQLite().database_path.name == "public_ip.db"

    @pytest.mark.no_test_env
    def test_in_memory_db(self, monkeypatch: MonkeyPatch):
        monkeypatch.setenv("IPGET_DATABASE", ":memory:")
        assert SQLite().database_path.name == ":memory:"

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


@pytest.mark.skipif(
    condition=not all(MYSQL_POSTGRES_REQUIRES),
    reason="MySQL requirements not given in .env",
)
class TestMySQL:
    @pytest.fixture(autouse=True)
    def get_test_env_vars(self, monkeypatch: MonkeyPatch):
        host = os.getenv("IPGET_TEST_MYSQL_HOST", "localhost")
        port = os.getenv("IPGET_TEST_MYSQL_PORT", "5432")
        monkeypatch.setenv(name="IPGET_HOST", value=host)
        monkeypatch.setenv(name="IPGET_PORT", value=port)

    def test_write_data(self, ip_data_static: tuple[datetime, IPv4Address]):
        db = MySQL()
        db.write_data(*ip_data_static)

    def test_missing_env_vars(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv("IPGET_HOST")
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


@pytest.mark.skipif(
    condition=not all(MYSQL_POSTGRES_REQUIRES),
    reason="PostgreSQL requirements not given in .env",
)
class TestPostgreSQL:
    @pytest.fixture(autouse=True)
    def get_test_env_vars(self, monkeypatch: MonkeyPatch):
        host = os.getenv("IPGET_TEST_POSTGRES_HOST", "localhost")
        port = os.getenv("IPGET_TEST_POSTGRES_PORT", "5432")
        monkeypatch.setenv(name="IPGET_HOST", value=host)
        monkeypatch.setenv(name="IPGET_PORT", value=port)

    def test_write_data(self, ip_data_static: tuple[datetime, IPv4Address]):
        db = PostgreSQL()
        db.write_data(*ip_data_static)

    def test_missing_env_vars(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv("IPGET_HOST")
        with pytest.raises(ConfigurationError):
            PostgreSQL()

    def test_get_last(self, ip_data_random: tuple[datetime, IPv4Address]):
        db = PostgreSQL()
        new_id = db.write_data(*ip_data_random)
        last = db.get_last()
        assert last is not None

        given_datetime, given_ip = ip_data_random
        last_id, last_datetime, last_ip = last

        assert last_id == new_id
        assert last_datetime == given_datetime.replace(tzinfo=None)
        assert last_ip == given_ip
