import requests
from ..config import EMBEDDING_MODEL, OLLAMA_URL, SUPABASE_URL, HEADERS


def get_embedding(text: str):
    """Generate query embeddings using Ollama (E5 model requires 'query: ' prefix)."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": f"query: {text}"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"[ERROR] Ollama embedding generation failed: {str(e)}")
        return []

def match_documents(query_embedding: list, match_count: int = 5):
    """Query Supabase RPC to find matching document chunks."""
    if not query_embedding:
        return []

    rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/match_documents"
    
    try:
        res = requests.post(
            rpc_url, 
            headers=HEADERS, 
            json={"query_embedding": query_embedding, "match_count": match_count}, 
            timeout=15
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"[ERROR] Supabase match error: {str(e)}")
        return []
