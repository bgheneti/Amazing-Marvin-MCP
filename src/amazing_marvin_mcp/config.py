import logging

from pydantic import Field
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration settings for the Amazing Marvin MCP"""

    # API settings
    amazing_marvin_api_key: str = Field(..., env="AMAZING_MARVIN_API_KEY")
    # Optional: only needed for tools that read/update arbitrary documents
    # (e.g. update_subtasks). Found next to the API token in Marvin's API strategy.
    amazing_marvin_full_access_token: str | None = Field(
        default=None, env="AMAZING_MARVIN_FULL_ACCESS_TOKEN"
    )

    # Server settings
    port: int = Field(default=3000, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")

    # FastMCP settings
    max_context_size: int = Field(default=8192, env="MAX_CONTEXT_SIZE")
    max_request_size: int = Field(default=32768, env="MAX_REQUEST_SIZE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get configuration settings with environment variable validation"""
    try:
        return Settings()
    except Exception:
        logger.exception("Configuration error")
        raise
