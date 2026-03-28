import pytest

from rag_pipeline.embedding.embedder import DEFAULT_MODEL, Embedder


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


def test_embed_returns_list_of_vectors(embedder):
    result = embedder.embed(["hello world", "foo bar"])
    assert len(result) == 2
    assert all(isinstance(v, list) for v in result)
    assert all(isinstance(x, float) for x in result[0])


def test_embed_vector_dimensions(embedder):
    # all-MiniLM-L6-v2 produces 384-dimensional vectors
    result = embedder.embed(["test sentence"])
    assert len(result[0]) == 384


def test_embed_deterministic(embedder):
    text = ["the quick brown fox"]
    assert embedder.embed(text) == embedder.embed(text)


def test_embed_similar_texts_closer_than_dissimilar(embedder):
    import math

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        mag = math.sqrt(sum(x**2 for x in a)) * math.sqrt(sum(x**2 for x in b))
        return dot / mag

    vecs = embedder.embed([
        "the cat sat on the mat",
        "a cat rested on a rug",
        "quantum mechanics and particle physics",
    ])
    sim_close = cosine(vecs[0], vecs[1])
    sim_far = cosine(vecs[0], vecs[2])
    assert sim_close > sim_far


def test_embed_chunks_adds_vector_field(embedder):
    chunks = [
        {"pageid": "1", "title": "Test", "section": "Intro", "part": 0, "text": "hello world"},
        {"pageid": "1", "title": "Test", "section": "Body", "part": 0, "text": "foo bar baz"},
    ]
    result = embedder.embed_chunks(chunks)
    assert len(result) == 2
    for chunk in result:
        assert "vector" in chunk
        assert isinstance(chunk["vector"], list)
        assert len(chunk["vector"]) == 384


def test_embed_chunks_preserves_metadata(embedder):
    chunks = [{"pageid": "42", "title": "Page", "section": "S", "part": 0, "text": "some text"}]
    result = embedder.embed_chunks(chunks)
    assert result[0]["pageid"] == "42"
    assert result[0]["title"] == "Page"
    assert result[0]["section"] == "S"


def test_default_model_name():
    assert DEFAULT_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
