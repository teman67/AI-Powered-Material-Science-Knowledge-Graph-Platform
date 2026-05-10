from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "Material Science KG Platform"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@postgres:5432/materials")
    redis_url: str = "redis://redis:6379/0"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "app/data/documents"
    max_upload_size_mb: int = Field(default=25, ge=1, le=200)

    chunk_size_tokens: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap_tokens: int = Field(default=150, ge=0, le=1000)

    embedding_model_name: str = "BAAI/bge-large-en"
    embedding_dimension: int = Field(default=1024, ge=64, le=4096)
    embedding_fallback_only: bool = False
    chat_default_top_k: int = Field(default=5, ge=1, le=20)
    chat_graph_top_k: int = Field(default=5, ge=1, le=20)
    chat_graph_candidate_pool: int = Field(default=60, ge=10, le=500)

    graph_enabled: bool = True

    extraction_enable_spacy: bool = False
    extraction_spacy_model: str = "en_core_web_sm"
    extraction_enable_scibert: bool = False
    extraction_scibert_model: str = ""
    extraction_scibert_device: int = -1


@lru_cache
def get_settings() -> Settings:
    return Settings()
