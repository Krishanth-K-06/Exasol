from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Exasol FastAPI Application"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Exasol Database Configuration
    EXASOL_HOST: str = "127.0.0.1"
    EXASOL_PORT: int = 8563
    EXASOL_USER: str = "sys"
    EXASOL_PASSWORD: str = "exasol"
    EXASOL_SCHEMA: Optional[str] = None  # e.g., "STARTER_KIT", "TPCH", or None
    EXASOL_ENCRYPTION: bool = True
    EXASOL_VALIDATE_CERT: bool = False  # False for local Exasol Personal self-signed cert
    EXASOL_CONNECTION_TIMEOUT: int = 30
    EXASOL_SOCKET_TIMEOUT: int = 60

    POSTGRES_URL: str = "postgresql+psycopg://incident:mock-postgres-password@127.0.0.1:5432/incidents"
    QDRANT_URL: str = "http://127.0.0.1:6333"
    QDRANT_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    DATA_ROOT: str = "/Users/admin/Downloads/autonomous_data_incident_platform"
    LOCAL_STATE_DIR: str = ".local-state"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @computed_field
    @property
    def EXASOL_DSN(self) -> str:
        """
        Exasol DSN format: <host>:<port>
        """
        return f"{self.EXASOL_HOST}:{self.EXASOL_PORT}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
