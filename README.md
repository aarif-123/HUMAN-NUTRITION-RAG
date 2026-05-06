# 🥗 HUMAN NUTRITION RAG CHATBOT

<p align="center">
  <img src="rag-ollama-diagram-c5e713fbc8bc1592f586a3107587519b.png" alt="System Architecture Diagram" width="800"/>
</p>

**Human Nutrition RAG Chatbot** is a full-stack **Retrieval-Augmented Generation (RAG)** system designed to answer nutrition-related questions using **human nutrition textbooks** as the sole source of truth.

Unlike generic chatbots, this system **grounds every response in retrieved textbook content**, significantly reducing hallucinations and improving factual reliability. The LLM runs **locally via Ollama**, ensuring privacy, offline capability, and full control over inference.

---

## 🎥 Demo Video

Below is a clickable thumbnail that opens the full demo on YouTube.  
(GitHub does not support embedded iframes in READMEs.)

[![Watch the demo](https://img.youtube.com/vi/98OSscUckXY/hqdefault.jpg)](https://youtu.be/98OSscUckXY)

🔗 Direct link: https://youtu.be/98OSscUckXY

---

## ✨ Key Features

- 📚 **Retrieval-Augmented Generation (RAG)**  
  Retrieves relevant textbook chunks before generating answers.

- 🧠 **Local LLM Inference**  
  Uses **Gemma-2B via Ollama**, running entirely on the local machine.

- 🔒 **Privacy-First Architecture**  
  No external LLM APIs required during inference.

- 📊 **Vector Search with Supabase**  
  Stores and queries embeddings using cosine similarity.

- 🔍 **Source-Aware Responses**  
  Each answer includes **references to the retrieved document chunks**.

- 🌗 **Modern UI**  
  Responsive interface built with **Next.js + Tailwind CSS**.

---

## 🧠 System Architecture (High Level)

```text
Human Nutrition PDF
        ↓
Chunking & Embedding
        ↓
Supabase (Vector Storage)
        ↓
User Query → Embedding
        ↓
Similarity Search (Cosine)
        ↓
Relevant Chunks
        ↓
Ollama (Gemma-2B)
        ↓
Answer + Source References
        ↓
Next.js Frontend
````

---

## 🛠️ Tech Stack

### Frontend

* **Framework:** Next.js 14 (App Router)
* **Language:** TypeScript
* **Styling:** Tailwind CSS
* **Icons:** Lucide React
* **Markdown Rendering:** `react-markdown`

### Backend & AI

* **LLM Runtime:** Ollama (Local)
* **Model:** Gemma-2B
* **Embedding Service:** Python (FastAPI / local service)
* **Vector Database:** Supabase (pgvector)
* **Similarity Metric:** Cosine Similarity

---

## 📂 Project Structure (Simplified)

```text
rag-chat/
├── public/                   # Static assets (icons, images)
├── src/
│   ├── app/                  # Next.js App Router (UI + API routes)
│   │   ├── page.tsx          # Main chat interface
│   │   └── api/route.ts      # RAG pipeline (query → retrieval → LLM)
│   
│   ├── models/               # Prompt templates / response schemas
│   └── middleware.ts         # Next.js middleware (routing / security)
│
├── human-nutrition-text.pdf  # Source Human Nutrition textbook
├── ingest.py                 # PDF ingestion & embedding generation
├── test_embeddings.py        # Embedding similarity testing script
│
├── .env.local                # Local environment variables
├── .env                      # Environment config (ignored in prod)
├── package.json              # Node.js dependencies
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.ts        # Tailwind CSS config
├── postcss.config.mjs        # PostCSS config
├── eslint.config.mjs         # ESLint rules
├── README.md                 # Project documentation
└── .gitignore                # Git ignore rules

```

---

## 🚀 Getting Started

This project requires **three running components**:

1. Embedding service
2. Ollama (local LLM)
3. Next.js frontend

---

### ✅ Prerequisites

* Node.js (v18+)
* Python (v3.10+)
* Ollama → [https://ollama.com](https://ollama.com)
* Supabase project with `pgvector` enabled

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/HUMAN-NUTRITION-RAG.git
cd HUMAN-NUTRITION-RAG.git
```

---

### 2️⃣ Run Ollama (Local LLM)

```bash
ollama pull gemma:2b
ollama serve
```

Ollama runs at:

```
http://127.0.0.1:11434
```

---

### 3️⃣ Start Embedding Server (Python)

```bash
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install fastapi uvicorn sentence-transformers torch
python server.py
```

Embedding server runs at:

```
http://127.0.0.1:8000
```

---

### 4️⃣ Setup Frontend (Next.js)

```bash
npm install
npm run dev
```

Open:

```
http://localhost:3000
```

---

## 🔧 Troubleshooting

### Ollama crashes due to GPU memory

Force CPU mode:

```powershell
$env:OLLAMA_NUM_GPU=0
ollama serve
```

---

### Port 3000 already in use

```powershell
taskkill /F /IM node.exe
```

---

## ☁️ Deployment Notes

* Frontend can be deployed on **Vercel**
* Ollama and embedding services **must run on a persistent server or local machine**
* For cloud-only deployment, replace Ollama with a hosted LLM API

---

## 🎯 Use Cases

* Nutrition education & learning
* Academic question answering
* Domain-specific RAG experimentation
* Offline & privacy-preserving AI assistants

---

## 📜 License

This project is intended for **educational and research purposes only**.

```
