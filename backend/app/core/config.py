"""
إعدادات التطبيق الأساسية
Application Configuration Settings
"""

from typing import List, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """إعدادات التطبيق الرئيسية"""
    
    # Server Configuration
    PROJECT_NAME: str = "Educational Content Comparison API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    # Database
    SUPABASE_URL: str = "https://vfuapihpzucmfqqfmsnt.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"
    SUPABASE_SERVICE_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # AI Services
    LANDING_AI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "AIzaSyCDO-0puQQN79BJ4u503O31g16ww8CAycg")
    VISION_AGENT_API_KEY: str = os.environ.get("VISION_AGENT_API_KEY", "")
    
    # File Processing
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "webp"]
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_MINUTES: int = 30
    CLEANUP_AFTER_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        # Vite dev server default fallback port when 8080 is busy
        "http://localhost:8081",
        # Local network IP (adjust accordingly if your LAN IP changes)
        "http://192.168.1.6:8081"
    ]
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    def create_upload_dir(self):
        """إنشاء مجلد الرفع إذا لم يكن موجوداً"""
        if not os.path.exists(self.UPLOAD_DIR):
            os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        
        # إنشاء مجلدات فرعية
        subdirs = ["old", "new", "temp", "results", "batch_processing", "multilingual_results"]
        for subdir in subdirs:
            path = os.path.join(self.UPLOAD_DIR, subdir)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"], 
        env_file_encoding="utf-8",
        extra="ignore"
    )


# إنشاء instance من الإعدادات
settings = Settings()

# إنشاء مجلدات الرفع
settings.create_upload_dir()

# دالة للحصول على الإعدادات
def get_settings() -> Settings:
    return settings 