import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Core ---
    APP_NAME: str = "AI-Resistant Video Privacy Platform"
    ENV: str = os.getenv("ENV", "development")

    # --- Auth ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME_DEV_ONLY_NOT_FOR_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h session

    # --- Database ---
    # Swap this for a Postgres/Supabase URL later, e.g.
    # postgresql+psycopg2://user:pass@host:5432/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # --- Storage ---
    # Local disk for MVP. Swap for S3/Supabase Storage later behind the same interface
    # (see app/storage/base.py).
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "./storage_data")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./storage_data/tmp")
    PROTECTED_DIR: str = os.getenv("PROTECTED_DIR", "./storage_data/protected")

    # --- Capture / processing constraints (mirrors SRS FR-005, FR-006) ---
    MAX_RECORD_SECONDS: int = 6
    TARGET_FPS: int = 24

    # --- Retention policy (SRS Privacy Requirements: must be documented) ---
    # Temporary original raw video is deleted immediately after a job reaches
    # COMPLETED or FAILED. This TTL is a hard backstop in case cleanup fails.
    TEMP_RETENTION_MINUTES: int = 30

    # --- Recognition / optimization thresholds ---
    # Cosine similarity between original and transformed face embedding.
    # Below this, we consider the automated recognizer "defeated".
    AI_DEFEAT_SIMILARITY_THRESHOLD: float = 0.35
    MAX_OPTIMIZATION_STEPS: int = 12

    class Config:
        env_file = ".env"


settings = Settings()
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.PROTECTED_DIR, exist_ok=True)
