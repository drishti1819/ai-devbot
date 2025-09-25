import requests
import json

LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-coder:6.7b"
TEST_PROMPT = "What is the capital of France?"

headers = {"Content-Type": "application/json"}
data = {"model": LLM_MODEL, "prompt": TEST_PROMPT, "stream": False}

try:
    response = requests.post(LLM_ENDPOINT, headers=headers, data=json.dumps(data))
    response.raise_for_status() # Raise an exception for bad status codes
    
    response_json = response.json()
    ai_response = response_json.get("response", "")
    
    print("Ollama LLM connection successful!")
    print(f"Model: {LLM_MODEL}")
    print(f"Response: {ai_response}")
    
except requests.exceptions.RequestException as e:
    print("Error connecting to Ollama LLM.")
    print(f"Error details: {e}")
    print("Please ensure Ollama is running (e.g., `ollama serve`) and the model `deepseek-coder:6.7b` is pulled.")
