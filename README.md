# IPget Docker

![GitHub](https://img.shields.io/github/license/LunaPurpleSunshine/ipget?label=licence)
![Python](https://img.shields.io/github/pipenv/locked/python-version/LunaPurpleSunshine/ipget)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python Linting](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/python-lint.yml/badge.svg)](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/python-lint.yml)
[![Python Tests](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/python-tests.yml/badge.svg)](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/python-tests.yml)
[![CodeQL](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/codeql.yml/badge.svg)](https://github.com/LunaPurpleSunshine/ipget/actions/workflows/codeql.yml)
[![GitHub Release (Latest SemVer)](https://img.shields.io/github/v/release/LunaPurpleSunshine/ipget?sort=semver)](https://github.com/LunaPurpleSunshine/ipget-docker/releases)

## Table of Contents

- [IPget Docker](#ipget-docker)
  - [Table of Contents](#table-of-contents)
  - [About](#about)
  - [Configuration](#configuration)
    - [General](#general)
    - [Database](#database)
      - [MySQL](#mysql)
      - [PostgreSQL](#postgresql)
      - [SQLite](#sqlite)
    - [Healthchecks](#healthchecks)
    - [Discord Notifications](#discord-notifications)
  - [Licence](#licence)

## About

A simple, containerised Python script, that gets the system's current public IPv4 address using [ident.me](https://api.ident.me) and records it to a MySQL/SQLite database.
Optionally, sends a Discord notification via webhook, and pings [healthchecks.io](https://healthchecks.io/).

## Configuration

All configuration is done through environment variables. Most values are required, but some have default values that will be used if the environment variable is not specified.
Docker-compose files containing [SQLite](docs/sqlite-example-compose.yaml) and [MySQL](docs/mysql-example-compose.yaml) examples are available in the [docs](docs).

### General

| Environment Variable | Default | Description                                                                                                                                             |
| -------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IPGET_LOG_LEVEL`    | `INFO`  | Log level. Passed directly to the python logging module's [`Logger.setlevel`](https://docs.python.org/3.7/library/logging.html#logging.Logger.setLevel) |

>⚠️ **WARNING**:
Healthcheck urls (see [Healthchecks](#healthchecks)), including un-redacted uuids, etc. will be included in `DEBUG` level logging output.

### Database

| Environment Variable | Default | Description                                                                |
| -------------------- | ------- | -------------------------------------------------------------------------- |
| `IPGET_DB_TYPE`      | None    | Which database type to use. Must be one of `MySQL`, `SQLite`, `PostgreSQL` |

#### MySQL

| Environment Variable   | Default | Description                                  |
| ---------------------- | ------- | -------------------------------------------- |
| `IPGET_MYSQL_USERNAME` | None    | User to connect to the database              |
| `IPGET_MYSQL_PASSWORD` | None    | Password for the database user               |
| `IPGET_MYSQL_HOST`     | None    | Address of the database host e.g. ip_address |
| `IPGET_MYSQL_PORT`     | None    | Port for the database connection             |
| `IPGET_MYSQL_DATABASE` | None    | Name of the database e.g. public_ip_db       |

#### PostgreSQL

| Environment Variable        | Default | Description                                  |
| --------------------------- | ------- | -------------------------------------------- |
| `IPGET_POSTGRESQL_USERNAME` | None    | User to connect to the database              |
| `IPGET_POSTGRESQL_PASSWORD` | None    | Password for the database user               |
| `IPGET_POSTGRESQL_HOST`     | None    | Address of the database host e.g. ip_address |
| `IPGET_POSTGRESQL_PORT`     | None    | Port for the database connection             |
| `IPGET_POSTGRESQL_DATABASE` | None    | Name of the database e.g. public_ip_db       |

#### SQLite

It is generally not necessary to modify environment variable configuration for SQLite. These values are intended for use in development **only** e.g. setting the path to `:memory:`, for testing. When deploying the container, the path should be configured via docker volume mappings.

| Environment Variable    | Default             | Description                                                                                                                                                                                            |
| ----------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `IPGET_SQLITE_DATABASE` | `/app/public_ip.db` | Path to the sqlite database file **within the container**. This path should be mapped via Docker to a persistent location, if it is not, then the database file **will be lost** on container restart! |

### Healthchecks

| Environment Variable       | Default               | Description                                                                                                             |
| -------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `IPGET_HEALTHCHECK_SERVER` | `https://hc-ping.com` | Server to send pings to, default will use [healthchecks.io](https://healthchecks.io)                                    |
| `IPGET_HEALTHCHECK_UUID`   | None                  | Check UUID to ping. Slug based pings are not supported. If left unspecified, healthchecks integration will be disabled. |

### Discord Notifications

If a discord webhook is given, then notifications will be sent every time the detected IP address changes, or if the script encounters errors.

![Example discord notifications](docs/images/notifications.jpg "Example discord notifications")

| Environment Variable    | Default | Description                                                                                            |
| ----------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `IPGET_DISCORD_WEBHOOK` | None    | Discord webhook to use for notifications. If left unspecified, Discord notifications will be disabled. |

## Licence

[MIT](LICENCE.txt)
