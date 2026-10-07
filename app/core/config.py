import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Invoice Automation Platform"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "SecurePass2026")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ap_automation_db")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # URL for the automation webhook (e.g. Make, Zapier, n8n)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "https://hook.us1.make.com/xxxxxxxxx")

    class Config:
        env_file = ".env"


settings = Settings()
