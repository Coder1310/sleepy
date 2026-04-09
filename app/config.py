from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  bot_token: str
  database_url: str = "sqlite+aiosqlite:///./sleep_bot.db"
  default_timezone: str = "Europe/Moscow"

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
  )


settings = Settings()
