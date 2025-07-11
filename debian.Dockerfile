# Some parts of this dockerfile are based on the example uv Python Dockerfile found at
# https://hynek.me/articles/docker-uv/ (retrieved 2024-10-14)

FROM debian:bookworm-slim@sha256:90522eeb7e5923ee2b871c639059537b30521272f10ca86fdbbbb2b75a8c40cd AS base

# Install updates
RUN  apt-get update -qy && apt-get install -qyy

FROM base AS python-deps
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:4faec156e35a5f345d57804d8858c6ba1cf6352ce5f4bffc11b7fdebdef46a38 /uv /usr/local/bin/uv
# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
# - and finally declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Since there's no point in shipping lock files, we move them
# into a directory that is NOT copied into the runtime image.
# The trailing slash makes COPY create `/_lock/` automagically.
COPY pyproject.toml /_lock/
COPY uv.lock /_lock/

# RUN uv python install cp3.12

# Synchronize DEPENDENCIES without the application itself.
RUN --mount=type=cache,target=/root/.cache  cd /_lock && \
    uv sync --locked --no-dev --no-install-project

FROM base AS runtime

RUN apt-get update -qq && \
    apt-get install -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Setup env
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
# Fix logging output
ENV PYTHONUNBUFFERED=1

# Copy virtual env from python-deps stage
COPY --from=python-deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install application into container
COPY ./src /app

# Don't run your app as root.
RUN groupadd -r app && useradd -r -d /app -g app -N app
USER app
WORKDIR /app

# Run the application
ENTRYPOINT ["python", "/home/appuser/app/app.py"]
# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT
