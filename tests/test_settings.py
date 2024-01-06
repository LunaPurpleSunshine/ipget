from pathlib import Path

import custom_strategies as cst
import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st
from pydantic import ValidationError

from ipget.settings import (
    AppSettings,
    GenericDatabaseSettings,
    HealthcheckSettings,
    LoggerSettings,
    NotificationSettings,
    SQLiteDatabaseSettings,
)

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DATABASE_TYPES = ["SQLite", "MySQL", "MariaDB", "Postgres", "PostgreSQL"]


class TestLoggerSettings:
    def test_default_values(self):
        settings = LoggerSettings()
        assert settings.level == "INFO"
        assert settings.file_path == Path("/app/logs")

    # @pytest.mark.parametrize("level", LOG_LEVELS)
    # @given(level=cst.log_levels())
    @given(cst.random_casing(LOG_LEVELS))
    def test_valid_log_levels(self, level: str):
        settings = LoggerSettings(level=level)  # type: ignore
        assert settings.level == level.upper()

    @given(bad_level=st.text())
    def test_invalid_log_level(self, bad_level):
        with pytest.raises(ValidationError):
            LoggerSettings(level=bad_level)  # type: ignore

    @given(st.builds(Path, st.text()) | st.text())
    def test_custom_path(self, custom_path):
        settings = LoggerSettings(file_path=custom_path)
        assert settings.file_path == Path(custom_path)


class TestHealthcheckSettings:
    def test_default_values(self):
        settings = HealthcheckSettings()
        assert settings.server == "https://hc-ping.com"
        assert settings.uuid == ""

    @given(server=st.text())
    @example("https://hc-ping.com")
    @example("https://example.com")
    def test_valid_server(self, server):
        settings = HealthcheckSettings(server=server)
        assert settings.server == server

    @given(bad_server=st.integers())
    def test_invalid_server(self, bad_server):
        with pytest.raises(ValidationError):
            HealthcheckSettings(server=bad_server)

    @given(st.text() | st.none())
    def test_valid_uuid(self, uuid):
        settings = HealthcheckSettings(uuid=uuid)
        assert settings.uuid == uuid

    @given(bad_uuid=st.integers())
    def test_invalid_uuid(self, bad_uuid):
        with pytest.raises(ValidationError):
            HealthcheckSettings(uuid=bad_uuid)

    def test_enabled_property_with_uuid(self):
        settings = HealthcheckSettings(uuid="valid-uuid")
        assert settings.enabled is True

    def test_enabled_property_without_uuid(self):
        settings = HealthcheckSettings(uuid=None)
        assert settings.enabled is False


class TestNotificationSettings:
    def test_default_values(self):
        settings = NotificationSettings()
        assert settings.discord_webhook is None

    @given(st.text() | st.none())
    def test_valid_discord_webhook(self, discord_webhook):
        settings = NotificationSettings(discord_webhook=discord_webhook)
        assert settings.discord_webhook == discord_webhook

    @given(bad_hook=st.integers())
    def test_invalid_discord_webhook(self, bad_hook):
        with pytest.raises(ValidationError):
            NotificationSettings(discord_webhook=bad_hook)


class TestSQLiteDatabaseSettings:
    def test_default_values(self):
        settings = SQLiteDatabaseSettings()
        assert settings.database_file_path == Path("/app/public_ip.db")

    @given(custom_path=st.builds(Path, st.text()) | st.text())
    def test_valid_database_file_path(self, custom_path):
        settings = SQLiteDatabaseSettings(database_file_path=custom_path)
        assert settings.database_file_path == Path(custom_path)

    @given(bad_path=st.integers())
    def test_invalid_database_file_path(self, bad_path):
        with pytest.raises(ValidationError):
            SQLiteDatabaseSettings(database_file_path=bad_path)


class TestGenericDatabaseSettings:
    def test_default_values(self):
        settings = GenericDatabaseSettings()
        assert settings.username is None
        assert settings.password is None
        assert settings.host is None
        assert settings.port is None
        assert settings.database_name is None

    @given(
        user=st.text(),
        password=st.text(),
        host=st.text(),
        port=st.integers(),
        db_name=st.text(),
    )
    def test_valid_values(
        self, user: str, password: str, host: str, port: int, db_name: str
    ):
        valid_settings = {
            "username": user,
            "password": password,
            "host": host,
            "port": port,
            "database_name": db_name,
        }
        settings = GenericDatabaseSettings(**valid_settings)  # type: ignore
        assert settings.username == user
        assert settings.password == password
        assert settings.host == host
        assert settings.port == port
        assert settings.database_name == db_name

    @given(bad_user=st.integers())
    def test_invalid_user(self, bad_user: str):
        test_settings = {
            "username": bad_user,
            "password": "test_password",
            "host": "db.example.com",
            "port": 4242,
            "database_name": "test_db",
        }
        with pytest.raises(ValidationError):
            GenericDatabaseSettings(**test_settings)  # type: ignore

    @given(bad_password=st.integers())
    def test_invalid_password(self, bad_password: str):
        test_settings = {
            "username": "test_user",
            "password": bad_password,
            "host": "db.example.com",
            "port": 4242,
            "database_name": "test_db",
        }
        with pytest.raises(ValidationError):
            GenericDatabaseSettings(**test_settings)  # type: ignore

    @given(bad_host=st.integers())
    def test_invalid_host(self, bad_host: str):
        test_settings = {
            "username": "test_user",
            "password": "test_password",
            "host": bad_host,
            "port": 4242,
            "database_name": "test_db",
        }
        with pytest.raises(ValidationError):
            GenericDatabaseSettings(**test_settings)  # type: ignore

    @given(bad_port=st.text(alphabet=st.characters(categories=["L", "P", "S"])))
    def test_invalid_port(self, bad_port: str):
        test_settings = {
            "username": "test_user",
            "password": "test_password",
            "host": "db.example.com",
            "port": bad_port,
            "database_name": "test_db",
        }
        with pytest.raises(ValidationError):
            GenericDatabaseSettings(**test_settings)  # type: ignore

    @given(bad_db_name=st.integers())
    def test_invalid_db_name(self, bad_db_name: str):
        test_settings = {
            "username": "test_user",
            "password": "test_password",
            "host": "db.example.com",
            "port": 4242,
            "database_name": bad_db_name,
        }
        with pytest.raises(ValidationError):
            GenericDatabaseSettings(**test_settings)  # type: ignore


class TestAppSettings:
    def test_default_values(self):
        settings = AppSettings()
        assert settings.db_type == "sqlite"

    # @given(valid_mode=st.sampled_from(DATABASE_TYPES))
    @given(cst.random_casing(DATABASE_TYPES))
    def test_valid_db_type(self, valid_mode: str):
        settings = AppSettings(db_type=valid_mode)  # type: ignore
        assert settings.db_type == valid_mode.lower()

    @given(invalid_mode=st.text())
    def test_invalid_db_type(self, invalid_mode):
        assume(invalid_mode not in DATABASE_TYPES)
        with pytest.raises(ValidationError):
            AppSettings(db_type=invalid_mode)  # type: ignore
