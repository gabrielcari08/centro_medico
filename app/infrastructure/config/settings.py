from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Credenciales del administrador pre-provisionado via .env
    NAME: str
    PASSWORD: str
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/app_db"
    SECRET_KEY: str = "dev-secret-key-change-in-prod"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
