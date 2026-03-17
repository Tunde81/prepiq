from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    APP_NAME: str = "PrepIQ"
    APP_ENV: str = "development"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql://prepiq:changeme@db:5432/prepiq"
    REDIS_URL: str = "redis://:changeme@redis:6379/0"
    MONGO_URL: str = "mongodb://prepiq:changeme@mongo:27017/prepiq_events?authSource=admin"

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@prepiq.io"
    EMAILS_FROM_NAME: str = "PrepIQ"

    OPENAI_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAIL_FROM: str = "noreply@fa3tech.io"

    FIRST_SUPERADMIN_EMAIL: str = "admin@prepiq.io"
    FIRST_SUPERADMIN_PASSWORD: str = "Admin@PrepIQ1!"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **values):
        super().__init__(**values)
        # Parse CORS list if given as JSON string
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                self.BACKEND_CORS_ORIGINS = json.loads(self.BACKEND_CORS_ORIGINS)
            except Exception:
                self.BACKEND_CORS_ORIGINS = [self.BACKEND_CORS_ORIGINS]


settings = Settings()
