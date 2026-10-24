from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Vercel/Neon expose DATABASE_URL (postgres://...). Optional so the API
    # still runs simulations when no database is configured.
    database_url: str | None = None
    max_qubits: int = 12
    max_shots: int = 10_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
