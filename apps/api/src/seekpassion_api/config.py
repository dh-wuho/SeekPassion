from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/ — the package root, not the process's CWD. A CWD-relative
# default (e.g. "sqlite:///./dev.db") silently points to a different,
# empty database depending on where a command is run from.
_API_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE_PATH = _API_ROOT / "dev.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEEKPASSION_")

    database_url: str = f"sqlite:///{_DEFAULT_SQLITE_PATH}"


settings = Settings()
