from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    cohere_api_key: str
    cohere_embedding_model: str = "embed-v4.0"
    cohere_embedding_dimension: int = 1024
    cohere_rerank_model: str = "rerank-v4.0-pro"
    pokemon_rerank_candidates: int = 25
    search_rate_limit_requests: int = 10
    search_rate_limit_window_seconds: int = 60
    cohere_rerank_limit_requests: int = 10
    cohere_rerank_limit_window_seconds: int = 60
    cohere_embed_limit_requests: int = 2000
    cohere_embed_limit_window_seconds: int = 60
    explain_cache_enabled: bool = True
    explain_cache_ttl_seconds: int = 86400  # 24 h
    explain_cache_max_entries: int = 1000
    explain_prompt_version: str = "v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
