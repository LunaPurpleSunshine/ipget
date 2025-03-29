# Some parts of this dockerfile are based on the example uv Python Dockerfile found at
# https://hynek.me/articles/docker-uv/ (retrieved 2024-10-14)

FROM python:3.13-alpine AS base

# Setup env
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

# Install updates
RUN apk update && apk upgrade --no-cache

FROM base AS python-deps
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:57da96c4557243fc0a732817854084e81af9393f64dc7d172f39c16465b5e2ba /uv /usr/local/bin/uv
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

# Synchronize DEPENDENCIES without the application itself.
RUN --mount=type=cache,target=/root/.cache  cd /_lock && \
    uv sync --locked --no-dev --no-install-project

FROM base AS runtime

# Fix logging output
ENV PYTHONUNBUFFERED=1

# Copy virtual env from python-deps stage
COPY --from=python-deps /app/.venv /home/appuser/.venv
ENV PATH="/home/appuser/.venv/bin:$PATH"

# Create and switch to a new user
# THIS BREAKS LOGGING with permissions errors writing the log file
# alpine
# RUN adduser -D -u 5000 appuser
# WORKDIR /home/appuser
# USER appuser

# Install application into container
COPY ./src /home/appuser/app

# Run the application
ENTRYPOINT ["python", "/home/appuser/app/app.py"]
# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT
