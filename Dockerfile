FROM python:3.12-alpine as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# Install updates
RUN apk update && apk upgrade --no-cache

FROM base as python-deps

# Install python deps into venv
ENV VIRTUAL_ENV=/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt .
RUN --mount=type=cache,target=~/.cache/pip \
    pip install -r requirements.txt

FROM base as runtime

# Fix logging output
ENV PYTHONUNBUFFERED=1

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

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
