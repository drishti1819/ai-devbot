# memory_logger.py
import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# ----------------- Config -----------------
MEMORY_DB_PATH = "./vectorstore" # Use consistent path
MEMORY_COLLECTION = "user_memory"
EMBED_MODEL_PATH = "./models/all-MiniLM-L6-v2" # Use consistent path

# ----------------- Setup ChromaDB -----------------
try:
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_PATH)
    client = PersistentClient(path=MEMORY_DB_PATH)
    collection = client.get_or_create_collection(name=MEMORY_COLLECTION, embedding_function=embedding_func)
except Exception as e:
    print(f"[Memory Logger Error] Failed to initialize ChromaDB: {e}")
    # Fallback or exit if this is critical
    collection = None

# ----------------- Memory Logging -----------------
def log_memory(question: str, answer: str, tag: str = "chat"):
    """Add a Q&A pair to memory if not empty."""
    if not collection or not question.strip() or not answer.strip():
        return

    combined = f"Q: {question.strip()}\nA: {answer.strip()}"
    uid = f"memory_{hash(combined)}"

    # Check if the document already exists based on ID
    if collection.get(ids=[uid]).get("documents"):
        return

    try:
        collection.add(
            documents=[combined],
            metadatas=[{"source": tag}],
            ids=[uid]
        )
    except Exception as e:
        print(f"[Memory Logger Error] Failed to add to collection: {e}")

def query_memory(query: str, n=5):
    """Retrieve top-n relevant memory entries."""
    if not collection or not collection.count():
        return []

    try:
        results = collection.query(query_texts=[query], n_results=n)
        return [doc for doc in results.get("documents", [[]])[0]]
    except Exception as e:
        print(f"[Memory Logger Error] Failed to query memory: {e}")
        return []
