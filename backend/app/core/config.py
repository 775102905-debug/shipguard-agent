from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
