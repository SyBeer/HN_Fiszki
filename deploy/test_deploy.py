"""Testy deploy/fiszki-deploy.sh na prawdziwym git, z udawanym docker compose i testem zdrowia.

Uruchomienie: python3 -m unittest discover -s deploy
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "fiszki-deploy.sh"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class DeployTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.origin = self.tmp / "origin"
        self.app = self.tmp / "app"
        self.release = self.tmp / "release.json"
        self.compose_log = self.tmp / "compose.log"

        self.origin.mkdir()
        git(self.origin, "init", "-q", "-b", "main")
        git(self.origin, "config", "user.email", "t@example.invalid")
        git(self.origin, "config", "user.name", "Test")
        self.commit("v1.0.0", "wersja 1.0.0")
        git(self.origin, "clone", "-q", str(self.origin), str(self.app))
        git(self.app, "checkout", "-q", "--detach", "v1.0.0")

        # udawany "docker compose": zapisuje, ktora wersja byla wdrazana
        fake = self.tmp / "fake-compose"
        fake.write_text('#!/bin/sh\necho "$* @ $(git describe --tags --exact-match 2>/dev/null)" >> "%s"\n' % self.compose_log)
        fake.chmod(0o755)
        self.env = dict(
            os.environ,
            REPO_DIR=str(self.app),
            RELEASE_API=self.release.as_uri(),
            COMPOSE=str(fake),
            # wersja "zepsuta" ma plik BROKEN - test zdrowia wtedy nie przechodzi
            HEALTH_CMD="test ! -f BROKEN",
            HEALTH_TRIES="2",
            HEALTH_SLEEP="0",
            LOCK_FILE=str(self.tmp / "deploy.lock"),
        )

    def commit(self, tag, text, extra_file=None):
        (self.origin / "app.txt").write_text(text)
        git(self.origin, "add", "app.txt")
        if extra_file:
            (self.origin / extra_file).write_text("x")
            git(self.origin, "add", extra_file)
        git(self.origin, "commit", "-q", "-m", text)
        git(self.origin, "tag", "-a", tag, "-m", text)

    def publish(self, tag):
        self.release.write_text('{\n  "url": "x",\n  "tag_name": "%s",\n  "name": "%s"\n}\n' % (tag, tag))

    def run_deploy(self):
        return subprocess.run(["bash", str(SCRIPT)], env=self.env, capture_output=True, text=True)

    def deployed(self):
        return git(self.app, "describe", "--tags", "--exact-match")

    def compose_calls(self):
        return self.compose_log.read_text().splitlines() if self.compose_log.exists() else []

    def test_deploys_new_release(self):
        self.commit("v1.1.0", "wersja 1.1.0")
        self.publish("v1.1.0")
        r = self.run_deploy()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.deployed(), "v1.1.0")
        self.assertEqual(self.compose_calls(), ["up -d --build @ v1.1.0"])

    def test_same_version_does_nothing(self):
        self.publish("v1.0.0")
        r = self.run_deploy()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.compose_calls(), [])
        self.assertIn("aktualna", r.stdout)

    def test_no_release_does_nothing(self):
        # brak pliku = brak Release albo brak sieci
        r = self.run_deploy()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.deployed(), "v1.0.0")
        self.assertEqual(self.compose_calls(), [])

    def test_rejects_bad_tag_name(self):
        self.publish("v1.1.0; rm -rf /")
        r = self.run_deploy()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.deployed(), "v1.0.0")
        self.assertEqual(self.compose_calls(), [])

    def test_aborts_on_local_changes(self):
        self.commit("v1.1.0", "wersja 1.1.0")
        self.publish("v1.1.0")
        (self.app / "app.txt").write_text("zmiana reczna na serwerze")
        r = self.run_deploy()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.deployed(), "v1.0.0")
        self.assertEqual(self.compose_calls(), [])

    def test_keeps_untracked_server_files(self):
        (self.app / ".env").write_text("ADMIN_TOKEN=abc")
        (self.app / "Caddyfile").write_text("fiszki.example {}")
        self.commit("v1.1.0", "wersja 1.1.0")
        self.publish("v1.1.0")
        r = self.run_deploy()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.app / ".env").read_text(), "ADMIN_TOKEN=abc")
        self.assertTrue((self.app / "Caddyfile").exists())

    def test_rolls_back_when_health_fails(self):
        self.commit("v1.1.0", "zepsuta wersja", extra_file="BROKEN")
        self.publish("v1.1.0")
        r = self.run_deploy()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.deployed(), "v1.0.0")
        self.assertEqual(self.compose_calls(), ["up -d --build @ v1.1.0", "up -d --build @ v1.0.0"])

    def test_tag_missing_in_git_fails(self):
        self.publish("v9.9.9")
        r = self.run_deploy()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.deployed(), "v1.0.0")


if __name__ == "__main__":
    unittest.main()
