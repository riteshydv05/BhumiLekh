
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
    # Base checkpoint for general document structure detection.
    # Fine-tuning on land-record datasets is required for field-level classification.
    LAYOUTLMV3_MODEL_NAME: str = "microsoft/layoutlmv3-base"
    LAYOUTLMV3_USE_CUDA: bool = False  # Set to True if GPU is available
    LAYOUTLMV3_MAX_LENGTH: int = 512  # Max tokens per page
    LAYOUTLMV3_NORMALIZE_COORD: int = 1000  # LayoutLMv3 coordinate range

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
