# Changelog

## 1.12.1 - 2026-11-25
- nginx 1.27 → 1.29 (obraz bazowy, PR od Dependabota).

## 1.12.0 - 2026-11-25
- Pipeline GitHub Actions: CI (lint, zgodność wersji, testy, build Dockera, test dymny) i Release na tag `vX.Y.Z`.
- Auto-deploy na VPS w modelu pull: `deploy/fiszki-deploy.sh` + timer systemd co 5 min, test zdrowia i rollback. Zero sekretów w GitHubie.
- Port 8085 tylko na `127.0.0.1` (z internetu wyłącznie HTTPS przez Caddy).
- Dependabot dla akcji GitHub i obrazów Dockera.
- `tools/check_version.py` - kontrola wersji w stopce, README i CHANGELOG.

## 1.11.0 - 2026-11-25
- Przycisk „Wyloguj” na ekranie „Kto ćwiczy?”: czyści imię i kropki „umiesz” na tym urządzeniu, następny uczeń zaczyna od pustego imienia. Wyniki na serwerze zostają.

## 1.10.0 - 2026-11-24
- Lekcja 2: Participios irregulares - 16 czasowników z rysunkami, talie wg końcówek (-cho, -ierto, -uelto, -to).
- Tryby lekcji 2: bezokolicznik → participio, participio → bezokolicznik, zdanie z luką, mieszane.
- Sprawdzanie czasowników bez tolerancji literówek, z podpowiedzią dla formy regularnej (abrido) i złego „haber”.
- Serwer przyjmuje nowe tryby i wyniki (`regular`, `auxiliar`); raport je nazywa.
- check.js ładowany z numerem wersji (telefony nie trzymają starej kopii).

## 1.9.0 - 2026-11-24
- Panel wyboru lekcji na starcie; Lekcja 1 „Opis wyglądu, charakteru i ubrania” z trzema taliami, przycisk „← Lekcje”.
- Wyniki zapisują lekcję (pole `lesson`, migracja starej bazy); raport pokazuje lekcję przy rundzie.
- Serwer przyjmuje karty i talie przyszłych lekcji.
- `tools/devserver.py` - lokalny podgląd z API.

## 1.8.0 - 2026-10-26
- Metering: „Kto ćwiczy?” i zapis każdej odpowiedzi (Quiz i Nauka) na serwerze, z kolejką offline.
- Strona wyników dla rodzica `/wyniki.html` (klucz): rundy, błędy, najtrudniejsze słowa.
- Nowy kontener `results` (Python, SQLite).

## 1.7.0 - 2026-10-26
- Przycisk włączania i wyłączania dźwięku (zapamiętywany na urządzeniu).

## 1.6.0 - 2026-10-26
- Quiz: przycisk „Nie wiem” - karta się odwraca, uczeń przepisuje odpowiedź; karta liczy się jako zła i wraca w powtórce.

## 1.5.0 - 2026-10-26
- „Na przodzie: Mieszane” - każda karta losuje obrazek, hiszpański albo polski (Quiz, Nauka, Wszystkie).
- Pasek opcji układa się w kolumnę na telefonie, bez przewijania w bok.

## 1.4.0 - 2026-10-26
- Przycisk „Wyczyść wyniki” z potwierdzeniem - zeruje „Umiem” dla wybranej talii i zaczyna rundę od nowa.

## 1.3.0 - 2026-10-26
- Tryb Quiz: wpisywanie odpowiedzi (hiszpański albo polski), sprawdzanie z tolerancją akcentów, rodzajnika i jednej literówki.
- Przyciski z literami á é í ó ú ü ñ ¡ ¿.
- Testy sprawdzania odpowiedzi (`node --test`).

## 1.2.0 - 2026-10-26
- Samodzielna aplikacja (nginx w Dockerze) na RPi, port 8085.
- Ikona i manifest - można dodać do ekranu telefonu.

## 1.1 - 2026-10-26
- Kategoria nad każdą fiszką.

## 1.0 - 2026-10-26
- 91 fiszek: La ropa, Descripción física, Carácter; tryb nauki, siatka, wymowa.
