import os
import sys
import uuid
import fitz
import docx2txt
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
# Import shared objects from the config file
from config import client, embed_func

# ----------------- Text Extraction -----------------
def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    text = ""
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
    elif ext in [".docx", ".doc"]:
        text = docx2txt.process(file_path)
    elif ext in [".txt", ".md", ".py", ".html", ".js", ".json", ".xml"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    return text

# ----------------- Text Splitting -----------------
def split_text(text: str, file_type: str):
    # Use a specialized splitter for programming languages
    if file_type in [".py", ".js", ".md", ".json"]:
        lang = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".md": Language.MARKDOWN,
            ".json": Language.JSON,
        }.get(file_type)
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang, chunk_size=1000, chunk_overlap=100
        )
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " ", ""],
        )
    
    return splitter.split_text(text)

# ----------------- Store in ChromaDB (with batching) -----------------
def store_chunks(chunks, collection_name: str):
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_func
    )

    documents = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        ids.append(f"{collection_name}-{i}")
    
    collection.add(
        documents=documents,
        ids=ids
    )

# ----------------- Reusable Ingest Function -----------------
def ingest_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"[INFO] Extracting text from {file_path} ...")
    raw_text = extract_text(file_path)

    print(f"[INFO] Splitting text into chunks ...")
    file_type = Path(file_path).suffix.lower()
    chunks = split_text(raw_text, file_type)
    print(f"[INFO] Created {len(chunks)} chunks.")

    collection_name = f"doc_{Path(file_path).stem}_{uuid.uuid4().hex[:6]}"
    print(f"[INFO] Storing in ChromaDB collection: {collection_name}")

    store_chunks(chunks, collection_name)

    print(f"[INFO] Ingested {len(chunks)} chunks into collection '{collection_name}'")
    return collection_name

# ----------------- CLI Support -----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_document.py <path-to-document>")
        sys.exit(1)

    file_path = sys.argv[1]
    ingest_file(file_path)
