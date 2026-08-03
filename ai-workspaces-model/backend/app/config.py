from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Workspaces Model")
    database_path: str = os.getenv("DATABASE_PATH", "data/ai_workspaces.db")
    api_token: str = os.getenv("API_TOKEN", "dev-token-change-me")
    cors_origins: tuple[str, ...] = tuple(filter(None, os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")))
    environment: str = os.getenv("ENVIRONMENT", "development")

settings = Settings()
