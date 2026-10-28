import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "mediagnotek.db"

class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    APP_NAME: str = "Mediagnotek API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    RXNAV_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"
    
    # AI API Keys (Ambil dari .env untuk keamanan)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    JWT_SECRET: str = "mediagnotek_jwt_secret_key_2026"

    @property
    def async_database_url(self) -> str:
        """Konversi URL ke format async yang sesuai (sqlite atau psycopg)."""
        url = self.DATABASE_URL
        if url.startswith("sqlite:///") and "+aiosqlite" not in url:
            return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif url.startswith("sqlite://") and "+aiosqlite" not in url:
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        # Neon/Render menggunakan postgresql:// atau postgres://
        if url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif "+asyncpg" in url:
            url = url.replace("+asyncpg", "+psycopg")
        return url

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
