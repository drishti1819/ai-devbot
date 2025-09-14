import fitz  # PyMuPDF
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

PDF_PATH = "tutorials/pythonlearn.pdf"
COLLECTION_NAME = "python_tutorial"

# Load the PDF
def extract_text_from_pdf(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text

# Split into chunks
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_text(text)

# Store into ChromaDB
def store_chunks(chunks):
    client = chromadb.PersistentClient(path="./db")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )

    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[f"{COLLECTION_NAME}-{i}"]
        )

if __name__ == "__main__":
    assert os.path.exists(PDF_PATH), f"PDF not found at {PDF_PATH}"
    raw_text = extract_text_from_pdf(PDF_PATH)
    chunks = split_text(raw_text)
    store_chunks(chunks)
    print(f"Ingested {len(chunks)} chunks into collection '{COLLECTION_NAME}'")
