# RAG Pipeline - Learning & Implementation TODO

## Phase 1: Ingestion
> Confluence fetch + HTML-to-markdown conversion is already handled by an
> external script. The output is a directory of markdown files sorted by
> page index (`pages/version/`). This phase just loads those files.
- [ ] Implement `cleaner.py` - light normalization pass (strip leftover HTML artifacts, normalize whitespace, remove WIKI boilerplate if any)
- [ ] Implement `reader.py` - walk the pages directory, load `.md` files into a document structure (text + metadata: page ID, file path, etc.)
- [ ] Write tests for ingestion (load sample `.md` files, verify document structure and clean output)

## Phase 2: Chunking
- [ ] Learn about chunking strategies (fixed-size, recursive, semantic)
- [ ] Learn why chunk size and overlap matter (too small = no context, too big = diluted relevance)
- [ ] Implement `splitter.py` - start with fixed-size + overlap, manually
- [ ] Experiment with different chunk sizes (256, 512, 1024 tokens) and see the difference
- [ ] Write tests for chunking (verify chunk sizes, overlap, edge cases)

## Phase 3: Embedding
- [ ] Learn what embeddings are (text -> dense vector, semantic similarity as distance)
- [ ] Install `sentence-transformers`, load `all-MiniLM-L6-v2`
- [ ] Implement `embedder.py` - take chunks in, get vectors out
- [ ] Inspect the raw vectors - look at dimensions, compare similar vs dissimilar text
- [ ] Write tests for embedding (verify output shape, deterministic results)

## Phase 4: Vector Store
- [ ] Learn how vector similarity search works (cosine similarity, approximate nearest neighbors)
- [ ] Install ChromaDB
- [ ] Implement `vector_store.py` - store embeddings with metadata, query by similarity
- [ ] Experiment with persistence (save to disk, reload, verify data survives restart)
- [ ] Write tests for store (insert, query, verify results match expectations)

## Phase 5: Retrieval
- [ ] Learn about retrieval strategies (top-k, similarity thresholds, re-ranking)
- [ ] Implement `retriever.py` - take a query string, return ranked document chunks
- [ ] Experiment with top-k values and observe how result quality changes
- [ ] Write tests for retrieval (known queries against known documents)

## Phase 6: Generation
- [ ] Decide on LLM backend (Claude API, local model via MLX/Ollama, etc.)
- [ ] Learn about prompt templates and context injection
- [ ] Implement `generator.py` - build prompt from retrieved chunks + user query, call LLM
- [ ] Experiment with different prompt templates and see how output quality changes
- [ ] Write tests for generation (mock the LLM, verify prompt construction)

## Phase 7: Pipeline Orchestration
- [ ] Implement `config.py` - centralize settings (model names, chunk sizes, paths, DB location)
- [ ] Implement `pipeline.py` - wire all stages together (ingest -> chunk -> embed -> store)
- [ ] Add a query flow (query -> retrieve -> generate -> response)
- [ ] Update `main.py` as CLI entrypoint (or add FastAPI for an HTTP interface)
- [ ] Write integration tests (end-to-end: ingest a doc, query it, get a response)

## Phase 8: LangChain Integration
- [ ] Go back through each phase and swap in LangChain equivalents
- [ ] Compare your manual implementations with LangChain's abstractions
- [ ] Identify where LangChain helps vs. where it hides too much

## Phase 9: Iterate & Improve
- [ ] Hook up the Confluence manifest script for incremental ingestion
- [ ] Experiment with different embedding models
- [ ] Try a different vector store (pgvector, FAISS) and compare
- [ ] Add metadata filtering (filter by Confluence space, page date, etc.)
- [ ] Explore re-ranking retrieved results before generation
