"""Testy zapisu wyników (SPEC.md, Metering).

Uruchomienie: python3 -m unittest discover -s results
"""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import results


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def entry(**kw):
    e = {"student": "Hania", "card": "r1", "word": "gorra", "deck": "ropa", "view": "quiz",
         "front": "img", "answer": "la gorra", "result": "dobrze", "session": "abc123"}
    e.update(kw)
    return e


class TestValidate(unittest.TestCase):
    def test_valid_entry_is_cleaned(self):
        e = results.validate(entry(student="  Hania  "))
        self.assertEqual(e["student"], "Hania")
        self.assertEqual(e["card"], "r1")

    def test_lesson_defaults_to_l1_and_accepts_new_lessons(self):
        self.assertEqual(results.validate(entry())["lesson"], "l1")
        e = results.validate(entry(lesson="l2", card="l2r1", deck="familia"))
        self.assertEqual((e["lesson"], e["card"], e["deck"]), ("l2", "l2r1", "familia"))

    def test_learn_entry_without_answer(self):
        e = results.validate(entry(view="nauka", result="umiem", answer=None))
        self.assertEqual(e["answer"], "")

    def test_rejects_bad_fields(self):
        bad = [
            entry(student=""), entry(student="x" * 41), entry(card="R1!"), entry(card="1r"), entry(card="r12345678"), entry(lesson="L 1"),
            entry(result="super"), entry(view="test"), entry(front="video"), entry(deck="Math!"),
            entry(answer="a" * 201), entry(word="w" * 81), entry(session="ZZ!"), "nie-obiekt",
            entry(view="nauka", result="dobrze"), entry(view="quiz", result="umiem"),
        ]
        for b in bad:
            with self.assertRaises(results.ApiError, msg=str(b)[:60]) as cm:
                results.validate(b)
            self.assertEqual(cm.exception.status, 400)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = results.Store(Path(self.tmp.name) / "r.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_list_newest_first_with_filter(self):
        self.store.add("1.1.1.1", results.validate(entry()))
        self.store.add("1.1.1.1", results.validate(entry(student="Ola", result="zle")))
        rows = self.store.list()
        self.assertEqual([r["student"] for r in rows], ["Ola", "Hania"])
        self.assertTrue(rows[0]["ts"].endswith("+00:00"))
        self.assertEqual([r["student"] for r in self.store.list(student="Hania")], ["Hania"])

    def test_lesson_is_stored(self):
        self.store.add("1.1.1.1", results.validate(entry(lesson="l2", card="l2r1")))
        self.assertEqual(self.store.list()[0]["lesson"], "l2")

    def test_migrates_old_db_without_lesson(self):
        import sqlite3
        old = Path(self.tmp.name) / "old.db"
        with sqlite3.connect(old) as db:
            db.execute("CREATE TABLE answers (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, ip TEXT NOT NULL, "
                       "student TEXT NOT NULL, card TEXT NOT NULL, word TEXT NOT NULL, deck TEXT NOT NULL, "
                       "view TEXT NOT NULL, front TEXT NOT NULL, answer TEXT NOT NULL, result TEXT NOT NULL, "
                       "session TEXT NOT NULL)")
            db.execute("INSERT INTO answers (ts, ip, student, card, word, deck, view, front, answer, result, session) "
                       "VALUES ('2026-10-26T15:00:00+00:00', 'x', 'Hania', 'r1', 'gorra', 'ropa', 'quiz', 'img', '', 'dobrze', 'abc123')")
        store = results.Store(old)
        self.assertEqual(store.list()[0]["lesson"], "l1")
        store.add("1.1.1.1", results.validate(entry(lesson="l2", card="l2r1")))
        self.assertEqual([r["lesson"] for r in store.list()], ["l2", "l1"])

    def test_survives_reopen(self):
        self.store.add("1.1.1.1", results.validate(entry()))
        again = results.Store(Path(self.tmp.name) / "r.db")
        self.assertEqual(len(again.list()), 1)


class TestApp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = FakeClock()
        self.app = results.App(results.Store(Path(self.tmp.name) / "r.db"), "sekret",
                               results.RateLimiter(limit=3, window=60, clock=self.clock))

    def tearDown(self):
        self.tmp.cleanup()

    def test_record_then_read_with_token(self):
        self.app.record("1.1.1.1", json.dumps(entry()).encode())
        data = self.app.results("sekret", {})
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["rows"][0]["word"], "gorra")

    def test_wrong_or_missing_token(self):
        for token in (None, "", "zly"):
            with self.assertRaises(results.ApiError) as cm:
                self.app.results(token, {})
            self.assertEqual(cm.exception.status, 401)

    def test_no_token_configured_hides_results(self):
        app = results.App(self.app.store, None, results.RateLimiter())
        with self.assertRaises(results.ApiError) as cm:
            app.results("cokolwiek", {})
        self.assertEqual(cm.exception.status, 404)

    def test_rate_limit_per_ip(self):
        body = json.dumps(entry()).encode()
        for _ in range(3):
            self.app.record("1.1.1.1", body)
        with self.assertRaises(results.ApiError) as cm:
            self.app.record("1.1.1.1", body)
        self.assertEqual(cm.exception.status, 429)
        self.app.record("2.2.2.2", body)
        self.clock.t = 61
        self.app.record("1.1.1.1", body)

    def test_bad_json(self):
        with self.assertRaises(results.ApiError) as cm:
            self.app.record("1.1.1.1", b"{nie json")
        self.assertEqual(cm.exception.status, 400)


class TestHttp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app = results.App(results.Store(Path(self.tmp.name) / "r.db"), "sekret", results.RateLimiter())
        self.server = results.make_server(app, "127.0.0.1", 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def call(self, path, body=None, headers=None):
        req = urllib.request.Request(self.base + path, data=body, headers=headers or {})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read() or b"{}")

    def test_roundtrip(self):
        status, _ = self.call("/api/answer", json.dumps(entry()).encode(), {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        status, data = self.call("/api/results?student=Hania", headers={"X-Admin-Token": "sekret"})
        self.assertEqual(status, 200)
        self.assertEqual(data["rows"][0]["result"], "dobrze")
        status, data = self.call("/api/results")
        self.assertEqual(status, 401)
        self.assertIn("error", data)

    def test_invalid_post_returns_400_with_message(self):
        status, data = self.call("/api/answer", json.dumps(entry(result="?")).encode())
        self.assertEqual(status, 400)
        self.assertTrue(data["error"])

    def test_unknown_path_404(self):
        self.assertEqual(self.call("/api/nic")[0], 404)


if __name__ == "__main__":
    unittest.main()
