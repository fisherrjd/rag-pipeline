from rag_pipeline.embedding.embedder import Embedder
from rag_pipeline.store.vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.0) -> list[dict]:
        """Embed query, search the store, return ranked chunks above min_score."""
        vector = self._embedder.embed([query])[0]
        results = self._store.query(vector, top_k=top_k)
        return [r for r in results if r["score"] >= min_score]
