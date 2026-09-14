from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    cohere_api_key: str
    cohere_embedding_model: str = "embed-v4.0"
    cohere_embedding_dimension: int = 1024
    cohere_rerank_model: str = "rerank-v4.0-pro"
    pokemon_rerank_candidates: int = 25

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
