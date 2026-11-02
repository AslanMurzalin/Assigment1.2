from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine, Base
import app.models  # Ensure all models are registered with Base metadata
from app.api.v1.auth import router as auth_router
from app.api.v1.links import router as links_router
from app.api.v1.downloads import router as downloads_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup
    Base.metadata.create_all(bind=engine)
    # Check and add any missing columns in links table for SQLite
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(links)"))
            existing_cols = {row[1] for row in result.fetchall()}
            if "image_url" not in existing_cols:
                conn.execute(text("ALTER TABLE links ADD COLUMN image_url VARCHAR"))
            if "price" not in existing_cols:
                conn.execute(text("ALTER TABLE links ADD COLUMN price VARCHAR"))
            if "specs" not in existing_cols:
                conn.execute(text("ALTER TABLE links ADD COLUMN specs TEXT"))
            conn.commit()
        except Exception:
            pass
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Link Saver backend API (FastAPI + SQLite M:N + Direct Streaming)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Disposition", "X-Estimated-Content-Length"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(links_router, prefix=settings.API_V1_STR)
app.include_router(downloads_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

# Mount static frontend build if directory exists (Single-Container Production Setup)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Allow API, docs, and OpenAPI routes to be handled by FastAPI
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path == "health"
        ):
            return {"detail": "Not Found"}
        target_file = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"detail": "Static frontend not found"}

