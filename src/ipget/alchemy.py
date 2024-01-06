import logging
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from ipaddress import ip_address as IPAddress
from pathlib import Path

import sqlalchemy as db
from sqlalchemy import URL, String
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

from ipget.errors import ConfigurationError
from ipget.settings import GenericDatabaseSettings, SQLiteDatabaseSettings

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


class AlchemyDB:
    """Abstract base class for interacting with the database using SQLAlchemy."""

    def __init__(self) -> None:
        """Initialise AlchemyDB, creating the necessary table."""
        self.table_name: str = TABLE_NAME
        self.created_new_table: bool = False
        self.dialect: str  # This attribute is given by sub-classes
        self.engine: db.Engine = self.create_engine()
        self.create_table()

    def _load_settings(self, settings: GenericDatabaseSettings):
        """Load MySQL/PostgreSQL configuration values from environment variables,
        using `pydantic-settings` .

        Raises:
            ConfigurationError: If any required setting is missing.
        """

        self.username: str | None = settings.username
        self.password: str | None = settings.password
        self.host: str | None = settings.host
        self.port: int | None = settings.port
        self.database: str | None = settings.database_name

        if missing_settings := [
            k for k, v in settings.model_dump(by_alias=True).items() if not v
        ]:
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

    def __init__(self, settings: SQLiteDatabaseSettings | None = None) -> None:
        """Initialize SQLite using valuse from config."""
        self.dialect: str = "sqlite"
        if not settings:
            settings = SQLiteDatabaseSettings()
        self._load_settings(settings)
        super().__init__()

    def _load_settings(self, settings: SQLiteDatabaseSettings):
        """Load SQLite file path from environment variable."""
        self.database_path: Path = settings.database_file_path

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

    def __init__(self, settings: GenericDatabaseSettings | None = None) -> None:
        """Initialize MySQL using valuse from config."""
        self.dialect: str = "mysql+pymysql"
        if not settings:
            settings = GenericDatabaseSettings()
        self._load_settings(settings)
        super().__init__()


class PostgreSQL(AlchemyDB):
    """Concrete class for interacting with a PostgreSQL database."""

    def __init__(self, settings: GenericDatabaseSettings | None = None) -> None:
        """Initialize PostgreSQL using valuse from config."""
        self.dialect = "postgresql+pg8000"
        if not settings:
            settings = GenericDatabaseSettings()
        self._load_settings(settings)
        super().__init__()


def get_database(mode: str) -> AlchemyDB:
    """Get the database instance based on the provided mode.

    Args:
        mode (str): The mode of database.
        Defaults to `sqlite`.

    Returns:
        AlchemyDB: An instance of the AlchemyDB or its derived classes.

    Raises:
        ConfigurationError: If the provided database mode is not supported
        or if any required configuration setting is missing.
    """
    log.debug(f"Requested database mode is '{mode.lower()}'")
    try:
        match mode.lower():
            case "sqlite":
                return SQLite()
            case "mysql" | "mariadb":
                return MySQL()
            case "postgres" | "postgresql":
                return PostgreSQL()
            case _:
                raise ConfigurationError("IPGET_DB_TYPE")
    except ConfigurationError as e:
        log.exception(e)
        raise e
