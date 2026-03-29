import logging
import sys

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from rag_pipeline import config
from rag_pipeline.ingest.fetcher import sync_pages
from rag_pipeline.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="RAG Pipeline")
_pipeline: Pipeline | None = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    min_score: float = 0.0


@app.post("/fetch")
def fetch():
    """Fetch new/updated pages from the wiki and update the manifest."""
    sync_pages(pages_dir=config.PAGES_DIR, manifest_path=config.MANIFEST_PATH)
    return {"status": "ok"}


@app.post("/index")
def index():
    """Chunk, embed, and store all new/updated pages."""
    return get_pipeline().index()


@app.post("/sync")
def sync():
    """Fetch from wiki then index — full pipeline in one shot."""
    sync_pages(pages_dir=config.PAGES_DIR, manifest_path=config.MANIFEST_PATH)
    return get_pipeline().index()


@app.post("/query")
def query(req: QueryRequest):
    """Retrieve relevant chunks for a query."""
    results = get_pipeline().query(req.query, top_k=req.top_k, min_score=req.min_score)
    return {"query": req.query, "results": results}


@app.get("/health")
def health():
    return {"status": "ok", "chunks": get_pipeline().store.count}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "index":
        summary = Pipeline().index()
        print(
            f"Indexed: {summary['indexed']}  Skipped: {summary['skipped']}  Total: {summary['total']}"
        )
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=2020, reload=True)


if __name__ == "__main__":
    main()
