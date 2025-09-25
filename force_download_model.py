import os
import ssl
import requests
from sentence_transformers import SentenceTransformer
import certifi

# Set environment variable for requests to use the certifi bundle
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

model_name = "all-MiniLM-L6-v2"
model_path = os.path.join(os.path.expanduser('~'), '.cache', 'torch', 'sentence_transformers', model_name)

if not os.path.exists(model_path):
    print(f"Downloading {model_name}...")
    try:
        # Use a more explicit way to handle the cache
        model = SentenceTransformer(model_name, cache_folder=os.path.join(os.path.expanduser('~'), '.cache', 'torch', 'sentence_transformers'))
        print("Model downloaded and saved successfully.")
    except Exception as e:
        print(f"Error downloading model: {e}")
else:
    print("Model already exists locally. Skipping download.")
