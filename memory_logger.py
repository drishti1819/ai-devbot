# memory_logger.py
import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# Config
MEMORY_DB_PATH = "./memorystore"
MEMORY_COLLECTION = "chat_memory"

# Setup ChromaDB
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
client = PersistentClient(path=MEMORY_DB_PATH)
try:
    collection = client.get_or_create_collection(name=MEMORY_COLLECTION, embedding_function=embedding_func)
except:
    client.delete_collection(MEMORY_COLLECTION)
    collection = client.create_collection(name=MEMORY_COLLECTION, embedding_function=embedding_func)

def log_memory(question: str, answer: str, tag: str = "chat"):
    if not question.strip() or not answer.strip():
        return

    combined = f"Q: {question.strip()}\nA: {answer.strip()}"
    uid = f"memory_{hash(combined)}"

    collection.add(
        documents=[combined],
        metadatas=[{"source": tag}],
        ids=[uid]
    )

def query_memory(query: str, n=5):
    results = collection.query(query_texts=[query], n_results=n)
    return [doc for doc in results.get("documents", [[]])[0]]
