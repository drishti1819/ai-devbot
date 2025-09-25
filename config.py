# config.py
import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# ----------------- Paths and Constants -----------------
VECTORSTORE_PATH = "./vectorstore"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_MODEL_PATH = os.path.join("./models", EMBED_MODEL_NAME)

# PostgreSQL config
PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

# LLM Config
LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-coder:6.7b"

# ----------------- Centralized Setup Objects -----------------
try:
    if not os.path.exists(EMBED_MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {EMBED_MODEL_PATH}")

    embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_PATH)
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
    embed = SentenceTransformer(EMBED_MODEL_PATH)

except Exception as e:
    print(f"Failed to initialize shared ChromaDB or embedding model: {e}")
    print("Please ensure the model is manually downloaded to the './models' directory.")
    exit(1)
