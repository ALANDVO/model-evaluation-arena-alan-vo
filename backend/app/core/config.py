import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    app_name: str = "model-evaluation-arena-alan-vo"
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    secret_key: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "default-dev-secret-key-at-least-32-chars-long"))
    cookie_secure: bool = Field(default_factory=lambda: os.getenv("COOKIE_SECURE", "false").lower() == "true")
    demo_mode: bool = Field(default_factory=lambda: os.getenv("DEMO_MODE", "true").lower() == "true")
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./arena.db"))

    # Keycloak / OIDC Settings
    oidc_issuer_url: str = Field(default_factory=lambda: os.getenv("OIDC_ISSUER_URL", "http://127.0.0.1:8080/realms/model-arena"))
    oidc_client_id: str = Field(default_factory=lambda: os.getenv("OIDC_CLIENT_ID", "model-arena-client"))
    oidc_client_secret: str = Field(default_factory=lambda: os.getenv("OIDC_CLIENT_SECRET", ""))
    oidc_redirect_uri: str = Field(default_factory=lambda: os.getenv("OIDC_REDIRECT_URI", "http://127.0.0.1:8000/api/auth/callback"))
    oidc_frontend_url: str = Field(default_factory=lambda: os.getenv("OIDC_FRONTEND_URL", "http://127.0.0.1:5173"))

    # Advisory LLM settings (keys only server-side, never exposed to clients)
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai-compatible"))
    llm_base_url: str = Field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://llm.chris-vo.com/v1"))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "qwen3.8-27b"))
    llm_api_key: str = Field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0")))

    def validate_runtime(self) -> None:
        if self.app_env.lower() == "production" and self.demo_mode:
            raise RuntimeError("CRITICAL: Startup refused - Demo mode cannot be enabled in production environment.")

settings = Settings()
