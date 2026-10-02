from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WasteHub API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg://wastehub:wastehub_dev_password"
        "@localhost:5432/wastehub"
    )

    secret_key: str = "change-this-development-secret"
    access_token_expire_minutes: int = 30
    media_root: str = "media"
    payment_provider: str = "demo"

    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()