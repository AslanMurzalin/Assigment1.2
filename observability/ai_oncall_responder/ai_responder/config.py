from pydantic_settings import BaseSettings, SettingsConfigDict

class AIResponderSettings(BaseSettings):
    PROJECT_NAME: str = "Link Saver AI On-Call Responder"
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "production"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Prometheus / Grafana / Service endpoints to query for more incident context
    PROMETHEUS_URL: str = "http://prometheus:9090"
    JAEGER_URL: str = "http://jaeger:16686"
    APP_BASE_URL: str = "http://linksaver-app:8000"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=(".env", "../.env", "../../.env"),
        extra="ignore",
    )

settings = AIResponderSettings()
