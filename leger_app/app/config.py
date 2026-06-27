from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./subledger.db"
    test_database_url: str = "sqlite:///./test.db"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"


settings = Settings()
