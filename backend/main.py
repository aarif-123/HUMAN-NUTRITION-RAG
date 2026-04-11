import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

# Import modular components
from app.services.vector_store import get_embedding, match_documents
from app.services.llm_service import generate_response, format_rag_prompt

app = FastAPI(
    title="Nutri-RAG Modular API",
    description="Refactored RAG Backend for Human Nutrition Research",
    version="3.0"
)

# Enable observability
Instrumentator().instrument(app).expose(app)

# --- Schemas ---


class ChatRequest(BaseModel):
    message: str

# --- Endpoints ---


@app.get("/health")
def health():
    return {"status": "ok", "service": "Nutri-RAG Modular"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        print(f"\n--- Chat Request: {req.message} ---")
        
        # 1. Generate Embedding
        vector = get_embedding(req.message)
        print("[SUCCESS] Embedding generated.")

        # 2. Query Vector DB
        print("[SEARCH] Querying Supabase...")
        chunks = match_documents(vector)
        print(f"[SUCCESS] Supabase found {len(chunks)} snippets.")
        
        if not chunks:
            return {
                "answer": "No relevant research found in our nutrition database for this specific query.", 
                "sources": []
            }

        # 3. Augment Context & Generate Response
        prompt = format_rag_prompt(req.message, chunks)
        
        print("[AI] Calling Ollama Service...")
        answer, debug_info = generate_response(prompt)
        
        if not answer:
            print(f"[DEBUG] Empty response from Ollama: {debug_info}")
            answer = "I found the research, but the AI generated an empty response. Please try rephrasing."

        print("[SUCCESS] Request Complete.")

        return {
            "answer": answer,
            "sources": chunks
        }

    except Exception as e:
        print(f"[FATAL] Global Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Static Assets ---
# Serving from the root/frontend directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    print(f"[WARNING] Static directory not found at {static_dir}")

# --- Run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
