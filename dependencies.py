import chromadb
from anthropic import Anthropic
from cohere import ClientV2

from config import settings

anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
embedding_client = ClientV2(api_key=settings.cohere_api_key)
chroma_db_client = chromadb.PersistentClient(path="data/chroma")
