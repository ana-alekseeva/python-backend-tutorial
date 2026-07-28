from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Two files: .env is ordinary configuration, .env.secrets holds the credentials.
    # Later files win, so a secret can never be shadowed by the config file.
    model_config = SettingsConfigDict(env_file=(".env", ".env.secrets"), extra="ignore")

    # Nebius Token Factory is OpenAI-API compatible, so we use the OpenAI SDK.
    nebius_api_key: str  # required: the app refuses to start without it
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"

    # Signs the session cookie. Rotating it logs everyone out.
    session_secret: str
    session_max_age_s: int = 60 * 60 * 24 * 7  # a week
    # False only for local development over plain http.
    cookie_secure: bool = True

    # Stands in for a users table: one account, from the environment.
    auth_username: str = "demo"
    auth_password: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
