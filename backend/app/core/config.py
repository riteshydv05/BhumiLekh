
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Land Record AI System"
    APP_ENV: str = "development"

    DATABASE_URL: str = (
        "postgresql+psycopg://land_admin:land_password"
        "@localhost:5432/land_records"
    )

    REDIS_URL: str = "redis://localhost:6379/0"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_password"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "land-documents"

    # PaddleOCR configuration
    PADDLE_OCR_LANG: str = "en"
    PADDLE_OCR_USE_ANGLE: bool = False
    PADDLE_OCR_DET_THRESH: float = 0.3
    PADDLE_OCR_REC_THRESH: float = 0.0
    # PDF rendering DPI — higher = better quality, more RAM
    PDF_RENDER_DPI: int = 150
    # Maximum pages to render per PDF (None = all)
    PDF_MAX_PAGES: int = 50

    # LayoutLMv3 document understanding configuration
    LAYOUTLMV3_MODEL_NAME: str = "microsoft/layoutlmv3-base"
    LAYOUTLMV3_USE_CUDA: bool = False  # Set to True if GPU is available
    LAYOUTLMV3_MAX_LENGTH: int = 512  # Max tokens per page
    LAYOUTLMV3_NORMALIZE_COORD: int = 1000  # LayoutLMv3 coordinate range

    # ---------------------------------------------------------------------------
    # Optional External API Integration Layer (Offline-First Defaults)
    # ---------------------------------------------------------------------------
    # Bhashini Hosted Translation & Transliteration
    ENABLE_BHASHINI: bool = False
    BHASHINI_API_KEY: str = ""
    BHASHINI_API_URL: str = ""
    BHASHINI_TIMEOUT: float = 5.0

    # VLM (Vision-Language Model) Fallback Escalation
    ENABLE_VLM_FALLBACK: bool = False
    VLM_CONFIDENCE_THRESHOLD: float = 0.60
    DEFAULT_VLM_PROVIDER: str = "gemini"  # 'gemini', 'openai', 'anthropic'

    # External Provider Keys (Must default to empty string / None)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ---------------------------------------------------------------------------
    # JWT Authentication & RBAC
    # ---------------------------------------------------------------------------
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-immediately"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    AUTH_ENABLED: bool = False  # Set True in production

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


def mask_secret(secret: str | None) -> str:
    """Mask sensitive API keys for safe logging (e.g. 'sk-****1234' or '<not-configured>')."""
    if not secret or not secret.strip():
        return "<not-configured>"
    s = secret.strip()
    if len(s) <= 8:
        return "********"
    return f"{s[:4]}****{s[-4:]}"


settings = Settings()
