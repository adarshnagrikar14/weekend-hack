from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - app still boots before deps install.
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "OrchestrateAI"
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    gemini_live_model: str = os.getenv(
        "GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview"
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ngrok_url: str = os.getenv("NGROK_URL", "")
    database_path: Path = INSTANCE_DIR / "orchestrateai.sqlite3"
    auth_secret: str = os.getenv("AUTH_SECRET", "change-this-in-env")
    auth_algorithm: str = "HS256"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
