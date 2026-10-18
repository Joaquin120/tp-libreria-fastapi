from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/libreria_db"
    db_echo: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def DB_ECHO(self) -> bool:
        return self.db_echo


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
