"""Lightweight HTTP server for InSIS Demo Website & Embedded VŠE Buddy Bot API.

Serves static InSIS web files on port 8502 and provides a /api/chat endpoint
connected to the underlying BuddyBot RAG engine.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
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

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_GET(self):
        # 1. API: InSIS Navigation Database Query
        if self.path.startswith("/api/insis/navigate"):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])

            try:
                import insis_nav_db
                routes = insis_nav_db.search_routes(query_str, limit=limit_val)
                payload = {
                    "query": query_str,
                    "count": len(routes),
                    "results": routes
                }
            except Exception as e:
                payload = {
                    "query": query_str,
                    "count": 0,
                    "error": str(e),
                    "results": []
                }

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1b. API: VŠE Policies & Regulations Query
        if self.path.startswith("/api/vse/policies"):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])

            try:
                import insis_nav_db
                policies = insis_nav_db.search_policies(query_str, limit=limit_val)
                payload = {
                    "query": query_str,
                    "count": len(policies),
                    "results": policies
                }
            except Exception as e:
                payload = {
                    "query": query_str,
                    "count": 0,
                    "error": str(e),
                    "results": []
                }

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1c. API: VŠE Campus Locations (Washrooms, Classrooms, Coordinators)
        if self.path.startswith("/api/vse/locations"):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])

            try:
                import insis_nav_db
                locations = insis_nav_db.search_campus_locations(query_str, limit=limit_val)
                payload = {
                    "query": query_str,
                    "count": len(locations),
                    "results": locations
                }
            except Exception as e:
                payload = {
                    "query": query_str,
                    "count": 0,
                    "error": str(e),
                    "results": []
                }

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1d. API: Unified Search (Locations + Policies + InSIS)
        if self.path.startswith("/api/vse/unified"):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])

            try:
                import insis_nav_db
                res = insis_nav_db.unified_search(query_str, limit=limit_val)
                payload = {
                    "query": query_str,
                    "results": res
                }
            except Exception as e:
                payload = {
                    "query": query_str,
                    "error": str(e),
                    "results": {}
                }

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1e. API: Tailored Pre-Arrival & Onboarding Checklist (Works with or without login)
        if self.path.startswith("/api/vse/checklist"):
            import urllib.parse
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            origin_val = params.get("origin", ["non_eu"])[0]
            housing_val = params.get("housing", ["dorm"])[0]
            stage_val = params.get("stage", ["pre_arrival"])[0]

            try:
                import student_profile
                items = student_profile.get_onboarding_checklist(
                    origin=origin_val,
                    housing=housing_val,
                    stage=stage_val,
                )
                payload = {
                    "origin": origin_val,
                    "housing": housing_val,
                    "stage": stage_val,
                    "count": len(items),
                    "items": items,
                }
            except Exception as e:
                payload = {
                    "error": str(e),
                    "count": 0,
                    "items": [],
                }

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1f. API: insis-links JSON
        if self.path.startswith("/api/insis-links"):
            all_urls_path = Path(__file__).resolve().parent / "all_urls.json"
            if all_urls_path.exists():
                resp_bytes = all_urls_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_bytes)
                return

        # 2. Check if a physical file exists on disk
        req_clean = self.path.split("?")[0].lstrip("/")
        demo_dir = Path(__file__).resolve().parent
        file_path = demo_dir / req_clean

        if req_clean and file_path.exists() and file_path.is_file():
            # Real static asset (styles.css, app.js, all_urls.json, etc.)
            super().do_GET()
        else:
            # 3. SPA Fallback: Serve index.html for all InSIS URLs!
            index_file = demo_dir / "index.html"
            content = index_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(body)
                question = (data.get("question") or data.get("message") or "").strip()
                history = data.get("history", [])
                user_context = data.get("user_context")

                bot = get_bot()
                if bot:
                    result = bot.answer(question=question, history=history, user_context=user_context)
                    resp_data = {
                        "status": "success" if result.get("mode") != "error" else "error",
                        "answer": result.get("answer", ""),
                        "mode": result.get("mode", "normal"),
                        "sources": result.get("sources", []),
                        "top_score": result.get("top_score", 0.0),
                        "latency_ms": result.get("latency_ms", 0.0),
                    }
                else:
                    resp_data = {
                        "status": "error",
                        "answer": "⚠️ **Backend Unavailable:** Could not initialize BuddyBot. Please check your GEMINI_API_KEY configuration.",
                        "mode": "error",
                    }
            except Exception as e:
                resp_data = {
                    "status": "error",
                    "answer": f"Error processing query: {str(e)}",
                    "mode": "error",
                }

            resp_bytes = json.dumps(resp_data, ensure_ascii=False).encode("utf-8")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_bytes)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run(port=8502):
    print("⏳ Pre-warming BuddyBot knowledge engine...", flush=True)
    get_bot()
    print("✅ BuddyBot engine ready!", flush=True)
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, InSISDemoHandler)
    print(f"============================================================", flush=True)
    print(f"🚀 InSIS Demo Website running at: http://localhost:{port}", flush=True)
    print(f"🎓 Embedded VŠE Buddy Bot API ready at: http://localhost:{port}/api/chat", flush=True)
    print(f"============================================================", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping InSIS Demo Server...", flush=True)
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8502))
    run(port)
