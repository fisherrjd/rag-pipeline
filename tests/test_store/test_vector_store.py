import pytest

from rag_pipeline.store.vector_store import VectorStore

DIM = 4


def _make_chunks(n: int, dim: int = DIM) -> list[dict]:
    return [
        {
            "pageid": str(i),
            "title": f"Page {i}",
            "section": "Section",
            "part": 0,
            "text": f"chunk text {i}",
            "vector": [float(i) / n] * dim,
        }
        for i in range(n)
    ]


@pytest.fixture
def store():
    return VectorStore()  # ephemeral — no disk writes


def test_add_and_count(store):
    store.add(_make_chunks(3))
    assert store.count == 3


def test_query_returns_top_k(store):
    store.add(_make_chunks(5))
    results = store.query([1.0, 1.0, 1.0, 1.0], top_k=3)
    assert len(results) == 3


def test_query_result_has_expected_fields(store):
    store.add(_make_chunks(2))
    result = store.query([1.0, 1.0, 1.0, 1.0], top_k=1)[0]
    assert "text" in result
    assert "score" in result
    assert "pageid" in result
    assert "title" in result
    assert "section" in result
    assert "part" in result


def test_query_score_between_zero_and_one(store):
    store.add(_make_chunks(3))
    results = store.query([1.0, 0.0, 0.0, 0.0], top_k=3)
    for r in results:
        assert 0.0 <= r["score"] <= 1.0


def test_query_most_similar_ranked_first(store):
    chunks = [
        {**_make_chunks(1, DIM)[0], "pageid": "a", "vector": [1.0, 0.0, 0.0, 0.0]},
        {**_make_chunks(1, DIM)[0], "pageid": "b", "vector": [0.0, 1.0, 0.0, 0.0]},
        {**_make_chunks(1, DIM)[0], "pageid": "c", "vector": [0.0, 0.0, 1.0, 0.0]},
    ]
    store.add(chunks)
    results = store.query([1.0, 0.0, 0.0, 0.0], top_k=3)
    assert results[0]["pageid"] == "a"
    assert results[0]["score"] > results[1]["score"]


def test_persistence(tmp_path):
    store1 = VectorStore(path=tmp_path)
    store1.add(_make_chunks(3))

    store2 = VectorStore(path=tmp_path)
    assert store2.count == 3
