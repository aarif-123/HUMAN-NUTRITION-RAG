import requests
import torch
from sentence_transformers import SentenceTransformer
from ..config import SUPABASE_URL, HEADERS

# Initialize Device and Model
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[STATUS] Vector Service: Initializing on {device}")

# E5 models require 'query:' prefix for retrieval
model = SentenceTransformer("intfloat/e5-base-v2", device=device)


def get_embedding(text: str):
    """Generate normalized embeddings for a given text."""
    return model.encode(f"query: {text}", normalize_embeddings=True).tolist()

def match_documents(query_embedding: list, match_count: int = 5):
    """Query Supabase RPC to find matching document chunks."""
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
