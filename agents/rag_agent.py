from utils.db import execute_query
from utils.llm import call_llm, get_embedding
from utils.intent_guard import is_smartcity_query
import json


def detect_domain(query: str) -> str:

    q = query.lower()

    if "traffic" in q or "congestion" in q:
        return "traffic"

    if "air" in q or "aqi" in q or "pollution" in q:
        return "air_quality"

    if "complaint" in q:
        return "complaints"

    if "pothole" in q or "infrastructure" in q or "streetlight" in q:
        return "infra"

    if "crowd" in q or "overcrowd" in q or "density" in q:
        return "crowd"

    if "accident" in q or "crash" in q or "collision" in q:
        return "accident"

    return None


def handle_rag_query(user_query: str):

    # DOMAIN GUARD
    if not is_smartcity_query(user_query):
        return "I can answer only Smart City knowledge queries."

    # DETECT DOMAIN 
    domain = detect_domain(user_query)

    # CREATE QUERY EMBEDDING
    query_vector = get_embedding(user_query)
    query_vector_str = str(query_vector)

    # BUILD SQL
    if domain:
        sql = f"""
        SELECT text_chunk, source_reference
        FROM rag_documents
        WHERE source_type = '{domain}'
        ORDER BY DOT_PRODUCT(
            embedding_vector,
            CAST('{query_vector_str}' AS VECTOR)
        ) DESC
        LIMIT 5
        """
    else:
        sql = f"""
        SELECT text_chunk, source_reference
        FROM rag_documents
        ORDER BY DOT_PRODUCT(
            embedding_vector,
            CAST('{query_vector_str}' AS VECTOR)
        ) DESC
        LIMIT 5
        """

    rows = execute_query(sql)

    if not rows:
        return "No relevant Smart City knowledge found."

    # BUILD CONTEXT
    context = "\n".join([r["text_chunk"] for r in rows])

    # LLM ANSWER 
    prompt = f"""
You are a Smart City AI assistant.

Answer using ONLY the provided context.

Rules:
- Do NOT use external knowledge
- If the answer is not in the context → say:
  "This information is not available in the Smart City knowledge base."
- Keep it concise and factual
- No greetings
- No assumptions

Context:
{context}

Question:
{user_query}
"""

    return call_llm(prompt)