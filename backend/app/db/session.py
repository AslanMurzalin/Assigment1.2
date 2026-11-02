import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Ensure parent directory exists if using a file path in SQLite URL
if SQLALCHEMY_DATABASE_URL.startswith("sqlite:////"):
    db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:////", "/")
    os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
    db_file_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_file_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(links)"))
            existing_cols = {row[1] for row in result.fetchall()}
            if existing_cols:
                if "image_url" not in existing_cols:
                    conn.execute(text("ALTER TABLE links ADD COLUMN image_url VARCHAR"))
                if "price" not in existing_cols:
                    conn.execute(text("ALTER TABLE links ADD COLUMN price VARCHAR"))
                if "specs" not in existing_cols:
                    conn.execute(text("ALTER TABLE links ADD COLUMN specs TEXT"))
                conn.commit()
        except Exception:
            pass

init_db()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
