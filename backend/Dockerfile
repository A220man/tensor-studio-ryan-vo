FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER 65532:65532

FROM base AS deps
COPY --chown=65532:65532 --from=base /usr/local/bin/python /usr/local/bin/python
RUN pip install --no-cache-dir --upgrade pip
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY --chown=65532:65532 backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=deps /app/.venv /app/.venv
COPY --chown=65532:65532 backend/app ./app
COPY --chown=65532:65532 backend/requirements.txt .

RUN mkdir -p /app/data && chown 65532:65532 /app/data

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]