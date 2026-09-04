from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """MemResolveAI application configuration.

    Local development reads values from the .env file.

    On GCP, the same settings are supplied through Cloud Run or
    Agent Runtime environment variables.
    """

    # Google Cloud and Gemini
    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: bool = True

    # MemResolveAI
    mem_resolve_model: str = "gemini-2.5-flash"
    mem_resolve_environment: str = "local"

    # Structured operational data
    data_backend: str = "firestore"
    firestore_database: str = "(default)"

    # Policy knowledge/RAG
    knowledge_backend: str = "chroma"
    chroma_persist_directory: str = "data/chroma"
    chroma_collection: str = "memresolve-policies"

    # MCP transport
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8001
    mcp_url: str = "http://127.0.0.1:8001/mcp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def chroma_directory(self) -> Path:
        """Return the absolute Chroma persistence directory."""
        configured_directory = Path(
            self.chroma_persist_directory
        )

        if configured_directory.is_absolute():
            return configured_directory

        return PROJECT_ROOT / configured_directory

    @property
    def use_local_mcp(self) -> bool:
        """Return True when MCP uses the local STDIO transport."""
        return self.mcp_transport.strip().lower() == "stdio"

    @property
    def use_http_mcp(self) -> bool:
        """Return True when MCP uses Streamable HTTP."""
        return (
            self.mcp_transport.strip().lower()
            == "streamable-http"
        )


@lru_cache
def get_settings() -> Settings:
    """Load and cache the application configuration."""
    return Settings()