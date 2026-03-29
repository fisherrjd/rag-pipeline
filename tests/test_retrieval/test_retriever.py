from unittest.mock import MagicMock

import pytest

from rag_pipeline.retrieval.retriever import Retriever


def _make_retriever(query_results):
    embedder = MagicMock()
    embedder.embed.return_value = [[0.1] * 384]

    store = MagicMock()
    store.query.return_value = query_results

    return Retriever(embedder, store), embedder, store


def _chunk(score, section="S", pageid="1"):
    return {"pageid": pageid, "title": "T", "section": section, "part": 0, "text": "text", "score": score}


def test_retrieve_returns_results():
    retriever, _, _ = _make_retriever([_chunk(0.9), _chunk(0.7)])
    results = retriever.retrieve("query")
    assert len(results) == 2


def test_retrieve_embeds_query():
    retriever, embedder, _ = _make_retriever([])
    retriever.retrieve("my query")
    embedder.embed.assert_called_once_with(["my query"])


def test_retrieve_passes_top_k_to_store():
    retriever, _, store = _make_retriever([])
    retriever.retrieve("query", top_k=7)
    store.query.assert_called_once()
    assert store.query.call_args[1]["top_k"] == 7


def test_retrieve_filters_by_min_score():
    results = [_chunk(0.9), _chunk(0.5), _chunk(0.3)]
    retriever, _, _ = _make_retriever(results)
    filtered = retriever.retrieve("query", min_score=0.6)
    assert len(filtered) == 1
    assert filtered[0]["score"] == 0.9


def test_retrieve_min_score_zero_returns_all():
    results = [_chunk(0.9), _chunk(0.1)]
    retriever, _, _ = _make_retriever(results)
    assert len(retriever.retrieve("query", min_score=0.0)) == 2


def test_retrieve_empty_store():
    retriever, _, _ = _make_retriever([])
    assert retriever.retrieve("query") == []
