#!/usr/bin/env python3
"""Zapis wyników fiszek (SPEC.md, Metering).

POST /api/answer   {student, lesson, card, word, deck, view, front, answer, result, session} -> {"ok": true}
GET  /api/results  (nagłówki X-Admin-Email + X-Admin-Token, opcjonalnie ?student=) -> {"rows": [...]}
POST /api/remind   {email} -> {"ok": true, "message": ...}; token idzie mailem tylko na ADMIN_EMAIL
"""
import hmac
import json
import logging
import os
import re
import smtplib
import sqlite3
import ssl
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parseaddr
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
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]+$")
REMIND_COOLDOWN = 600
REMIND_MESSAGE = "Jeśli ten e-mail jest przypisany do wyników, przypomnienie przyjdzie za chwilę."

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


def same_email(a, b):
    return bool(a) and bool(b) and a.strip().lower() == b.strip().lower()


class SmtpMailer:
    """SMTP z logowaniem (user + hasło) albo przekaźnik bez logowania (np. smtp-relay.gmail.com, autoryzacja po IP)."""

    def __init__(self, host, port, user, password, sender, security="starttls", helo=None):
        self.host, self.port, self.user, self.password = host, int(port), user, password
        self.sender, self.security, self.helo = sender, security, helo

    def send(self, to, subject, text):
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, subject
        msg.set_content(text)
        if self.security == "ssl":
            smtp = smtplib.SMTP_SSL(self.host, self.port, local_hostname=self.helo, timeout=20,
                                    context=ssl.create_default_context())
        else:
            smtp = smtplib.SMTP(self.host, self.port, local_hostname=self.helo, timeout=20)
        with smtp:
            if self.security == "starttls":
                smtp.starttls(context=ssl.create_default_context())
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.send_message(msg)


def mailer_from_env(env):
    host = env.get("SMTP_HOST")
    user = env.get("SMTP_USER") or ""
    sender = env.get("SMTP_FROM") or user
    if not host or not sender:
        return None
    port = int(env.get("SMTP_PORT") or 587)
    security = env.get("SMTP_SECURITY") or ("ssl" if port == 465 else "starttls")
    # przedstawiamy się domeną nadawcy (jak "domain" w msmtp), nie nazwą kontenera
    helo = env.get("SMTP_HELO") or parseaddr(sender)[1].rpartition("@")[2] or None
    return SmtpMailer(host, port, user, env.get("SMTP_PASSWORD") or "", sender, security, helo)


class App:
    def __init__(self, store, admin_token, limiter, admin_email=None, mailer=None, remind_limiter=None,
                 clock=time.monotonic, background=True, public_url=""):
        self.store, self.admin_token, self.limiter = store, admin_token, limiter
        self.admin_email, self.mailer, self.clock = admin_email, mailer, clock
        self.remind_limiter = remind_limiter or RateLimiter(limit=3, window=3600, clock=clock)
        self.background, self.public_url = background, public_url
        self.last_mail = None
        self.mail_lock = threading.Lock()

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

    def results(self, token, query, email=None):
        if not self.admin_token:
            raise ApiError(404, "Nie znaleziono.")
        token_ok = bool(token) and hmac.compare_digest(token.encode(), self.admin_token.encode())
        email_ok = not self.admin_email or same_email(email, self.admin_email)
        if not (token_ok and email_ok):
            raise ApiError(401, "Zły e-mail lub token." if self.admin_email else "Zły klucz.")
        student = (query.get("student") or [""])[0].strip() or None
        return {"rows": self.store.list(student=student)}

    def remind(self, ip, body):
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "Nieprawidłowe zapytanie.")
        email = payload.get("email") if isinstance(payload, dict) else None
        if not isinstance(email, str) or len(email.strip()) > 254 or not EMAIL_RE.match(email.strip()):
            raise ApiError(400, "Wpisz poprawny e-mail.")
        if not self.remind_limiter.allow(ip):
            raise ApiError(429, "Za dużo prób, spróbuj za godzinę.")
        if self.admin_token and same_email(email, self.admin_email):
            if not self.mailer:
                log.warning("Przypomnienie: brak SMTP_HOST - mail nie wysłany.")
            else:
                with self.mail_lock:
                    now = self.clock()
                    due = self.last_mail is None or now - self.last_mail >= REMIND_COOLDOWN
                    if due:
                        self.last_mail = now
                if due:
                    self._send_reminder()
        return {"ok": True, "message": REMIND_MESSAGE}

    def _send_reminder(self):
        link = f"\nRaport: {self.public_url}\n" if self.public_url else ""
        text = (f"Cześć,\n\nprzypominamy token do wyników fiszek:\n\n    {self.admin_token}\n{link}\n"
                "Token się nie zmienił. Jeśli to nie Ty prosiłeś o przypomnienie, zignoruj tę wiadomość.\n")

        def go():
            try:
                self.mailer.send(self.admin_email, "Fiszki - przypomnienie tokenu do wyników", text)
                log.info("Przypomnienie tokenu wysłane.")
            except Exception as e:  # noqa: BLE001 - błąd poczty nie może wywrócić serwera
                log.error("Przypomnienie: wysyłka nie powiodła się: %s", e)

        if self.background:
            threading.Thread(target=go, daemon=True).start()
        else:
            go()


def make_server(app, host, port):
    class Handler(BaseHTTPRequestHandler):
        def ip(self):
            return self.headers.get("X-Real-IP") or self.client_address[0]

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path.rstrip("/") != "/api/results":
                return self.reply(404, {"error": "Nie znaleziono."})
            try:
                self.reply(200, app.results(self.headers.get("X-Admin-Token"), parse_qs(url.query),
                                            email=self.headers.get("X-Admin-Email")))
            except ApiError as e:
                self.reply(e.status, {"error": e.message})

        def do_POST(self):
            path = self.path.rstrip("/")
            handler = {"/api/answer": app.record, "/api/remind": app.remind}.get(path)
            if not handler:
                return self.reply(404, {"error": "Nie znaleziono."})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self.reply(400, {"error": "Nieprawidłowe zapytanie."})
            try:
                self.reply(200, handler(self.ip(), self.rfile.read(length)))
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
    admin_email = os.environ.get("ADMIN_EMAIL") or None
    mailer = mailer_from_env(os.environ)
    if admin_token and not admin_email:
        log.warning("Brak ADMIN_EMAIL - logowanie do wyników samym tokenem, bez przypomnień.")
    elif admin_email and not mailer:
        log.warning("Brak SMTP_HOST lub SMTP_FROM - przypomnienia tokenu nie będą wysyłane.")
    store = Store(os.environ.get("DB_PATH", "/data/results.db"))
    app = App(store, admin_token, RateLimiter(limit=int(os.environ.get("RATE_LIMIT", "120"))),
              admin_email=admin_email, mailer=mailer, public_url=os.environ.get("PUBLIC_URL", ""))
    log.info("results: port 8000")
    make_server(app, "0.0.0.0", 8000).serve_forever()


if __name__ == "__main__":
    main()
