import logging
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ipget.environment import (
    DATABASE_TYPE_ENV,
    DISCORD_WEBHOOK_ENV,
    GENERIC_DB_DATABASE_NAME_ENV,
    GENERIC_DB_HOST_ENV,
    GENERIC_DB_PASSWORD_ENV,
    GENERIC_DB_PORT_ENV,
    GENERIC_DB_USERNAME_ENV,
    HEALTHCHECK_SERVER_ENV,
    HEALTHCHECK_UUID_ENV,
    LOG_FILE_PATH,
    LOG_LEVEL_ENV,
    SQLITE_DATABASE_PATH_ENV,
)

log = logging.getLogger(__name__)

LOG_LEVELS = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DATABASE_TYPES = Literal["sqlite", "mysql", "mariadb", "postgres", "postgresql"]


class ConfiguredBaseSettings(BaseSettings):
    """Common configuration used by all `BaseSettings` derived classes."""

    model_config = SettingsConfigDict(
        env_prefix="IPGET_",
        populate_by_name=True,
        # Disabled due to issues when building container, implement later.
        # secrets_dir="/run/secrets" if platform.system() == "Linux" else None,
    )


class LoggerSettings(ConfiguredBaseSettings):
    """Settings used by python logging."""

    level: LOG_LEVELS = Field(
        default="INFO",
        serialization_alias=LOG_LEVEL_ENV,
        validation_alias=LOG_LEVEL_ENV,
    )
    file_path: Path = Field(
        default=Path("/app/logs"),
        serialization_alias=LOG_FILE_PATH,
        validation_alias=LOG_FILE_PATH,
    )

    @field_validator("level", mode="before")
    @classmethod
    def convert_to_upper(cls, v):
        return v.upper() if isinstance(v, str) else v


class HealthcheckSettings(ConfiguredBaseSettings):
    """Settings needed for healthchecks.io pings."""

    server: str = Field(
        default="https://hc-ping.com",
        serialization_alias=HEALTHCHECK_SERVER_ENV,
        validation_alias=HEALTHCHECK_SERVER_ENV,
    )
    uuid: str | None = Field(
        default="",
        serialization_alias=HEALTHCHECK_UUID_ENV,
        validation_alias=HEALTHCHECK_UUID_ENV,
    )

    @property
    def enabled(self) -> bool:
        # TODO: Test this, should be easy
        return bool(self.uuid)


class NotificationSettings(ConfiguredBaseSettings):
    """Settings used by notifications.

    Attributes:
        discord_webhook (str | None): Discord webhook URL for notifications.
    """

    discord_webhook: str | None = Field(
        default=None,
        serialization_alias=DISCORD_WEBHOOK_ENV,
        validation_alias=DISCORD_WEBHOOK_ENV,
    )


class SQLiteDatabaseSettings(ConfiguredBaseSettings):
    """Settings used by the `SQLite` database type."""

    database_file_path: Path = Field(
        default=Path("/app/public_ip.db"),
        serialization_alias=SQLITE_DATABASE_PATH_ENV,
        validation_alias=SQLITE_DATABASE_PATH_ENV,
    )


class GenericDatabaseSettings(ConfiguredBaseSettings):
    """Settings used by multiple database types.

    Currently used by `MySQL` & `Postgres`
    """

    username: str | None = Field(
        default=None,
        serialization_alias=GENERIC_DB_USERNAME_ENV,
        validation_alias=GENERIC_DB_USERNAME_ENV,
    )
    password: str | None = Field(
        default=None,
        serialization_alias=GENERIC_DB_PASSWORD_ENV,
        validation_alias=GENERIC_DB_PASSWORD_ENV,
    )
    host: str | None = Field(
        default=None,
        serialization_alias=GENERIC_DB_HOST_ENV,
        validation_alias=GENERIC_DB_HOST_ENV,
    )
    port: int | None = Field(
        default=None,
        serialization_alias=GENERIC_DB_PORT_ENV,
        validation_alias=GENERIC_DB_PORT_ENV,
    )
    database_name: str | None = Field(
        default=None,
        serialization_alias=GENERIC_DB_DATABASE_NAME_ENV,
        validation_alias=GENERIC_DB_DATABASE_NAME_ENV,
    )


class AppSettings(ConfiguredBaseSettings):
    """Settings used by the main App.

    Attributes:
        db_type (str): Type of the database.
    """

    db_type: DATABASE_TYPES = Field(
        default="sqlite",
        serialization_alias=DATABASE_TYPE_ENV,
        validation_alias=DATABASE_TYPE_ENV,
    )

    @field_validator("db_type", mode="before")
    @classmethod
    def convert_to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v


class URLSettings(ConfiguredBaseSettings):
    """Settings used by the IP retrieval process.

    Attributes:
        urls (list[str]): List of URLs used to retrieve the IP address.
    """

    urls: list[HttpUrl] = Field(
        default=[
            "https://ident.me",
            "https://api.ipify.org",
        ],
        serialization_alias="IPGET_URL_LIST",
        validation_alias="IPGET_URL_LIST",
    )
