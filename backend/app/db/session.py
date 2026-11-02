import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQLite path handling if running in SQLite mode
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
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
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
