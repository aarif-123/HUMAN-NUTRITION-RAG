import requests
from ..config import OLLAMA_URL, OLLAMA_MODEL

def generate_response(prompt: str):
    """Call Ollama API to generate a response based on the provided prompt."""
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/generate", 
            json={
                "model": OLLAMA_MODEL, 
                "prompt": prompt, 
                "stream": False
            }, 
            timeout=75
        )
        res.raise_for_status()
        resp_json = res.json()
        return resp_json.get("response", "").strip(), resp_json
    except Exception as e:
        print(f"[ERROR] Ollama Service Error: {str(e)}")
        return f"AI Service Error: {str(e)}", None

def format_rag_prompt(question: str, chunks: list):
    """Format the RAG prompt from chunks and user question."""
    context_blocks = []
    for i, c in enumerate(chunks):
        content_snippet = c['content'].replace('\n', ' ').strip()
        context_blocks.append(f"RESEARCH_BLOCK_{i+1} [DOC: {c['doc_id']}]: {content_snippet}")
        
    context_text = "\n\n".join(context_blocks)
    
    return f"""You are Nutri-RAG, an AI Research Assistant. 
Your task is to answer the Question based ONLY on the provided Research Context.

RESEARCH CONTEXT:
{context_text}

USER QUESTION: 
{question}

INSTRUCTIONS:
1. Use a professional tone.
2. Structure your answer with clear headings (###) and bullet points.
3. Cite sources using [1], [2], etc., corresponding to RESEARCH_BLOCK numbers.
4. Bold key nutritional terms.
5. If the context doesn't have the answer, say "Based on the provided research documents, I cannot find information to answer this specific query."

ANSWER:"""
