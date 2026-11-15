FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir . -r backend/requirements.txt \
    && useradd --uid 10001 --create-home app \
    && mkdir /var/lib/agrosphere && chown app:app /var/lib/agrosphere \
    && chmod 700 /var/lib/agrosphere
COPY backend/app/ backend/app/
COPY backend/services/ backend/services/
COPY data/ data/
COPY deploy/staging/backup_sqlite.py /app/backup_sqlite.py
USER 10001:10001
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/ready', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
