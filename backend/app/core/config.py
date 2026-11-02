from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Link Saver API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "link-saver-super-secret-key-for-development-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/linksaver"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    RENDER_EXTERNAL_URL: str = ""  # Auto-set by Render (e.g. https://linksaver-app.onrender.com)

    BHAPI_TOKEN: str = ""
    BHAPI_BASE_URL: str = "https://bhapi.ru"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(".env", "backend/.env", "../.env"),
        extra="ignore",
    )

settings = Settings()
