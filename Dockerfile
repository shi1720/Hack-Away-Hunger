FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 pantry
COPY backend/ ./backend/
COPY scripts/backup.py scripts/account_admin.py scripts/healthcheck.py ./scripts/
COPY --from=frontend /build/dist ./frontend/dist/
RUN mkdir -p /app/data && chown -R pantry:pantry /app
USER pantry
ENV PANTRY_DATABASE=/app/data/pantry-relay.sqlite3
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python scripts/healthcheck.py
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
