# Fiszki Arriba Joven (hiszpański)

Fiszki obrazek / słowo dla Hani, na podstawie podręcznika *Arriba Joven 1* (s. 28, ćw. 3.2 i 3.3) i karty „La ropa”.
91 kart w 3 taliach: La ropa, Descripción física, Carácter. Rysunki to SVG w kodzie, bez zewnętrznych obrazków.

Wersja: **1.13.0**

## Lekcje
Ekran startowy to panel lekcji. Lekcja 1: „Opis wyglądu, charakteru i ubrania” (talie La ropa, Descripción física, Carácter). Lekcja 2: „Participios irregulares” - 16 nieregularnych imiesłowów w taliach -cho, -ierto, -uelto, -to; tryby: bezokolicznik → participio, participio → bezokolicznik, zdanie z luką (he/ha + participio). Nowa lekcja = wpis w tablicy `LESSONS` w `html/index.html` (karty z prefiksem id, np. `l2r1`).

## Widoki
- **Nauka** - odwracanie kart, „Umiem” / „Jeszcze nie”.
- **Quiz** - wpisujesz odpowiedź, aplikacja sprawdza (akcenty i rodzajnik z podpowiedzią, zasady w SPEC.md). „Nie wiem” odwraca kartę, a odpowiedź trzeba przepisać.
- **Wszystkie** - siatka kart.

Przycisk „Dźwięk włączony / wyłączony” wycisza automatyczne czytanie słów (głośnik przy karcie w Nauce działa zawsze).

„Na przodzie: Mieszane” losuje dla każdej karty obrazek, hiszpański albo polski.

## Wyniki uczniów
Aplikacja pyta „Kto ćwiczy?” i wysyła każdą odpowiedź na serwer (kontener `fiszki-hiszpanski-results`, SQLite w wolumenie).
Raport: https://fiszki.ktd.pl/wyniki.html - wymaga klucza rodzica (`ADMIN_TOKEN` w `.env` na serwerze, poza repo; wartość w menedżerze haseł).

## Testy
```bash
node --test
python3 -m unittest discover -s results
python3 -m unittest discover -s deploy
python3 -m unittest discover -s tools
python3 tools/check_version.py
```

## Uruchomienie lokalne
```bash
python3 tools/devserver.py
```
http://localhost:8090 (z API wyników; klucz rodzica: `dev`).

## Serwer (VPS, https://fiszki.ktd.pl)
Docker Compose w `/opt/fiszki-hiszpanski`; HTTPS daje Caddy z `docker-compose.override.yml` (plik tylko na serwerze). Port 8085 słucha wyłącznie na `127.0.0.1`. Na telefonie: „Dodaj do ekranu początkowego” - działa jak aplikacja.

## Pipeline i wydania
- **CI** (`.github/workflows/ci.yml`) - push do `main` i PR: lint, zgodność wersji, testy, build Dockera i test dymny.
- **Release** (`.github/workflows/release.yml`) - tag `vX.Y.Z`: CI, kontrola tag = wersja, GitHub Release z wpisem z CHANGELOG.
- **Deploy** - VPS sam co 5 min sprawdza najnowszy Release (`deploy/fiszki-deploy.sh`, timer systemd), wdraża go i robi test zdrowia; przy błędzie wraca do poprzedniej wersji. GitHub nie ma żadnych sekretów ani dostępu do serwera.

Wydanie:
```bash
git tag -a v1.12.0 -m "opis" && git push github main --tags && git push origin main --tags
```

Instalacja timera na VPS (raz, jako root):
```bash
cd /opt/fiszki-hiszpanski && git pull
install -m 644 deploy/fiszki-deploy.service deploy/fiszki-deploy.timer /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now fiszki-deploy.timer
```
Podgląd: `systemctl list-timers fiszki-deploy.timer`, logi: `journalctl -u fiszki-deploy.service -n 50`. Ręczne uruchomienie: `systemctl start fiszki-deploy.service`.

Postęp nauki („Umiem”) zapisuje się w przeglądarce danego urządzenia. Przycisk „Wyczyść wyniki” (obok licznika) zeruje wyniki wybranej talii; w talii „Wszystko” - wszystkie.
