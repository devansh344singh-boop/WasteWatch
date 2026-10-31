from pydantic_settings import BaseSettings, SettingsConfigDict
from secrets import token_urlsafe

class Settings(BaseSettings):
    database_url: str = "sqlite:///./wastewatch.db"
    # Ephemeral fallback keeps first-run local setup simple; set JWT_SECRET in .env
    # to retain sessions across restarts and for every deployed environment.
    jwt_secret: str = token_urlsafe(48)
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    upload_dir: str = "uploads"
    max_upload_mb: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
