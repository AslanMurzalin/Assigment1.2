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
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY backend/app ./app

# Copy built static frontend into FastAPI static assets directory
COPY --from=frontend-builder /app/frontend/dist ./app/static

# Persistent SQLite directory configuration
RUN mkdir -p /app/data
ENV DATABASE_URL="sqlite:////app/data/app.db"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

