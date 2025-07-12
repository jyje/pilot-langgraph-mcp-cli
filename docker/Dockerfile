# Builder Stage
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --frozen
RUN uv build

# Runtime Stage
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app
COPY --from=builder /app/dist/*.whl ./
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN pip install --no-cache-dir *.whl && rm -f *.whl
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import my_mcp.cli; print('OK')" || exit 1

ENTRYPOINT ["my-mcp"]
CMD ["--help"]
