from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    PROJECT_NAME: str
    API_VERSION: str
    ENVIRONMENT: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()