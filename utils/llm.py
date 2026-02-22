import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("XAI_API_KEY")

CHAT_URL = "https://api.x.ai/v1/chat/completions"
EMBED_URL = "https://api.x.ai/v1/embeddings"


# 🔹 LLM CALL
def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "grok-beta",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(CHAT_URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()


# 🔹 EMBEDDING FOR RAG
def get_embedding(text: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "text-embedding-3-small",
        "input": text
    }

    response = requests.post(EMBED_URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["data"][0]["embedding"]