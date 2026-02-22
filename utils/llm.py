import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("XAI_API_KEY")

URL = "https://api.x.ai/v1/chat/completions"


def call_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "grok-beta",   # you can change later
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(URL, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"].strip()