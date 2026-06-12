FROM ghcr.io/astral-sh/uv:0.8.22-python3.8-alpine AS dependencies
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.8-alpine AS build-image
COPY --from=dependencies /app/.venv /home/.venv
COPY speedtest-cli/ookla-speedtest-linux-x86_64/speedtest /usr/local/bin/speedtest
COPY influxspeedtest /home/influxspeedtest
COPY influxspeedtest.py /home/

ENV PATH="/home/.venv/bin:$PATH"

RUN chmod +x /usr/local/bin/speedtest

CMD [ "python", "-u", "/home/influxspeedtest.py" ]
