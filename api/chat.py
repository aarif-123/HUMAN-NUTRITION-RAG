import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Ensure repository root is importable in Vercel runtime.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from backend.app.services.llm_service import generate_response, format_rag_prompt
from backend.app.services.vector_store import get_embedding, match_documents


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("content-length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            body = json.loads(raw_body.decode("utf-8"))
            message = str(body.get("message", "")).strip()

            if not message:
                self._send_json(400, {"detail": "Field 'message' is required."})
                return

            vector = get_embedding(message)
            chunks = match_documents(vector)

            if not chunks:
                self._send_json(
                    200,
                    {
                        "answer": "No relevant research found in our nutrition database for this specific query.",
                        "sources": [],
                    },
                )
                return

            prompt = format_rag_prompt(message, chunks)
            answer, debug_info = generate_response(prompt)

            if not answer:
                print(f"[DEBUG] Empty response from Ollama: {debug_info}")
                answer = "I found the research, but the AI generated an empty response. Please try rephrasing."

            self._send_json(200, {"answer": answer, "sources": chunks})
        except Exception as exc:
            print(f"[FATAL] Chat function error: {exc}")
            self._send_json(500, {"detail": str(exc)})

    def do_GET(self):
        self._send_json(405, {"detail": "Method Not Allowed"})
