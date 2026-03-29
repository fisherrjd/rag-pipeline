from pathlib import Path

# Paths
DATA_DIR = Path("data")
PAGES_DIR = DATA_DIR / "pages"
MANIFEST_PATH = DATA_DIR / "manifest.json"
STORE_PATH = DATA_DIR / "chroma"
STATE_PATH = DATA_DIR / "index_state.db"

# Embedding
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Retrieval
DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.0
