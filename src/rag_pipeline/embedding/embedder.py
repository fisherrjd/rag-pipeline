from fastembed import TextEmbedding

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(texts)]

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        texts = [c["text"] for c in chunks]
        vectors = self.embed(texts)
        return [{**chunk, "vector": vector} for chunk, vector in zip(chunks, vectors)]
