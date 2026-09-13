from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mediagnotek"
    APP_NAME: str = "Mediagnotek API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    RXNAV_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"

    @property
    def async_database_url(self) -> str:
        """Konversi URL ke format asyncpg jika perlu."""
        url = self.DATABASE_URL
        # Neon / Render menggunakan postgresql://, asyncpg butuh postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
