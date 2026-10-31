import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "Pandu@18052000"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "university_ranking_db"
    DATABASE_URL: Optional[str] = None

    # Read-Only Database Configuration
    POSTGRES_READONLY_USER: str = "ranking_readonly"
    POSTGRES_READONLY_PASSWORD: str = "ReadOnly@Ranking2026"
    READONLY_DATABASE_URL: Optional[str] = None

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "university-ranking-analytics"

    # Application Settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        from urllib.parse import quote_plus
        escaped_password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{escaped_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_readonly_database_url(self) -> str:
        if self.READONLY_DATABASE_URL:
            return self.READONLY_DATABASE_URL
        from urllib.parse import quote_plus
        escaped_password = quote_plus(self.POSTGRES_READONLY_PASSWORD)
        return f"postgresql+psycopg2://{self.POSTGRES_READONLY_USER}:{escaped_password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
