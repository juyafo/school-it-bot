from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    admin_ids: list[int] = []

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()