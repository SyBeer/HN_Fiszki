"""Lokalny podgląd: pliki z html/ + /api/ z results.App (klucz rodzica: dev).

Uruchomienie: python3 tools/devserver.py   ->   http://localhost:8090
"""
import functools
import json
import os
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "results"))
import results  # noqa: E402

app = results.App(results.Store(os.path.join(tempfile.gettempdir(), "fiszki-dev.db")), "dev", results.RateLimiter())


class Handler(SimpleHTTPRequestHandler):
    def reply(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path.startswith("/api/results"):
            try:
                return self.reply(200, app.results(self.headers.get("X-Admin-Token"), parse_qs(url.query)))
            except results.ApiError as e:
                return self.reply(e.status, {"error": e.message})
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/answer"):
            return self.reply(404, {"error": "Nie znaleziono."})
        length = int(self.headers.get("Content-Length") or 0)
        try:
            self.reply(200, app.record("127.0.0.1", self.rfile.read(length)))
        except results.ApiError as e:
            self.reply(e.status, {"error": e.message})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=os.path.join(ROOT, "html"))).serve_forever()
