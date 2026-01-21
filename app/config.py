from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # En local podés usar .env, en Railway no existe (y no debe ser requisito)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    DATABASE_URL: str
    JWT_SECRET: str

    # defaults seguros
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 60 * 24 * 30  # 30 días


settings = Settings()

