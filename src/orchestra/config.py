"""Application configuration via pydantic-settings (.env loading)."""

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "OrchestraAI"
    app_env: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "INFO"
    stealth_mode: bool = True

    # LLM Providers (Tier 1)
    openai_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")
    ollama_base_url: str = "http://ollama:11434"

    # Model routing
    default_fast_model: str = "gpt-4o-mini"
    default_capable_model: str = "claude-sonnet-4-20250514"
    default_local_model: str = "llama3.2"

    # Platform API Keys (Tier 2)
    twitter_api_key: SecretStr = SecretStr("")
    twitter_api_secret: SecretStr = SecretStr("")
    twitter_access_token: SecretStr = SecretStr("")
    twitter_access_token_secret: SecretStr = SecretStr("")
    twitter_bearer_token: SecretStr = SecretStr("")
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    youtube_api_key: SecretStr = SecretStr("")
    pinterest_app_id: str = ""
    pinterest_app_secret: SecretStr = SecretStr("")
    tiktok_app_id: str = ""
    tiktok_app_secret: SecretStr = SecretStr("")

    # Platform API Keys (Tier 3 -- requires LLC)
    meta_app_id: str = ""
    meta_app_secret: SecretStr = SecretStr("")
    linkedin_client_id: str = ""
    linkedin_client_secret: SecretStr = SecretStr("")
    snapchat_app_id: str = ""
    snapchat_app_secret: SecretStr = SecretStr("")
    google_ads_developer_token: SecretStr = SecretStr("")
    google_ads_client_id: str = ""
    google_ads_client_secret: SecretStr = SecretStr("")

    # Infrastructure (Tier 4 -- auto-handled by Docker)
    database_url: str = "postgresql+asyncpg://orchestra:orchestra_dev_password@postgres:5432/orchestraai"
    redis_url: str = "redis://redis:6379/0"
    kafka_bootstrap_servers: str = "kafka:9092"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    @property
    def ollama_url(self) -> str:
        return self.ollama_base_url

    # Security
    jwt_secret_key: SecretStr = SecretStr("CHANGE-ME-generate-with-openssl-rand-hex-32")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    fernet_key: SecretStr = SecretStr("CHANGE-ME-generate-with-python-cryptography-fernet")
    encryption_key: SecretStr = SecretStr("CHANGE-ME-generate-aes-256-key")

    # Video generation (fal.ai)
    fal_api_key: SecretStr = SecretStr("")

    @property
    def has_fal(self) -> bool:
        return bool(self.fal_api_key.get_secret_value())

    # SMTP (email notifications)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from_email: str = "alerts@useorchestra.dev"

    @property
    def has_smtp(self) -> bool:
        return bool(self.smtp_host)

    # Stripe billing
    stripe_secret_key: SecretStr = SecretStr("")
    stripe_webhook_secret: SecretStr = SecretStr("")
    stripe_starter_price_id: str = ""
    stripe_agency_price_id: str = ""
    frontend_url: str = "http://localhost:3000"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"])

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key.get_secret_value())

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
