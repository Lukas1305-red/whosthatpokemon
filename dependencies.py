import chromadb
from anthropic import Anthropic
from cohere import ClientV2

from config import settings

anthropic_client = Anthropic(
    api_key=settings.anthropic_api_key,
    timeout=settings.anthropic_timeout_seconds,
    # A retry can create another paid provider request. Keep retries explicit
    # at the application layer, where we can enforce a future global budget.
    max_retries=settings.anthropic_max_retries,
)
embedding_client = ClientV2(api_key=settings.cohere_api_key)
chroma_db_client = chromadb.PersistentClient(path="data/chroma")
