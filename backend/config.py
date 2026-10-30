import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    GROQ_API_KEY: Optional[str] = ""
    ELEVENLABS_API_KEY: Optional[str] = ""
    ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    TELEGRAM_BOT_TOKEN: Optional[str] = ""
    TELEGRAM_CHAT_ID: Optional[str] = ""
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./voxera.db"

    # Phase 3: Ollama local fallback LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Phase 3: Provider health flags (refreshed on /api/health)
    ELEVENLABS_TIMEOUT_SEC: float = 10.0
    GROQ_TIMEOUT_SEC: float = 20.0

    # Phase 4: Local STT via faster-whisper
    WHISPER_MODEL_SIZE: str = "base"
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY.strip() and not self.GROQ_API_KEY.startswith("your_"))

    @property
    def has_elevenlabs(self) -> bool:
        return bool(self.ELEVENLABS_API_KEY and self.ELEVENLABS_API_KEY.strip() and not self.ELEVENLABS_API_KEY.startswith("your_"))

    @property
    def has_telegram(self) -> bool:
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_BOT_TOKEN.strip() and not self.TELEGRAM_BOT_TOKEN.startswith("your_"))

settings = Settings()
