import fitz
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
# Import shared objects from the config file
from config import client, embed_func
from pathlib import Path

# ----------------- Config -----------------
PDF_PATH = "tutorials/pythonlearn.pdf"
COLLECTION_NAME = "python_tutorial"

# ----------------- PDF Extraction -----------------
def extract_text_from_pdf(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text

# ----------------- Text Splitting -----------------
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

# ----------------- Store Chunks (with batching) -----------------
def store_chunks(chunks):
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_func
    )

    documents = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        ids.append(f"{COLLECTION_NAME}-{i}")

    collection.add(
        documents=documents,
        ids=ids
    )

# ----------------- CLI -----------------
if __name__ == "__main__":
    assert os.path.exists(PDF_PATH), f"PDF not found at {PDF_PATH}"
    print(f"Attempting to ingest tutorial from {PDF_PATH}...")
    try:
        raw_text = extract_text_from_pdf(PDF_PATH)
        chunks = split_text(raw_text)
        store_chunks(chunks)
        print(f"Ingested {len(chunks)} chunks into collection '{COLLECTION_NAME}' successfully.")
    except Exception as e:
        print(f"Failed to ingest tutorial: {e}")
