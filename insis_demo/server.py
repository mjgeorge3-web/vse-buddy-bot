"""Lightweight HTTP server for InSIS Demo Website & Embedded VŠE Buddy Bot API.

Serves static InSIS web files on port 8502 and provides a /api/chat endpoint
connected to the underlying BuddyBot RAG engine.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from pathlib import Path

# Ensure parent directory (vse-buddy-bot) is in python path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import BuddyBot lazily
_bot = None

def get_bot():
    global _bot
    if _bot is None:
        try:
            from bot import BuddyBot
            _bot = BuddyBot()
        except Exception as e:
            print(f"[Server Warning] Could not initialize BuddyBot: {e}")
            _bot = None
    return _bot


class InSISDemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve files from insis_demo directory
        demo_dir = str(Path(__file__).resolve().parent)
        super().__init__(*args, directory=demo_dir, **kwargs)

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(body)
                question = data.get("question", "")
                history = data.get("history", [])

                bot = get_bot()
                if bot:
                    result = bot.answer(question=question, history=history)
                    resp_data = {
                        "status": "success",
                        "answer": result.get("answer", ""),
                        "mode": result.get("mode", "normal"),
                        "sources": result.get("sources", []),
                        "top_score": result.get("top_score", 0.0),
                        "latency_ms": result.get("latency_ms", 0.0),
                    }
                else:
                    resp_data = {
                        "status": "fallback",
                        "answer": "Backend bot currently unavailable. Using offline verified knowledge.",
                        "mode": "fallback",
                    }
            except Exception as e:
                resp_data = {
                    "status": "error",
                    "answer": f"Error processing query: {str(e)}",
                    "mode": "error",
                }

            resp_bytes = json.dumps(resp_data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run(port=8502):
    server_address = ("", port)
    httpd = HTTPServer(server_address, InSISDemoHandler)
    print(f"============================================================")
    print(f"🚀 InSIS Demo Website running at: http://localhost:{port}")
    print(f"🎓 Embedded VŠE Buddy Bot API ready at: http://localhost:{port}/api/chat")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping InSIS Demo Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8502))
    run(port)
