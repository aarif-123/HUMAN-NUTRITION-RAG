#!/usr/bin/env python
"""
test_agent.py
-------------
Verifies the multi-turn conversational routing and query reformulation of the
updated LangGraph RAG agent.
"""

import sys
import os
import uuid

# Ensure the backend directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging_config import setup_logging
from app.services.langgraph_agent import query_agent

def run_turn(session_id: str, message: str):
    print("\n" + "=" * 80)
    print(f"USER: {message}")
    print("=" * 80)
    
    config = {"configurable": {"thread_id": session_id}}
    # Omit history, chunks, and response to let LangGraph retrieve them from the checkpoint
    inputs = {
        "query": message,
    }
    
    # Execute the LangGraph workflow
    output = query_agent.invoke(inputs, config=config)
    
    # Extract details
    intent = output.get("intent", "UNKNOWN")
    chunks = output.get("chunks", [])
    response = output.get("response", "No response generated.")
    
    print(f"\n[AGENT DECISION]")
    print(f"-> Classified Intent: {intent}")
    print(f"-> Retrieved Chunks: {len(chunks)}")
    if chunks:
        print(f"-> Top Similarity Score: {chunks[0].get('similarity', 0.0):.4f}")
        print(f"-> Source Doc: {chunks[0].get('doc_id', 'Unknown')}")
        
    print(f"\n[AI RESPONSE]")
    print(response)
    print("-" * 80)

def main():
    # Initialize logging using the existing app configuration
    setup_logging("INFO")
    
    # Generate a unique thread session ID
    session_id = str(uuid.uuid4())
    print(f"Starting conversation session: {session_id}")
    
    # Turn 1: Conversational greeting (should trigger DIRECT_CHAT, no retrieval)
    run_turn(session_id, "Hello! Who are you and what do you do?")
    
    # Turn 2: Factual nutrition query (should trigger RETRIEVAL_QUERY, fetch chunks)
    run_turn(session_id, "What are the major symptoms of scurvy?")
    
    # Turn 3: Follow-up query with contextual pronoun (should trigger RETRIEVAL_QUERY, reformulate query, fetch chunks)
    run_turn(session_id, "Which vitamin deficiency causes it?")
    
if __name__ == "__main__":
    main()
