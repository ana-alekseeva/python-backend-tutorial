from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Nebius Token Factory is OpenAI-API compatible, so we use the OpenAI SDK.
    nebius_api_key: str  # required: the app refuses to start without it
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
