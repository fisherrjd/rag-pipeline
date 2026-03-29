from __future__ import annotations

import logging

from rag_pipeline import config
from rag_pipeline.chunking.splitter import chunk_page
from rag_pipeline.embedding.embedder import Embedder
from rag_pipeline.ingest.reader import iter_pages
from rag_pipeline.retrieval.retriever import Retriever
from rag_pipeline.store.index_state import IndexState
from rag_pipeline.store.vector_store import VectorStore

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self) -> None:
        self.embedder = Embedder(model_name=config.EMBEDDING_MODEL)
        self.store = VectorStore(path=config.STORE_PATH)
        self.retriever = Retriever(self.embedder, self.store)

    def index(self, page_batch_size: int = 50) -> dict:
        """Ingest all pages, embed and store any that are new or updated.

        Chunks are accumulated across pages and embedded in batches for efficiency.
        Returns a summary dict with counts of indexed and skipped pages.
        """
        indexed = skipped = 0
        pending: list[tuple[dict, list[dict]]] = []  # (page_meta, chunks)

        with IndexState(config.STATE_PATH) as state:
            for page in iter_pages(
                pages_dir=config.PAGES_DIR,
                manifest_path=config.MANIFEST_PATH,
            ):
                pageid, revid = page["pageid"], page["revid"]
                if not state.is_stale(pageid, revid):
                    skipped += 1
                    continue
                self.store.delete_page(pageid)
                chunks = chunk_page(page, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
                if chunks:
                    pending.append((page, chunks))

                if len(pending) >= page_batch_size:
                    indexed += self._flush(pending, state)
                    pending.clear()

            if pending:
                indexed += self._flush(pending, state)

        log.info(f"Index complete — {indexed} indexed, {skipped} skipped")
        return {"indexed": indexed, "skipped": skipped, "total": self.store.count}

    def _flush(self, pending: list[tuple[dict, list[dict]]], state: "IndexState") -> int:
        all_chunks = [chunk for _, chunks in pending for chunk in chunks]
        self.store.add(self.embedder.embed_chunks(all_chunks))
        for page, _ in pending:
            state.update(page["pageid"], page["revid"])
            log.info(f"Indexed {page['title']!r} (revid={page['revid']})")
        return len(pending)

    def query(
        self,
        query: str,
        top_k: int = config.DEFAULT_TOP_K,
        min_score: float = config.DEFAULT_MIN_SCORE,
    ) -> list[dict]:
        """Retrieve the top-k most relevant chunks for a query string."""
        return self.retriever.retrieve(query, top_k=top_k, min_score=min_score)
