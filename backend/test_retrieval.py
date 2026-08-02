#!/usr/bin/env python
"""
test_retrieval.py
-----------------
A utility script to test embedding generation and document retrieval.
Generates an embedding for a user query using the core vector store
(which tries HuggingFace first and falls back to local Ollama if offline),
queries the Supabase vector store, and displays the top matching chunks.
"""

import sys
import os
from dotenv import load_dotenv

# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import setup_logging
from app.services.vector_store import get_embedding, match_documents

def main():
    # Initialize logging using the existing app configuration
    setup_logging("INFO")
    
    # 1. Get the query from command-line arguments or use a default one
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is the role of Vitamin C in collagen synthesis?"
        
    print("=" * 80)
    print(f"QUERY: '{query}'")
    print("=" * 80)
    
    # 2. Generate the embedding
    print("\n[1/2] Generating query embedding...")
    embedding = get_embedding(query)
    
    if not embedding:
        print("ERROR: Failed to generate embedding via both HuggingFace and local Ollama.")
        sys.exit(1)
        
    print(f"Success! Embedding Dimensions: {len(embedding)}")
    print(f"First 5 vector values: {embedding[:5]}")
    
    # 3. Retrieve documents matching the embedding from Supabase
    print("\n[2/2] Retrieving relevant document chunks from Supabase...")
    matches = match_documents(embedding, match_count=5)
    
    if not matches:
        print("No documents matched or an error occurred during Supabase retrieval.")
        sys.exit(0)
        
    print(f"Found {len(matches)} matching document chunks in Supabase:")
    print("-" * 80)
    
    for idx, match in enumerate(matches, 1):
        similarity = match.get("similarity", 0.0)
        doc_id = match.get("doc_id", "Unknown")
        chunk_index = match.get("chunk_index", 0)
        content = match.get("content", "")
        
        # Format and display the chunk information
        print(f"Match #{idx} | Similarity: {similarity:.4f} | Document: {doc_id} | Chunk: {chunk_index}")
        # Print a snippet of the content with nice indentation
        content_snippet = content.strip().replace("\n", " ")
        if len(content_snippet) > 300:
            content_snippet = content_snippet[:300] + "..."
        print(f"Content: {content_snippet}")
        print("-" * 80)

if __name__ == "__main__":
    main()
