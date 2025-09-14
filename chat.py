import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import psycopg2
from datetime import datetime
import requests
import json
import hashlib

# Constants
TUTORIAL_COLLECTION = "python_tutorial"
MEMORY_COLLECTION = "user_memory"
VECTORSTORE_PATH = "./vectorstore"
EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-coder:6.7b"

# PostgreSQL config
PG_HOST = "localhost"
PG_DB = "devbot_db"
PG_USER = "devbot_user"
PG_PASS = "123456"

# Setup ChromaDB (Ephemeral = no disk writes, works anywhere)
try:
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
except PermissionError:
    client = chromadb.EphemeralClient()

embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

# Load collections
tutorial = client.get_or_create_collection(name=TUTORIAL_COLLECTION, embedding_function=embed_func)
memory = client.get_or_create_collection(name=MEMORY_COLLECTION, embedding_function=embed_func)

embed = SentenceTransformer(EMBED_MODEL)

# Helper: Generate a unique hash for memory logging
def make_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

# Retrieve memory and tutorial context
def retrieve_context(query, top_k=5):
    try:
        tutorial_results = tutorial.query(query_texts=[query], n_results=top_k)
        memory_results = memory.query(query_texts=[query], n_results=top_k)
    except Exception as e:
        print(f"[Context Retrieval Error]: {e}")
        return []

    tutorial_chunks = tutorial_results.get("documents", [[]])[0]
    memory_chunks = memory_results.get("documents", [[]])[0]
    return tutorial_chunks + memory_chunks

# Query DeepSeek-Coder via Ollama
def query_llm(prompt, model=LLM_MODEL):
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"[LLM Error {response.status_code}] {response.text}"
    except requests.exceptions.RequestException as e:
        return f"[Connection Error] {e}"

# Log question and answer to memory
def log_to_memory(question: str, answer: str, embed):
    q_hash = make_hash(question)
    existing = memory.get()
    existing_hashes = {make_hash(doc): doc for doc in existing.get("documents", [])}

    if q_hash in existing_hashes:
        return  # Skip duplicate

    uid = str(uuid.uuid4())
    memory.add(
        ids=[uid],
        documents=[question],
        metadatas=[{"answer": answer}],
        embeddings=[embed.encode(question)]
    )
    
    # Also log to PostgreSQL
    log_to_postgres(question, answer)

def log_to_postgres(question: str, answer: str):
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute(
            "INSERT INTO chat_history (question, answer) VALUES (%s, %s)",
            (question, answer)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[PostgreSQL Logging Error]: {e}")

def get_chat_history(limit=20):
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT question, answer, timestamp
            FROM chat_history
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"question": row[0], "answer": row[1], "timestamp": row[2].isoformat()} for row in rows]
    except Exception as e:
        print(f"[PostgreSQL Retrieval Error]: {e}")
        return []

# Unified response: returns only string
def chat_response(user_input: str) -> str:
    result = chat_raw(user_input)
    return result["answer"]

# UI-friendly: returns dict with question + answer
def chat_raw(user_input: str) -> dict:
    context_chunks = retrieve_context(user_input)
    context = "\n\n".join(context_chunks) if context_chunks else "[No relevant memory/tutorial found.]"

    full_prompt = f"""You are a helpful assistant for Python developers.
Use CONTEXT and MEMORY to answer the QUESTION clearly and precisely. If code is given, analyze or modify it as needed.

### CONTEXT ###
{context}

### QUESTION ###
{user_input}

### RESPONSE ###
"""
    ai_response = query_llm(full_prompt)
    log_to_memory(user_input, ai_response, embed)
    return {"question": user_input, "answer": ai_response.strip()}
    
# UI entrypoint
def chat(user_input: str) -> str:
    """
    Wrapper for Streamlit UI.
    Takes user input string and returns chatbot's answer string.
    """
    return chat_response(user_input)

if __name__ == "__main__":
    print("Devbot (Private Python Assistant using DeepSeek-Coder)\nType 'exit' or 'quit' to end the session.")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip().lower() in {"exit", "quit"}:
                print("[Goodbye]")
                break
            result = chat_raw(user_input)
            print(f"\nDevbot: {result['answer']}")
        except KeyboardInterrupt:
            print("\n[Session Ended]")
            break
