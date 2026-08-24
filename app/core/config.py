from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        # Some managed Postgres providers (e.g. Render) hand out connection
        # strings prefixed `postgres://`, a scheme SQLAlchemy 2.0 rejects.
        if value.startswith("postgres://"):
            return "postgresql://" + value.removeprefix("postgres://")
        return value


settings = Settings()
