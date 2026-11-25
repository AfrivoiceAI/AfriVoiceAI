from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AfriVoice AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "afrivoice"
    jwt_secret: str = "development-only-change-this"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173"
    ai_mode: Literal["demo", "local", "gateway"] = "demo"
    ai_gateway_api_key: str = ""
    ai_gateway_model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    tts_provider: str = "demo"
    asr_provider: str = "demo"
    whisper_model: str = "base"
    image_provider: str = "demo"
    monthly_generation_limit: int = 20
    max_upload_mb: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
