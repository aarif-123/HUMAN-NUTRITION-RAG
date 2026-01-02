# server.py — Embedding Server (E5-base-v2 + GPU)

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import torch

# --------------------------------------------------
# App
# --------------------------------------------------
app = FastAPI(
    title="Embedding Server",
    description="E5-base-v2 embedding service for RAG",
    version="1.0"
)

# --------------------------------------------------
# Device
# --------------------------------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔥 Embedding server running on: {device}")

# --------------------------------------------------
# Load model (ONCE)
# --------------------------------------------------
model = SentenceTransformer(
    "intfloat/e5-base-v2",
    device=device
)

# --------------------------------------------------
# Request schema
# --------------------------------------------------
class EmbedRequest(BaseModel):
    text: str

# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "device": device}

# --------------------------------------------------
# Embed endpoint
# --------------------------------------------------
@app.post("/embed")
def embed(req: EmbedRequest):
    """
    Input:
      { "text": "query: your question here" }

    Output:
      { "embedding": [float, float, ...] }
    """
    embedding = model.encode(
        req.text,
        normalize_embeddings=True
    ).tolist()

    return {"embedding": embedding}
