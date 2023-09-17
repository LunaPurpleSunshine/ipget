import logging
from abc import ABC
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from ipaddress import ip_address as IPAddress
from os import environ
from pathlib import Path

import sqlalchemy as db
from sqlalchemy import URL, String
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
        self.created_new_table: bool = False
        self.dialect: str  # This attribute is given by sub-classes
        self.engine: db.Engine = self.create_engine()
        self.create_table()

    def _load_config_from_environment(self):
        """Load MySQL/PostgreSQL configuration values from environment variables.

        Raises:
            ConfigurationError: If any required setting is missing.
        """
        self.username: str | None = environ.get("IPGET_USERNAME")
        self.password: str | None = environ.get("IPGET_PASSWORD")
        self.host: str | None = environ.get("IPGET_HOST")
        self.port: int | None = (
            int(port) if (port := environ.get("IPGET_PORT")) else None
        )
        self.database: str | None = environ.get("IPGET_DATABASE")
        required_settings = [
            (self.username, "IPGET_USERNAME"),
            (self.password, "IPGET_PASSWORD"),
            (self.host, "IPGET_HOST"),
            (self.port, "IPGET_PORT"),
            (self.database, "IPGET_DATABASE"),
        ]
        if missing_settings := [e for k, e in required_settings if not k]:
            raise ConfigurationError(missing_env_var=", ".join(missing_settings))

    def create_engine(self) -> db.Engine:
        """Create and return the SQLAlchemy engine.

        Returns:
            sqlalchemy.engine: The SQLAlchemy engine object.
        """
        log.debug("Creating database engine")
        url = URL.create(
            drivername=self.dialect,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
        log.debug(f"SQLAlchemy {url=}")
        return db.create_engine(url)

    def write_data(self, datetime: datetime, ip: IPv4Address | IPv6Address) -> int:
        """Write the IP information to the database.

        Args:
            datetime (dt.datetime): The timestamp the IP was retrieved.
            ip (str): The IP address to be stored.

        Returns:
            int: The ID of the newly inserted row.
        """
        values = IPInfo(time=datetime, ip_address=str(ip))
        log.info(f"Adding row to table '{self.table_name}' in '{self}'")
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

    def __str__(self) -> str:
        return f"{self.table_name} in {self.database} on {self.host}:{self.port}"


class SQLite(AlchemyDB):
    """Concrete class for interacting with an SQLite database.

    Note: SQLite is very different to other supported databases,
    this means it is necessary to override inherited methods.
    """

    def __init__(self) -> None:
        """Initialize SQLite using valuse from config."""
        self.dialect: str = "sqlite"
        self._load_config_from_environment()
        super().__init__()

    def _load_config_from_environment(self):
        """Load SQLite file path from environment variable."""
        self.database_path: Path = Path(
            environ.get("IPGET_DATABASE", "/app/public_ip.db")
        )

    def create_engine(self) -> db.Engine:
        """Create and return the SQLAlchemy engine for SQLite.

        Returns:
            sqlalchemy.engine: The SQLAlchemy engine object.
        """
        log.debug("Creating database engine")
        log.debug(f"CWD: {Path.cwd()}")
        # url = f"{self.dialect}:///{self.database_path}"
        url = URL.create(drivername=self.dialect, database=str(self.database_path))
        log.debug(f"SQLAlchemy {url=}")
        return db.create_engine(url)

    def __str__(self) -> str:
        return f"{self.table_name} in {self.database_path}"


class MySQL(AlchemyDB):
    """Concrete class for interacting with a MySQL database."""

    def __init__(self) -> None:
        """Initialize MySQL using valuse from config."""
        self.dialect: str = "mysql+pymysql"
        self._load_config_from_environment()
        super().__init__()


class PostgreSQL(AlchemyDB):
    """Concrete class for interacting with a PostgreSQL database."""

    def __init__(self) -> None:
        """Initialize PostgreSQL using valuse from config."""
        self.dialect = "postgresql+pg8000"
        self._load_config_from_environment()
        super().__init__()


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
            case "postgres" | "postgresql":
                return PostgreSQL()
            case _:
                raise ConfigurationError("IPGET_DB_TYPE")
    except ConfigurationError as e:
        log.exception(e)
        raise e
