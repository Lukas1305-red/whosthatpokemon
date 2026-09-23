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
    explain_rate_limit_requests: int = 3
    explain_rate_limit_window_seconds: int = 60
    anthropic_timeout_seconds: float = 15.0
    anthropic_max_retries: int = 0
    llm_enabled: bool = True
    explain_daily_llm_budget: int = 25
    redis_url: str = ""
    explain_cache_enabled: bool = True
    explain_cache_ttl_seconds: int = 86400  # 24 h
    explain_cache_max_entries: int = 1000
    explain_prompt_version: str = "v1"
    chroma_data_path: str = "data/chroma"
    allowed_origins: str = ""
    trusted_hosts: str = ""
    max_request_body_bytes: int = 16 * 1024
    max_concurrent_requests: int = 20
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> list[str]:
        return self._csv_values(self.allowed_origins)

    @property
    def host_allowlist(self) -> list[str]:
        return self._csv_values(self.trusted_hosts)

    @staticmethod
    def _csv_values(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()
