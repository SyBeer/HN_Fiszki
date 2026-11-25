"""Sprawdza, czy wersja jest ta sama w stopce, check.js?v=, wyniki.html, README i CHANGELOG.

python3 tools/check_version.py            # zgodność plików
python3 tools/check_version.py v1.12.0    # dodatkowo: tag = wersja w kodzie
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATTERNS = [
    ("CHANGELOG.md", r"^## (\d+\.\d+\.\d+)"),
    ("README.md", r"Wersja: \*\*(\d+\.\d+\.\d+)\*\*"),
    ("html/index.html (stopka)", r"<span>v(\d+\.\d+\.\d+)</span>"),
    ("html/index.html (check.js?v=)", r"check\.js\?v=(\d+\.\d+\.\d+)"),
    ("html/wyniki.html", r"· v(\d+\.\d+\.\d+)</footer>"),
]


def check(root=ROOT, expected=None):
    """Zwraca (wersja z CHANGELOG, lista błędów)."""
    found = {}
    errors = []
    for label, pattern in PATTERNS:
        path = Path(root) / label.split(" ")[0]
        m = re.search(pattern, path.read_text(encoding="utf-8"), re.M)
        if not m:
            errors.append(f"{label}: nie znaleziono numeru wersji")
        else:
            found[label] = m.group(1)
    version = found.get("CHANGELOG.md")
    for label, v in found.items():
        if v != version:
            errors.append(f"{label}: {v}, a CHANGELOG.md: {version}")
    if expected and expected != f"v{version}":
        errors.append(f"tag {expected} nie zgadza się z wersją w kodzie {version}")
    return version, errors


if __name__ == "__main__":
    version, errors = check(expected=sys.argv[1] if len(sys.argv) > 1 else None)
    for e in errors:
        print("BŁĄD:", e)
    if errors:
        sys.exit(1)
    print(f"Wersja {version} zgodna we wszystkich plikach.")
