from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    UPLOAD_DIR: Path = Path("uploads")
    EXTRACT_DIR: Path = Path("extracted")
    MAX_UPLOAD_SIZE_MB: int = 50

    IGNORED_DIRS: set = {
        ".git", "node_modules", ".venv", "venv", "__pycache__",
        "dist", "build", ".next", ".cache", "logs", "data",
        "uploads", "tmp", ".pytest_cache",
    }

    SENIOR_CHECK_THRESHOLD: int = 85
    PASS_THRESHOLD: int = 70
    CONDITIONAL_PASS_THRESHOLD: int = 50

    MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    LLM_REVIEW_ENABLED: bool = False
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: int = 20
    LLM_DEFAULT_MODEL: str = "gpt-4o-mini"

    STUDENT_REVIEW_MODEL: str = ""
    GITHUB_REVIEW_MODEL: str = ""
    INTERVIEW_REVIEW_MODEL: str = ""
    COMMERCIAL_REVIEW_MODEL: str = ""

    ROOT_DIR: Path = PROJECT_ROOT

    LLM_GUARD_ENABLED: bool = False
    LLM_GUARD_BLOCK_ON_HIGH_RISK: bool = True

    METRICS_ENABLED: bool = True

    MCP_ENABLED: bool = False
    MCP_SAFE_UPLOAD_DIR: str = "examples"
    MCP_MAX_ZIP_MB: int = 50


settings = Settings()
