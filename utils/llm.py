import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("XAI_API_KEY")

def call_llm(prompt: str) -> str:

    url = "https://api.x.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "grok-2-latest",   # ✅ safest working model
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(url, headers=headers, json=payload)

    # 👇 VERY IMPORTANT FOR DEBUGGING
    if response.status_code != 200:
        print(response.text)

    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


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