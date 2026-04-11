# ðŸ¥— HUMAN NUTRITION RAG CHATBOT

<p align="center">
  <img src="rag-ollama-diagram-c5e713fbc8bc1592f586a3107587519b.png" alt="System Architecture Diagram" width="800"/>
</p>

**Human Nutrition RAG Chatbot** is a full-stack **Retrieval-Augmented Generation (RAG)** system designed to answer nutrition-related questions using **human nutrition textbooks** as the sole source of truth.

This project demonstrates a production-grade architecture focusing on **local inference**, **modular software design**, and **system observability**.

---

## ðŸŽ¥ Demo Video

Below is a clickable thumbnail that opens the full demo on YouTube.  
(GitHub does not support embedded iframes in READMEs.)

[![Watch the demo](https://img.youtube.com/vi/98OSscUckXY/hqdefault.jpg)](https://youtu.be/98OSscUckXY)

ðŸ”— Direct link: https://youtu.be/98OSscUckXY

---

## âœ¨ Key Features

- ðŸ“š **Retrieval-Augmented Generation (RAG)**  
  Retrieves relevant textbook chunks before generating answers.

- ðŸ§  **Local LLM Inference**  
  Uses **Gemma-3 via Ollama**, running entirely on the local machine.

- ðŸ”’ **Privacy-First Architecture**  
  No external LLM APIs required during inference.

- ðŸ“Š **Vector Search with Supabase**  
  Stores and queries embeddings using cosine similarity.

- ðŸ” **Source-Aware Responses**  
  Each answer includes **references to the retrieved document chunks**.

- ðŸŒ— **Premium UI**  
  Gemini-inspired responsive interface built with **Vanilla HTML5/CSS3/JS**.

- ðŸ“ˆ **Observability**  
  Integrated **Prometheus & Grafana** for real-time API monitoring.

---

## ðŸ“‚ Project Structure

```text
rag-chat/
â”œâ”€â”€ backend/            # Modular FastAPI backend
â”‚   â”œâ”€â”€ app/            # Core logic (Config, Services)
â”‚   â”œâ”€â”€ main.py         # API entry point
â”‚   â””â”€â”€ Dockerfile      # Backend containerization
â”œâ”€â”€ frontend/           # Gemini-inspired UI (HTML/CSS/JS)
â”œâ”€â”€ ops/                # Infrastructure (Docker Compose, Prometheus, Grafana)
â”œâ”€â”€ start.ps1           # Automation script for Windows
â”œâ”€â”€ README.md           # Project documentation
â””â”€â”€ .gitignore          # Git ignore rules
```

---

## ðŸš€ One-Click Quick Start (Windows)

The project includes a smart automation script that handles environment setup and service orchestration.

```powershell
.\start.ps1
```

### ðŸ› ï¸ Execution Modes
- **Docker Mode**: Starts the full microservice stack (Backend, Prometheus, Grafana).
- **Local Mode**: Falls back to a standalone FastAPI backend serving the frontend directly.

Open [**http://localhost:8000**](http://localhost:8000) once initialized.

---

## ðŸ› ï¸ Tech Stack

### Frontend & UI
* **Vanilla HTML5/CSS3/JS**: Premium design with glassmorphism and micro-animations.
* **Custom Styles**: Hand-crafted CSS for a modern, high-end feel.

### Backend & AI
* **Framework**: FastAPI (Modular Service Architecture)
* **LLM Runtime**: Ollama (Local)
* **Model**: Gemma3
* **Vector Database**: Supabase (Remote Vector Search)
* **Observability**: Prometheus & Grafana

---

## ðŸ§  Interview Talking Points

1.  **Architecture**: "I migrated from a monolithic script to a **Modular Service Pattern**, separating the embedding service, vector store logic, and LLM orchestration."
2.  **UI/UX**: "Implemented a **Gemini-inspired interface** focusing on structured AI responses and context-aware source visualization."
3.  **Observability**: "Integrated **Prometheus** to track API performance and model latency, demonstrating a focus on production monitoring."
4.  **Privacy**: "The system uses **local embeddings and LLMs** (via Ollama), ensuring sensitive research data never leaves the local environment."

---

## ðŸ“œ License

This project is intended for **educational and research purposes only**.
Developed for the Vizuara RAG Challenge â€” Precision, Privacy, and Performance.
