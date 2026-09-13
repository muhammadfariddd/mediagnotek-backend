from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mediagnotek"
    APP_NAME: str = "Mediagnotek API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    RXNAV_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"

    @property
    def async_database_url(self) -> str:
        """Konversi URL ke format psycopg async."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        # Jika sudah asyncpg, ganti ke psycopg
        if "+asyncpg" in url:
            url = url.replace("+asyncpg", "+psycopg")
        return url

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
