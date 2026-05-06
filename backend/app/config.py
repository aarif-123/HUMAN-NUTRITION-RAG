import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Ollama Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "jeffh/intfloat-e5-base-v2:f32")

# Embedding model used for vector search (must match ingest model family)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jeffh/intfloat-e5-base-v2:f32")

# API Headers
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
