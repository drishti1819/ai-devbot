import os
import uuid
import requests
import json
import hashlib
import psycopg2
# Import shared objects from the new config file
from config import client, embed_func, embed, LLM_ENDPOINT, LLM_MODEL, PG_HOST, PG_DB, PG_USER, PG_PASS

<<<<<<< HEAD
# Constants
# Constants
TUTORIAL_COLLECTION = "python_tutorial"
MEMORY_COLLECTION = "user_memory"

# Store inside the container filesystem (safe for all users)
VECTORSTORE_PATH = "/app/vectorstore"

EMBED_MODEL = "all-MiniLM-L6-v2"

LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-coder:6.7b"

# PostgreSQL config
PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

# Setup ChromaDB (persistent with safe fallback)
os.makedirs(VECTORSTORE_PATH, exist_ok=True)  # ensure directory exists

try:
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
    print(f"[ChromaDB] Using PersistentClient at {VECTORSTORE_PATH}")
except Exception as e:
    print(f"[ChromaDB] PersistentClient failed ({type(e).__name__}): {e!s}")
    print("[ChromaDB] Falling back to EphemeralClient")
    client = chromadb.EphemeralClient()

embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

# Load collections
tutorial = client.get_or_create_collection(name=TUTORIAL_COLLECTION, embedding_function=embed_func)
=======
# ----------------- Constants -----------------
DEFAULT_TUTORIAL_COLLECTION = "python_tutorial"
MEMORY_COLLECTION = "user_memory"

# Load collections using the shared client and embed_func
tutorial = client.get_or_create_collection(name=DEFAULT_TUTORIAL_COLLECTION, embedding_function=embed_func)
>>>>>>> 4584bef1 (feat: Add local RAG, clean code, and consolidate dependencies)
memory = client.get_or_create_collection(name=MEMORY_COLLECTION, embedding_function=embed_func)

# ----------------- Helpers -----------------
def make_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def retrieve_context(query, top_k=5, collection_names=None):
    """
    Retrieve relevant chunks from uploaded document collections (if any) and memory.
    Prioritize document context first, then memory, then tutorial.
    """
    context_chunks = []
    
    try:
        if collection_names:
            for col_name in reversed(collection_names):
                collection = client.get_or_create_collection(
                    name=col_name, embedding_function=embed_func
                )
                results = collection.query(query_texts=[query], n_results=top_k)
                doc_chunks = results.get("documents", [[]])[0]
                context_chunks.extend(doc_chunks)
        
        memory_results = memory.query(query_texts=[query], n_results=top_k)
        memory_chunks = memory_results.get("documents", [[]])[0]
        context_chunks.extend(memory_chunks)

        if not context_chunks:
            tutorial_results = tutorial.query(query_texts=[query], n_results=top_k)
            tutorial_chunks = tutorial_results.get("documents", [[]])[0]
            context_chunks.extend(tutorial_chunks)

    except Exception as e:
        print(f"[Context Retrieval Error]: {e}")
        return []

    return context_chunks

def query_llm(prompt, model=LLM_MODEL):
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"[LLM Error {response.status_code}] {response.text}"
    except requests.exceptions.RequestException as e:
        return f"[Connection Error] Is the local LLM running at {LLM_ENDPOINT}? Error: {e}"

def log_to_memory(question: str, answer: str):
    if not question or not answer:
        return
    
    combined_text = f"Q: {question.strip()}\nA: {answer.strip()}"
    uid = str(uuid.uuid4())
    memory.add(
        ids=[uid],
        documents=[combined_text],
        metadatas=[{"source": "chat"}],
        embeddings=[embed.encode(combined_text).tolist()]
    )

def log_to_postgres(user_email: str, question: str, answer: str):
    try:
        conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_email TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute(
            "INSERT INTO chat_history (user_email, question, answer) VALUES (%s, %s, %s)",
            (user_email, question, answer)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[PostgreSQL Logging Error]: {e}")

# ----------------- Chat Functions -----------------
def chat_raw(user_input: str, collection_names=None) -> dict:
    context_chunks = retrieve_context(user_input, collection_names=collection_names)
    context = "\n\n".join(context_chunks) if context_chunks else "[No relevant memory or document found.]"

    full_prompt = f"""You are a helpful assistant.
Use CONTEXT and MEMORY to answer the QUESTION clearly and precisely.

### CONTEXT ###
{context}

### QUESTION ###
{user_input}

### RESPONSE ###
"""
    ai_response = query_llm(full_prompt)
    log_to_memory(user_input, ai_response)
    return {"question": user_input, "answer": ai_response.strip()}

def chat(user_input: str, collection_names=None) -> str:
    result = chat_raw(user_input, collection_names=collection_names)
    return result["answer"]
