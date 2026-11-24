#!/usr/bin/env python3
"""Zapis wyników fiszek (SPEC.md, Metering).

POST /api/answer   {student, lesson, card, word, deck, view, front, answer, result, session} -> {"ok": true}
GET  /api/results  (nagłówek X-Admin-Token, opcjonalnie ?student=) -> {"rows": [...]}
"""
import hmac
import json
import logging
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_BODY = 4096
MAX_LIST = 2000
FRONT_RE = re.compile(r"^[a-z]{1,8}$")
RESULTS = {
    "quiz": ("dobrze", "akcent", "literowka", "rodzajnik", "zle", "nie_wiem", "regular", "auxiliar"),
    "nauka": ("umiem", "nie_umiem"),
}
SESSION_RE = re.compile(r"^[a-z0-9]{6,32}$")
CARD_RE = re.compile(r"^[a-z][a-z0-9]{1,7}$")
DECK_RE = re.compile(r"^[a-z0-9_]{1,24}$")
LESSON_RE = re.compile(r"^l\d{1,3}$")

log = logging.getLogger("results")


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _text(payload, key, max_len, required=True):
    value = payload.get(key)
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise ApiError(400, f"Brak pola {key}.")
    value = value.strip()
    if (required and not value) or len(value) > max_len:
        raise ApiError(400, f"Nieprawidłowe pole {key}.")
    return value


def validate(payload):
    if not isinstance(payload, dict):
        raise ApiError(400, "Nieprawidłowe zapytanie.")
    e = {
        "student": _text(payload, "student", 40),
        "card": _text(payload, "card", 8),
        "word": _text(payload, "word", 80),
        "deck": _text(payload, "deck", 10),
        "view": _text(payload, "view", 10),
        "front": _text(payload, "front", 8),
        "answer": _text(payload, "answer", 200, required=False),
        "result": _text(payload, "result", 12),
        "session": _text(payload, "session", 32),
        "lesson": _text(payload, "lesson", 4, required=False) or "l1",
    }
    if not LESSON_RE.match(e["lesson"]):
        raise ApiError(400, "Nie ma takiej lekcji.")
    if not CARD_RE.match(e["card"]):
        raise ApiError(400, "Nie ma takiej karty.")
    if not DECK_RE.match(e["deck"]):
        raise ApiError(400, "Nie ma takiej talii.")
    if e["view"] not in RESULTS or e["result"] not in RESULTS[e["view"]]:
        raise ApiError(400, "Nieprawidłowy wynik.")
    if not FRONT_RE.match(e["front"]):
        raise ApiError(400, "Nieprawidłowy przód karty.")
    if not SESSION_RE.match(e["session"]):
        raise ApiError(400, "Nieprawidłowa runda.")
    return e


class RateLimiter:
    def __init__(self, limit=120, window=60, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key):
        now = self.clock()
        with self.lock:
            q = self.hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


class Store:
    COLUMNS = ("id", "ts", "ip", "student", "card", "word", "deck", "view", "front", "answer", "result", "session", "lesson")

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, ip TEXT NOT NULL, "
                "student TEXT NOT NULL, card TEXT NOT NULL, word TEXT NOT NULL, deck TEXT NOT NULL, "
                "view TEXT NOT NULL, front TEXT NOT NULL, answer TEXT NOT NULL, result TEXT NOT NULL, "
                "session TEXT NOT NULL, lesson TEXT NOT NULL DEFAULT 'l1')"
            )
            if "lesson" not in {row[1] for row in db.execute("PRAGMA table_info(answers)")}:
                db.execute("ALTER TABLE answers ADD COLUMN lesson TEXT NOT NULL DEFAULT 'l1'")

    def connect(self):
        return sqlite3.connect(self.path)

    def add(self, ip, e):
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cols = self.COLUMNS[1:]
        with self.lock, self.connect() as db:
            db.execute(
                f"INSERT INTO answers ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                (ts, ip, *(e[c] for c in cols[2:])),
            )

    def list(self, student=None, limit=MAX_LIST):
        sql = f"SELECT {', '.join(self.COLUMNS)} FROM answers"
        args = []
        if student:
            sql += " WHERE student = ?"
            args.append(student)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with self.connect() as db:
            return [dict(zip(self.COLUMNS, row)) for row in db.execute(sql, args)]


class App:
    def __init__(self, store, admin_token, limiter):
        self.store, self.admin_token, self.limiter = store, admin_token, limiter

    def record(self, ip, body):
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "Nieprawidłowe zapytanie.")
        e = validate(payload)
        if not self.limiter.allow(ip):
            raise ApiError(429, "Za dużo odpowiedzi naraz, odczekaj minutę.")
        self.store.add(ip, e)
        return {"ok": True}

    def results(self, token, query):
        if not self.admin_token:
            raise ApiError(404, "Nie znaleziono.")
        if not token or not hmac.compare_digest(token.encode(), self.admin_token.encode()):
            raise ApiError(401, "Zły klucz.")
        student = (query.get("student") or [""])[0].strip() or None
        return {"rows": self.store.list(student=student)}


def make_server(app, host, port):
    class Handler(BaseHTTPRequestHandler):
        def ip(self):
            return self.headers.get("X-Real-IP") or self.client_address[0]

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path.rstrip("/") != "/api/results":
                return self.reply(404, {"error": "Nie znaleziono."})
            try:
                self.reply(200, app.results(self.headers.get("X-Admin-Token"), parse_qs(url.query)))
            except ApiError as e:
                self.reply(e.status, {"error": e.message})

        def do_POST(self):
            if self.path.rstrip("/") != "/api/answer":
                return self.reply(404, {"error": "Nie znaleziono."})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self.reply(400, {"error": "Nieprawidłowe zapytanie."})
            try:
                self.reply(200, app.record(self.ip(), self.rfile.read(length)))
            except ApiError as e:
                self.reply(e.status, {"error": e.message})

        def reply(self, status, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return ThreadingHTTPServer((host, port), Handler)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    admin_token = os.environ.get("ADMIN_TOKEN") or None
    if not admin_token:
        log.warning("Brak ADMIN_TOKEN - strona wyników wyłączona.")
    store = Store(os.environ.get("DB_PATH", "/data/results.db"))
    app = App(store, admin_token, RateLimiter(limit=int(os.environ.get("RATE_LIMIT", "120"))))
    log.info("results: port 8000")
    make_server(app, "0.0.0.0", 8000).serve_forever()


if __name__ == "__main__":
    main()
