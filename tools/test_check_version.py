"""Testy tools/check_version.py. Uruchomienie: python3 -m unittest discover -s tools"""
import tempfile
import unittest
from pathlib import Path

from check_version import check

FILES = {
    "html/index.html": '<span>v{v}</span>\n<script src="check.js?v={v}"></script>',
    "html/wyniki.html": "<footer>wyniki · v{v}</footer>",
    "README.md": "Wersja: **{v}**",
    "CHANGELOG.md": "# Changelog\n\n## {v} - 2026-11-25\n- zmiana",
}


def make_repo(versions):
    root = Path(tempfile.mkdtemp())
    for name, tpl in FILES.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(tpl.format(v=versions.get(name, "1.2.0")))
    return root


class CheckVersionTest(unittest.TestCase):
    def test_same_version_everywhere(self):
        self.assertEqual(check(make_repo({})), ("1.2.0", []))

    def test_mismatch_is_reported(self):
        version, errors = check(make_repo({"html/wyniki.html": "1.1.0"}))
        self.assertEqual(version, "1.2.0")
        self.assertEqual(len(errors), 1)
        self.assertIn("wyniki.html", errors[0])

    def test_expected_tag(self):
        _, errors = check(make_repo({}), expected="v1.3.0")
        self.assertTrue(any("v1.3.0" in e for e in errors))
        self.assertEqual(check(make_repo({}), expected="v1.2.0")[1], [])


if __name__ == "__main__":
    unittest.main()
