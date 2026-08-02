from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FarmLink Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./data/farmlink.db"
    secret_key: str = "change-this-before-production"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    public_base_url: str = "http://localhost:8000"
    initial_ceo_name: str = "Makwande Gcora"
    initial_ceo_email: str = ""
    initial_ceo_password: str = ""
    paystack_public_key: str = ""
    paystack_secret_key: str = ""
    paystack_callback_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
