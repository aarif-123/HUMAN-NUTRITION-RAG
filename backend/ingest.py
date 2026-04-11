import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
MODEL_NAME = "intfloat/e5-base-v2"

# Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = SentenceTransformer(MODEL_NAME)


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
            # Prep for E5 model (requires 'passage: ' prefix)
            embedding = model.encode(
                f"passage: {chunk}",
                normalize_embeddings=True
            ).tolist()
           
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
