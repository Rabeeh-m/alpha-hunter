FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app/ app/
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
