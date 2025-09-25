import os
import uuid
import chromadb
from sentence_transformers import SentenceTransformer
import psycopg2
import requests
import json
import hashlib

# ----------------- Constants -----------------
DEFAULT_TUTORIAL_COLLECTION = "python_tutorial"
MEMORY_COLLECTION = "user_memory"
VECTORSTORE_PATH = "./vectorstore"
EMBED_MODEL = "./models/all-MiniLM-L6-v2" # Use local path
LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-coder:6.7b"

# PostgreSQL config
PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

# ----------------- Centralized Setup -----------------
try:
    # Initialize SentenceTransformer directly and pass embeddings manually
    embed = SentenceTransformer(EMBED_MODEL)
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)

    # Load collections
    tutorial = client.get_or_create_collection(name=DEFAULT_TUTORIAL_COLLECTION)
    memory = client.get_or_create_collection(name=MEMORY_COLLECTION)

except Exception as e:
    print(f"Failed to initialize ChromaDB or embedding model: {e}")
    exit(1)

# ----------------- Helpers -----------------
def make_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def retrieve_context(query, top_k=5, collection_names=None):
    """
    Retrieve relevant chunks from uploaded document collections (if any) and memory.
    - collection_names: list of active collection names in order of upload.
    - Prioritize document context first, then memory, then tutorial.
    """
    context_chunks = []

    try:
        # Query all uploaded document collections in reverse order (most recent first)
        if collection_names:
            for col_name in reversed(collection_names):
                collection = client.get_or_create_collection(name=col_name)
                results = collection.query(query_texts=[query], n_results=top_k)
                doc_chunks = results.get("documents", [[]])[0]
                context_chunks.extend(doc_chunks)

        # Always add memory chunks as fallback
        memory_results = memory.query(query_texts=[query], n_results=top_k)
        memory_chunks = memory_results.get("documents", [[]])[0]
        context_chunks.extend(memory_chunks)

        # If no uploaded document and no memory, fallback to tutorial
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
        # Check if the LLM endpoint is reachable
        requests.get(f"{LLM_ENDPOINT.rsplit('/', 1)[0]}")
        response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"[LLM Error {response.status_code}] {response.text}"
    except requests.exceptions.RequestException as e:
        return f"[Connection Error] Is the local LLM running at {LLM_ENDPOINT}? Error: {e}"

def log_to_memory(question: str, answer: str):
    # Check for empty inputs to prevent errors
    if not question or not answer:
        return

    q_hash = make_hash(question)
    existing_documents = memory.get(where={"answer": answer}).get("documents", [])
    if any(make_hash(doc) == q_hash for doc in existing_documents):
        return

    uid = str(uuid.uuid4())
    memory.add(
        ids=[uid],
        documents=[question],
        metadatas=[{"answer": answer}],
        embeddings=[embed.encode(question).tolist()]
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

def get_chat_history(user_email: str, limit=20):
    try:
        conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)
        cur = conn.cursor()
        cur.execute("""
            SELECT question, answer, timestamp
            FROM chat_history
            WHERE user_email = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (user_email, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"question": row[0], "answer": row[1], "timestamp": row[2].isoformat()} for row in rows]
    except Exception as e:
        print(f"[PostgreSQL Retrieval Error]: {e}")
        return []

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

# ----------------- CLI Entry -----------------
if __name__ == "__main__":
    print(f"Devbot (Private Assistant using DeepSeek-Coder)\\nType 'exit' or 'quit' to end the session.")
    collections_input = input(
        f"Enter comma-separated collection names (leave blank for default '{DEFAULT_TUTORIAL_COLLECTION}'): "
    ).strip()
    active_collections = [c.strip() for c in collections_input.split(",") if c.strip()] or None

    if active_collections:
        for col_name in active_collections:
            client.get_or_create_collection(name=col_name)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("[Goodbye]")
                break
            result = chat_raw(user_input, collection_names=active_collections)
            print(f"\nDevbot: {result['answer']}")
        except KeyboardInterrupt:
            print("\n[Session Ended]")
            break
