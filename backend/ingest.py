import os
import fitz  # PyMuPDF
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "jeffh/intfloat-e5-base-v2"

# Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_embedding(text: str, is_passage: bool = True):
    prefix = "passage: " if is_passage else "query: "
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": MODEL_NAME, "prompt": f"{prefix}{text}"}
        )
        res.raise_for_status()
        return res.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return []


def ingest_pdf(file_path):
    print(f"ðŸ“„ Ingesting {file_path}...")
    doc = fitz.open(file_path)  
    doc_id = os.path.basename(file_path)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
       
        # Chunking (Simple by page for now)
        if not text.strip():
            continue
           
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
       
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk, is_passage=True)
           
            data = {
                "doc_id": doc_id,
                "chunk_index": i,
                "content": chunk,
                "metadata": {"page_number": page_num + 1, "source": file_path},
                "embedding": embedding
            }
           
            supabase.table("chunks").insert(data).execute()
            print(f"âœ… Page {page_num + 1}, Chunk {i} inserted into 'chunks' table.")


if __name__ == "__main__":
    # Example usage
    # ingest_pdf("path/to/nutrition_manual.pdf")
    print("Run this script with a PDF path to ingest documents into Supabase.")
