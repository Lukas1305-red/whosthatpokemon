from anthropic import Anthropic

from config import settings

anthropic_client = Anthropic(api_key=settings.anthropic_api_key)