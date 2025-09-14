import os
import re
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from pathlib import Path
from chromadb import PersistentClient

# Config
TUTORIAL_PATH = Path("tutorials/python_tutorial.md")
CHUNK_SIZE = 300  # characters per chunk
COLLECTION_NAME = "python_tutorial"

# Load tutorial
with open(TUTORIAL_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Split on any header line like #, ##, ###, etc.
chunks = re.split(r'\n(?=#+ )', content.strip())

# Setup ChromaDB client
client = PersistentClient(path="./vectorstore")

# Optional: clean old collection if it exists
try:
    client.delete_collection(COLLECTION_NAME)
except:
    pass

# Load embedding model
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create collection and add documents
collection = client.create_collection(name=COLLECTION_NAME, embedding_function=embedding_func)

for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk],
        metadatas=[{"source": "python_tutorial", "chunk_id": i}],
        ids=[f"chunk_{i}"]
    )

print(f"Indexed {len(chunks)} chunks from the tutorial.")
