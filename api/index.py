"""Vercel Serverless Function entry point for VŠE Buddy Bot & InSIS API.

Handles:
- /api/chat (POST)
- /api/insis/navigate (GET)
- /api/vse/policies (GET)
- /api/vse/locations (GET)
- /api/vse/unified (GET)
- /api/vse/checklist (GET)
- /api/insis-links (GET)
- /api/health (GET)
"""

import sys
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import urllib.parse

# Ensure parent directory (vse-buddy-bot root) is in Python search path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Lazy loaded BuddyBot instance
_bot = None

def get_bot():
    global _bot
    if _bot is None:
        try:
            from bot import BuddyBot
            _bot = BuddyBot()
        except Exception as e:
            print(f"[Vercel Handler Warning] Could not initialize BuddyBot: {e}", flush=True)
            _bot = None
    return _bot


def resolve_api_path(req_path: str, headers) -> tuple[str, dict]:
    parsed = urllib.parse.urlparse(req_path)
    params = urllib.parse.parse_qs(parsed.query)
    route_arg = params.get("__route", [""])[0]

    if route_arg:
        normalized = "/" + route_arg.lstrip("/")
        if not normalized.startswith("/api"):
            normalized = "/api" + normalized
        return normalized, params

    matched = headers.get("x-matched-path") or headers.get("x-vercel-matched-path")
    if matched and parsed.path.endswith("index.py"):
        return matched, params

    return parsed.path, params


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path, params = resolve_api_path(self.path, self.headers)

        # 0. Health check
        if path in ["/api/health", "/api", "/api/index.py"]:
            resp_bytes = json.dumps({"status": "ok", "service": "VŠE Buddy Bot Vercel API"}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 1. API: InSIS Navigation Database Query
        if path.startswith("/api/insis/navigate"):
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])
            try:
                import insis_nav_db
                routes = insis_nav_db.search_routes(query_str, limit=limit_val)
                payload = {"query": query_str, "count": len(routes), "results": routes}
            except Exception as e:
                payload = {"query": query_str, "count": 0, "error": str(e), "results": []}

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 2. API: VŠE Policies & Regulations Query
        if path.startswith("/api/vse/policies"):
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])
            try:
                import insis_nav_db
                policies = insis_nav_db.search_policies(query_str, limit=limit_val)
                payload = {"query": query_str, "count": len(policies), "results": policies}
            except Exception as e:
                payload = {"query": query_str, "count": 0, "error": str(e), "results": []}

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 3. API: VŠE Campus Locations
        if path.startswith("/api/vse/locations"):
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])
            try:
                import insis_nav_db
                locations = insis_nav_db.search_campus_locations(query_str, limit=limit_val)
                payload = {"query": query_str, "count": len(locations), "results": locations}
            except Exception as e:
                payload = {"query": query_str, "count": 0, "error": str(e), "results": []}

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 4. API: Unified Search
        if path.startswith("/api/vse/unified"):
            query_str = params.get("q", [""])[0]
            limit_val = int(params.get("limit", [3])[0])
            try:
                import insis_nav_db
                res = insis_nav_db.unified_search(query_str, limit=limit_val)
                payload = {"query": query_str, "results": res}
            except Exception as e:
                payload = {"query": query_str, "error": str(e), "results": {}}

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 5. API: Checklist
        if path.startswith("/api/vse/checklist"):
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
                payload = {"error": str(e), "count": 0, "items": []}

            resp_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 6. API: insis-links JSON
        if path.startswith("/api/insis-links"):
            candidate_paths = [
                BASE_DIR / "all_urls.json",
                BASE_DIR / "public" / "all_urls.json",
                BASE_DIR / "insis_demo" / "all_urls.json",
            ]
            for p in candidate_paths:
                if p.exists():
                    resp_bytes = p.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(resp_bytes)))
                    self.end_headers()
                    self.wfile.write(resp_bytes)
                    return
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": f"Endpoint not found: {path}"}).encode("utf-8"))

    def do_POST(self):
        path, params = resolve_api_path(self.path, self.headers)

        if path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

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
                        "answer": "⚠️ **Backend Unavailable:** Could not initialize BuddyBot. Please check the server GEMINI_API_KEY configuration.",
                        "mode": "error",
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
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": f"Endpoint not found: {path}"}).encode("utf-8"))
