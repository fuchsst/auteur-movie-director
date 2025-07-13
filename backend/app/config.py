"""
Application configuration using Pydantic settings.
Manages all environment variables and application settings.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "Auteur Movie Director API"
    version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    allowed_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # Workspace (mounted volume in container)
    workspace_root: Path = Field(default=Path("./workspace"), env="WORKSPACE_ROOT")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_progress_channel: str = "auteur:progress"
    redis_state_prefix: str = "auteur:project:"

    # WebSocket
    ws_heartbeat_interval: int = 30  # seconds
    ws_message_queue_size: int = 100

    # Quality Settings (aligned with generative pipeline)
    quality_presets: dict[str, dict] = {
        "low": {
            "pipeline_id": "auteur-flux:1.0-draft",
            "target_vram": 12,
            "steps": 10,
            "resolution": "512x512",
            "use_case": "rapid iteration and previz",
        },
        "standard": {
            "pipeline_id": "auteur-flux:1.0-standard",
            "target_vram": 16,
            "steps": 20,
            "resolution": "1024x1024",
            "use_case": "production quality",
        },
        "high": {
            "pipeline_id": "auteur-flux:1.0-cinematic",
            "target_vram": 24,
            "steps": 30,
            "resolution": "1920x1080",
            "use_case": "final renders",
        },
    }
    default_quality: str = "standard"

    # Task Dispatcher
    task_timeout: int = 300  # 5 minutes
    max_concurrent_tasks: int = 3

    # Future: Multi-agent settings
    enable_crew_ai: bool = False
    crew_orchestrator_url: str | None = None

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"

    # Container environment
    is_docker: bool = Field(default=False, env="DOCKER_ENV")
    container_name: str = "auteur-backend"

    # Git configuration
    git_author_name: str | None = Field(default=None, env="GIT_AUTHOR_NAME")
    git_author_email: str | None = Field(default=None, env="GIT_AUTHOR_EMAIL")
    git_lfs_threshold_mb: int = 50  # Files larger than this use LFS

    class Config:
        env_file = ".env"
        env_prefix = "BACKEND_"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
settings = Settings()
