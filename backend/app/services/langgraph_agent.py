"""
langgraph_agent.py
------------------
LangGraph-orchestrated multi-step RAG agent for Nutri-RAG.

Graph topology
~~~~~~~~~~~~~~

    START
      │
      ▼
  classify_intent
      │
      ├─ NUTRITION ──► retrieve_context ──► generate_answer ──┐
      │                                                        │
      └─ GREETING / OFFTOPIC ──► generate_direct_response ────┤
                                                              │
                                                              ▼
                                                      save_to_history
                                                              │
                                                             END

Nodes
~~~~~
- ``classify_intent``       — Groq LLM classifies query into NUTRITION/GREETING/OFFTOPIC
- ``retrieve_context``      — Embeds query, runs pgvector search via Supabase
- ``generate_answer``       — Groq LLM generates a grounded, cited answer
- ``generate_direct_response`` — Groq LLM handles greetings / off-topic politely
- ``save_to_history``       — Appends current turn to the in-memory conversation history

Conversation memory is persisted across turns within a session using
LangGraph's ``MemorySaver`` keyed on ``thread_id`` (= ``session_id``).
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.config import GROQ_API_KEY, RELEVANCE_THRESHOLD
from app.core.logging_config import logger
from app.services.vector_store import get_embedding, match_documents

# ---------------------------------------------------------------------------
# LLM initialisation
# ---------------------------------------------------------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY,
    temperature=0.2,
    max_retries=2,  # automatic retry on transient Groq errors
)


# ---------------------------------------------------------------------------
# Agent state schema
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Shared mutable state passed through every node in the graph."""

    query: str
    history: List[BaseMessage]
    intent: str
    chunks: List[Dict[str, Any]]
    response: str


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

_INTENT_SYSTEM_PROMPT = (
    "You are an intent classification routing engine for a RAG chatbot. "
    "Classify the user query into exactly ONE of three categories:\n"
    "1. 'NUTRITION' — if the query is about nutrition, vitamins, diet, biology, "
    "health research, metabolism, food composition, OR is a follow-up to a previous "
    "nutrition topic in the conversation history.\n"
    "2. 'GREETING' — if the query is a friendly greeting or introduction "
    "(e.g. 'hi', 'hello', 'who are you?').\n"
    "3. 'OFFTOPIC' — if the query is unrelated to nutrition, biology, or greetings.\n\n"
    "Respond with ONLY one word: NUTRITION, GREETING, or OFFTOPIC."
)


def classify_intent(state: AgentState) -> dict:
    """Classify the user query into NUTRITION, GREETING, or OFFTOPIC."""
    query = state["query"]
    history = state.get("history", [])

    messages: List[BaseMessage] = [SystemMessage(content=_INTENT_SYSTEM_PROMPT)]
    # Include the last 4 messages (= 2 full turns) for context-aware routing
    if history:
        messages.extend(history[-4:])
    messages.append(HumanMessage(content=query))

    try:
        result = llm.invoke(messages)
        raw_intent = result.content.strip().upper()
        if "NUTRITION" in raw_intent:
            intent = "NUTRITION"
        elif "GREETING" in raw_intent:
            intent = "GREETING"
        else:
            intent = "OFFTOPIC"
    except Exception as exc:
        logger.error(f"Intent classification failed: {exc}", exc_info=True)
        intent = "NUTRITION"  # safe fallback — still attempts retrieval

    logger.info(f"Intent classified as: {intent}")
    return {"intent": intent}


def retrieve_context(state: AgentState) -> dict:
    """Embed the query and retrieve relevant document chunks from Supabase."""
    query = state["query"]
    try:
        embedding = get_embedding(query)
        chunks = match_documents(embedding, match_count=5)
        # Filter chunks by relevance similarity threshold
        relevant_chunks = [
            c for c in chunks if c.get("similarity", 0.0) >= RELEVANCE_THRESHOLD
        ]
        logger.info(
            f"Retrieved {len(chunks)} context chunks, "
            f"filtered to {len(relevant_chunks)} relevant chunks (threshold >= {RELEVANCE_THRESHOLD})."
        )
        chunks = relevant_chunks
    except Exception as exc:
        logger.error(f"Context retrieval failed: {exc}", exc_info=True)
        chunks = []
    return {"chunks": chunks}


_RAG_SYSTEM_TEMPLATE = """\
You are Nutri-RAG, an AI Research Assistant specialised in human nutrition science.
Your task is to answer the User Question based ONLY on the provided Research Context.

RESEARCH CONTEXT:
{context}

INSTRUCTIONS:
1. Use a professional, objective, academic tone.
2. Structure your answer with clear headings (###) and bullet points where appropriate.
3. Cite sources using [1], [2], etc., corresponding to RESEARCH_BLOCK numbers.
4. Bold key nutritional terms using **term**.
5. If the context is insufficient, state:
   "Based on the provided research documents, I cannot find enough information
   to answer this specific query reliably."
"""

_NO_CONTEXT_SYSTEM_PROMPT = (
    "You are Nutri-RAG, an AI Research Assistant specialised in human nutrition science.\n"
    "No relevant textbook sources or references were found in the database to answer the user's query.\n"
    "Politely inform the user that you could not find any relevant textbook sources or information "
    "in the database to answer their specific query, and suggest they ask another question related to human nutrition.\n"
    "Do NOT attempt to answer the query or provide information using general knowledge.\n"
    "Maintain a professional, polite, and helpful tone."
)


def generate_answer(state: AgentState) -> dict:
    """Generate a RAG-grounded response using retrieved context chunks."""
    query = state["query"]
    chunks = state.get("chunks", [])
    history = state.get("history", [])

    if not chunks:
        # No context retrieved — output polite refusal instead of answering from general knowledge
        messages: List[BaseMessage] = [SystemMessage(content=_NO_CONTEXT_SYSTEM_PROMPT)]
        messages.extend(history)
        messages.append(HumanMessage(content=query))
    else:
        context_text = "\n\n".join(
            f"RESEARCH_BLOCK_{i + 1} [DOC: {c.get('doc_id', 'unknown')}]: "
            f"{c.get('content', '').replace(chr(10), ' ').strip()}"
            for i, c in enumerate(chunks)
        )
        system_prompt = _RAG_SYSTEM_TEMPLATE.format(context=context_text)
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(history)
        messages.append(HumanMessage(content=query))

    try:
        result = llm.invoke(messages)
        response_text = result.content
    except Exception as exc:
        traceback.print_exc()
        logger.error(f"Groq generation failed: {exc}", exc_info=True)
        response_text = f"**AI Service Error:** {exc}"

    return {"response": response_text}


def generate_direct_response(state: AgentState) -> dict:
    """Handle greetings and off-topic queries without RAG retrieval."""
    query = state["query"]
    history = state.get("history", [])
    intent = state["intent"]

    if intent == "GREETING":
        system_prompt = (
            "You are Nutri-RAG, a friendly AI Research Assistant specialised in human "
            "nutrition science. Greet the user warmly, briefly explain what you can do "
            "(answer questions grounded in nutrition textbooks), and invite them to ask "
            "their first question."
        )
    else:
        system_prompt = (
            "You are Nutri-RAG, an AI Research Assistant specialised in human nutrition. "
            "Politely inform the user that their query is outside your area of expertise "
            "(human nutrition and health science), and guide them back to nutrition topics. "
            "Do not attempt to answer unrelated questions."
        )

    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    messages.extend(history)
    messages.append(HumanMessage(content=query))

    try:
        result = llm.invoke(messages)
        response_text = result.content
    except Exception as exc:
        logger.error(f"Direct response generation failed: {exc}", exc_info=True)
        response_text = f"**AI Service Error:** {exc}"

    return {"response": response_text}


def save_to_history(state: AgentState) -> dict:
    """Append the current query/response turn to the conversation history."""
    query = state["query"]
    response = state["response"]
    history = list(state.get("history", []))

    history.append(HumanMessage(content=query))
    history.append(AIMessage(content=response))

    return {"history": history}


# ---------------------------------------------------------------------------
# Conditional router
# ---------------------------------------------------------------------------

def _route_intent(state: AgentState) -> str:
    """Return the next node name based on the classified intent."""
    return "retrieve_context" if state["intent"] == "NUTRITION" else "generate_direct_response"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

_workflow = StateGraph(AgentState)

_workflow.add_node("classify_intent", classify_intent)
_workflow.add_node("retrieve_context", retrieve_context)
_workflow.add_node("generate_answer", generate_answer)
_workflow.add_node("generate_direct_response", generate_direct_response)
_workflow.add_node("save_to_history", save_to_history)

_workflow.add_edge(START, "classify_intent")
_workflow.add_conditional_edges(
    "classify_intent",
    _route_intent,
    {
        "retrieve_context": "retrieve_context",
        "generate_direct_response": "generate_direct_response",
    },
)
_workflow.add_edge("retrieve_context", "generate_answer")
_workflow.add_edge("generate_answer", "save_to_history")
_workflow.add_edge("generate_direct_response", "save_to_history")
_workflow.add_edge("save_to_history", END)

# Compiled agent — MemorySaver persists per-thread history in-process
_memory = MemorySaver()
query_agent = _workflow.compile(checkpointer=_memory)

logger.info("LangGraph RAG agent compiled and ready.")
