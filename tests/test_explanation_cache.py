from types import SimpleNamespace

from server.services.explanation_cache import ExplanationCache, RedisExplanationCache
from server.services.llm_service import LLMService


class FakeAnthropicClient:
    def __init__(self):
        self.messages = self
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            content=[SimpleNamespace(text=f"Explanation {self.calls}")]
        )


class FakeRedisRepository:
    def __init__(self):
        self.entries = {}
        self.ttls = {}

    def get(self, key):
        return self.entries.get(key)

    def set_with_ttl(self, key, value, ttl_seconds):
        self.entries[key] = value
        self.ttls[key] = ttl_seconds


def test_llm_service_caches_an_identical_explanation_request():
    client = FakeAnthropicClient()
    service = LLMService(client, explanation_cache=ExplanationCache(60, 10))

    first = service.explain_pokemon_match("Characteristics: calm.", "Lapras")
    second = service.explain_pokemon_match("Characteristics: calm.", "Lapras")

    assert first == second == "Explanation 1"
    assert client.calls == 1


def test_llm_service_invalidates_when_the_pokemon_document_changes():
    client = FakeAnthropicClient()
    service = LLMService(client, explanation_cache=ExplanationCache(60, 10))

    service.explain_pokemon_match("Characteristics: calm.", "Lapras: calm")
    service.explain_pokemon_match("Characteristics: calm.", "Lapras: adventurous")

    assert client.calls == 2


def test_explanation_cache_expires_entries():
    now = [0.0]
    cache = ExplanationCache(10, 10, clock=lambda: now[0])
    calls = [0]

    def create():
        calls[0] += 1
        return f"Explanation {calls[0]}"

    assert cache.get_or_create("key", create) == "Explanation 1"
    now[0] = 10.0
    assert cache.get_or_create("key", create) == "Explanation 2"


def test_redis_explanation_cache_reuses_an_answer_and_sets_its_ttl():
    redis = FakeRedisRepository()
    cache = RedisExplanationCache(redis, ttl_seconds=60)
    calls = [0]

    def create():
        calls[0] += 1
        return f"Explanation {calls[0]}"

    assert cache.get_or_create("key", create) == "Explanation 1"
    assert cache.get_or_create("key", create) == "Explanation 1"
    assert calls == [1]
    assert redis.ttls == {"key": 60}
