import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL="https://yqwrstdhsuulisdosycb.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlxd3JzdGRoc3V1bGlzZG9zeWNiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTk0NjIyMywiZXhwIjoyMDc1NTIyMjIzfQ.2UgIJEifthhyUCxfFu6LEWQQfL81RPxGEpgIizZKQFE"

# Ollama Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

# API Headers
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
