import logging
from abc import ABC, abstractmethod
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from ipaddress import ip_address as IPAddress
from os import environ
from pathlib import Path

import sqlalchemy as db
from sqlalchemy import String
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

from ipget.errors import ConfigurationError

log = logging.getLogger(__name__)

Base = declarative_base()

TABLE_NAME = "public_ip_address"


class IPInfo(Base):
    """Represents IP information stored in the database table."""

    __tablename__ = TABLE_NAME

    ID: Mapped[int] = mapped_column(
        primary_key=True, nullable=False, autoincrement=True
    )
    time: Mapped[datetime] = mapped_column(nullable=False)
    ip_address: Mapped[str] = mapped_column(String(80), nullable=True)


class AlchemyDB(ABC):
    """Abstract base class for interacting with the database using SQLAlchemy."""

    def __init__(self) -> None:
        """Initialise AlchemyDB, creating the necessary table."""
        self.table_name: str = TABLE_NAME
        self.database_name: str
        self.created_new_table: bool = False
        self.engine: db.Engine = self.create_engine()
        self.create_table()

    @abstractmethod
    def create_engine(self) -> db.Engine:
        """Create and return the SQLAlchemy engine.

        Returns:
            sqlalchemy.engine object.
        """

    def write_data(self, datetime: datetime, ip: IPv4Address | IPv6Address) -> int:
        """Write the IP information to the database.

        Args:
            datetime (dt.datetime): The timestamp the IP was retrieved.
            ip (str): The IP address to be stored.

        Returns:
            int: The ID of the newly inserted row.
        """
        values = IPInfo(time=datetime, ip_address=str(ip))
        log.info(f"Adding row to table '{self.table_name}' in '{self.database_name}'")
        return self.commit_row(values)

    def create_table(self):
        """Create the database table, if it does not exist."""
        if not db.inspect(self.engine).has_table(self.table_name):
            log.info(f"Table '{self.table_name}' does not exist, creating")
            self.created_new_table = True
            Base.metadata.create_all(self.engine)

    def commit_row(self, values: IPInfo) -> int:
        """Commit the IP information to the database.

        Args:
            values (IPInfo): The IPInfo object to be committed.

        Returns:
            int: The ID of the newly inserted row.
        """
        log.debug("Creating session")
        with Session(self.engine) as session:
            with session.begin():
                log.debug("Session started, adding data")
                session.add(values)
                log.debug("Committing changes")
                session.commit()
            session.refresh(values)
            new_row_ID = values.ID
            log.info(f"Committed new row to database with ID {new_row_ID}")
        return new_row_ID

    def get_last(self) -> tuple[int, datetime, IPv4Address | IPv6Address] | None:
        """Retrieve the most recent IP information from the database.

        Returns:
            tuple[int, datetime, IPv4Address | IPv6Address | None]: A tuple containing
            the ID, timestamp, and IP address of the most recent entry, or
            'None', if no entry is found.
        """
        log.debug("Retrieving most recent IP from database")
        with Session(self.engine) as session:
            with session.begin():
                log.debug("Session started, fetching data")
                q = db.select(IPInfo).order_by(IPInfo.time.desc()).limit(1)
                result = session.scalars(q).first()
                return (
                    None
                    if result is None
                    else (result.ID, result.time, IPAddress(result.ip_address))
                )


class MySQL(AlchemyDB):
    """Concrete class for interacting with a MySQL database."""

    def __init__(self) -> None:
        """Initialize MySQL using valuse from config."""
        self._load_config()
        super().__init__()
        self.database_name = f"{self._database} on {self._host}:{self._port}"

    def _load_config(self):
        """Load MySQL configuration values from environment variables.

        Raises:
            ConfigurationError: If any required setting is missing.
        """
        self._username: str | None = environ.get("IPGET_MYSQL_USERNAME")
        self._password: str | None = environ.get("IPGET_MYSQL_PASSWORD")
        self._host: str | None = environ.get("IPGET_MYSQL_HOST")
        self._port: int | None = (
            int(port) if (port := environ.get("IPGET_MYSQL_PORT")) else None
        )
        self._database: str | None = environ.get("IPGET_MYSQL_DATABASE")
        required_settings = [
            (self._username, "IPGET_MYSQL_USERNAME"),
            (self._password, "IPGET_MYSQL_PASSWORD"),
            (self._host, "IPGET_MYSQL_HOST"),
            (self._port, "IPGET_MYSQL_PORT"),
            (self._database, "IPGET_MYSQL_DATABASE"),
        ]
        if missing_settings := [e for k, e in required_settings if not k]:
            raise ConfigurationError(", ".join(missing_settings))

    def create_engine(self) -> db.Engine:
        """Create and return the SQLAlchemy engine for MySQL.

        Returns:
            sqlalchemy.engine: The SQLAlchemy engine object.
        """
        log.debug("Creating database engine")
        dialect = "mysql+pymysql"
        user_pass = f"{self._username}:{self._password}"
        host = f"{self._host}:{self._port}"
        database = self._database
        url = f"{dialect}://{user_pass}@{host}/{database}"
        return db.create_engine(url)


class SQLite(AlchemyDB):
    """Concrete class for interacting with an SQLite database."""

    def __init__(self) -> None:
        """Initialize SQLite using valuse from config."""
        self._load_config()
        super().__init__()
        self.database_name = f"{self._path.name}"

    def _load_config(self):
        """Load SQLite file path from environment variable."""
        self._path: Path = Path(
            environ.get("IPGET_SQLITE_DATABASE", "/app/public_ip.db")
        )

    def create_engine(self) -> db.Engine:
        """Create and return the SQLAlchemy engine for SQLite.

        Returns:
            sqlalchemy.engine: The SQLAlchemy engine object.
        """
        log.debug("Creating database engine")
        log.debug(f"CWD: {Path.cwd()}")
        dialect = "sqlite"
        database = str(self._path)
        url = f"{dialect}:///{database}"
        log.debug(f"SQLAlchemy url: '{url}'")
        return db.create_engine(url)


def get_database(type: str = environ.get("IPGET_DB_TYPE", "")) -> AlchemyDB:
    """Get the database instance based on the provided type.

    Args:
        type (str): The type of database.
        Defaults to the value of IPGET_DB_TYPE environment variable.

    Returns:
        AlchemyDB: An instance of the AlchemyDB or its derived classes.

    Raises:
        ConfigurationError: If the provided database type is not supported
        or if any required configuration setting is missing.
    """
    log.debug(f"Requested database type is '{type.lower()}'")
    try:
        match type.lower():
            case "mysql":
                return MySQL()
            case "sqlite":
                return SQLite()
            case _:
                raise ConfigurationError("IPGET_DB_TYPE")
    except ConfigurationError as e:
        log.exception(e)
        raise e
