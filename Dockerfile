FROM python:3.11-slim-bookworm

ARG SOURCE_COMMIT=unknown
LABEL org.opencontainers.image.revision=$SOURCE_COMMIT
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_COMMIT=$SOURCE_COMMIT

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home app

COPY statuswatch/ statuswatch/
USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/live', timeout=2).close()"

CMD ["sh", "-c", "flask --app statuswatch:create_app init-db && exec gunicorn --bind 0.0.0.0:8000 --workers 1 --timeout 120 'statuswatch:create_app()'"]
