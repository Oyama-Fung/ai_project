# 从根目录读取环境变量.env并暴露settings单例
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    app_name: str = "rag-knowledge-base"
    log_level: str = "INFO"
    # 数据库配置
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag_kb"
    # 腾讯云COS配置
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_bucket: str = ""
    cos_region: str = "ap-beijing"
    # 跨域配置
    cors_origins: str = "http://localhost:5173"
    # Embedding
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024
    embedding_batch_size: int = 10
    # 文档上传与切分
    upload_max_size_mb: int = 50
    chunk_size: int = 600
    chunk_overlap: int = 60

    @property
    def cos_configured(self) -> bool:
        return bool(self.cos_secret_id and self.cos_secret_key and self.cos_bucket)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
