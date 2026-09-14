from types import SimpleNamespace

from evaluation.rerankers import CohereReranker


def test_cohere_reranker_preserves_api_rank_and_score():
    class FakeClient:
        def rerank(self, **kwargs):
            assert kwargs["query"] == "patient researcher"
            assert kwargs["documents"] == ["first", "second", "third"]
            assert kwargs["top_n"] == 2
            return SimpleNamespace(
                results=[
                    SimpleNamespace(index=2, relevance_score=0.9),
                    SimpleNamespace(index=0, relevance_score=0.4),
                ]
            )

    reranker = CohereReranker(FakeClient(), model="test-model")

    assert reranker("patient researcher", ["first", "second", "third"], 2) == [
        (2, 0.9),
        (0, 0.4),
    ]
