from pathlib import Path

import chromadb

DEFAULT_COLLECTION = "rag_pipeline"


class VectorStore:
    def __init__(self, path: str | Path | None = None, collection: str = DEFAULT_COLLECTION) -> None:
        if path is None:
            self._client = chromadb.EphemeralClient()
        else:
            self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[dict], batch_size: int = 100) -> None:
        """Upsert embedded chunks (must have a 'vector' field) into the store.

        Uses upsert so re-indexing the same page is idempotent. Batches to
        stay within Chroma's internal limits.
        """
        for offset in range(0, len(chunks), batch_size):
            batch = chunks[offset : offset + batch_size]
            self._collection.upsert(
                ids=[f"{c['pageid']}_{offset + j}" for j, c in enumerate(batch)],
                embeddings=[c["vector"] for c in batch],
                documents=[c["text"] for c in batch],
                metadatas=[
                    {"pageid": c["pageid"], "title": c["title"], "section": c["section"], "part": c["part"]}
                    for c in batch
                ],
            )

    def query(self, vector: list[float], top_k: int = 5) -> list[dict]:
        """Return top_k most similar chunks to the given vector."""
        results = self._collection.query(query_embeddings=[vector], n_results=top_k)
        return [
            {
                "text": doc,
                "score": 1 - dist,  # chroma returns cosine distance; convert to similarity
                **meta,
            }
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0],
            )
        ]

    def delete_page(self, pageid: str) -> None:
        """Delete all chunks belonging to a page."""
        ids = self._collection.get(where={"pageid": pageid})["ids"]
        if ids:
            self._collection.delete(ids=ids)

    @property
    def count(self) -> int:
        return self._collection.count()
