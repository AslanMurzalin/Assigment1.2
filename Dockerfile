# ===================================================
# Stage 1: Build React Frontend as Static SPA
# ===================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ENV VITE_API_URL=""
RUN npm run build

# ===================================================
# Stage 2: Unified Backend + Static Frontend Image
# ===================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies:
# - ffmpeg: audio/video muxing
# - nodejs: JS runtime for yt-dlp
# - libpq-dev / gcc if needed, or psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend application source code & Alembic migration files
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini

# Copy built static frontend into FastAPI static assets directory
COPY --from=frontend-builder /app/frontend/dist ./app/static

ENV DATABASE_URL="postgresql+psycopg2://postgres:postgres@db:5432/linksaver"

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
