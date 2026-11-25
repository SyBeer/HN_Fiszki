# SPEC - Fiszki Arriba Joven

## Cel
Hania uczy się słówek z hiszpańskiego (Arriba Joven 1): ubrania, wygląd, charakter. Fiszki pomagają rozpoznawać słowa, a quiz uczy ich pisania.

## Widoki
1. **Nauka** - jedna karta naraz, odwracanie, "Umiem" / "Jeszcze nie", powtórka trudnych.
2. **Quiz** (od 1.3.0) - karta pokazuje przód, Hania wpisuje odpowiedź, aplikacja ją sprawdza.
3. **Wszystkie** - siatka kart do przeglądania.

## Quiz - zasady sprawdzania
- Przód = obrazek albo polski: odpowiedź po hiszpańsku. Przód = hiszpański: odpowiedź po polsku.
- "Na przodzie: Mieszane" (od 1.5.0): każda karta losuje przód (obrazek / hiszpański / polski) na początku rundy; język odpowiedzi wynika z przodu tej karty. Działa też w Nauce i Wszystkich.
- Wielkość liter, spacje na brzegach i znaki ¡!¿?.,; nie mają znaczenia.
- Hiszpański: przyjmujemy formę męską, żeńską i każdy wariant rozdzielony "/" (np. "blanco" lub "gris", "inteligente" lub "listo"/"lista").
- Rodzajnik (el/la/los/las/un/una/unos/unas) jest opcjonalny. Zły rodzajnik = odpowiedź zaliczona z uwagą, jaki jest poprawny.
- Brak akcentu lub tyldy (debil zamiast débil, castano zamiast castaño) = zaliczone z uwagą o akcencie.
- Jedna literówka w odpowiedzi od 6 liter (krótsze słowa jak gorra/gorro muszą być dokładne) = zaliczone z uwagą "Prawie" i poprawną pisownią.
- Polski: wystarczy jeden z wariantów rozdzielonych "/" lub ",", tekst w nawiasie jest opcjonalny, brak polskich znaków = zaliczone z uwagą.
- Puste pole nie jest oceniane.
- Po sprawdzeniu karta się odwraca, widać pełną odpowiedź; Enter przechodzi dalej.
- Zła odpowiedź trafia do powtórki i zdejmuje kartę z "Umiem"; dobra dodaje do "Umiem".
- Przyciski z literami á é í ó ú ü ñ ¡ ¿ wstawiają znak w miejscu kursora.
- "Nie wiem" (od 1.6.0): karta się odwraca, a uczeń przepisuje odpowiedź z karty do pola. Przepisanie sprawdzane jest tymi samymi zasadami; przy błędzie można poprawiać do skutku. Karta liczy się jako zła (trafia do powtórki, zdjęta z "Umiem"). Dopiero po przepisaniu pojawia się "Dalej".
- Na końcu rundy: wynik i "Powtórz trudne".

## Kryteria akceptacji
- `node --test` przechodzi (test/check.test.js pokrywa zasady sprawdzania).
- Quiz działa na ekranie telefonu (375 px) bez przewijania w bok.
- Wersja w stopce, README i CHANGELOG jest ta sama.

## Metering - zapis wyników na serwerze (od 1.8.0)
Cel: rodzic może sprawdzić, kto, kiedy i jak ćwiczył (wcześniej wyniki były tylko w przeglądarce ucznia).

- Przed Nauką i Quizem aplikacja pyta "Kto ćwiczy?" (imię 1-40 znaków), zapamiętuje je na urządzeniu; na pasku "Uczeń: Hania - zmień".
- Każda odpowiedź idzie na serwer: imię, karta (id + słowo), talia, widok (nauka/quiz), przód karty, wpisany tekst (quiz), wynik, id rundy, czas.
  - Wyniki: quiz `dobrze`, `akcent`, `literowka`, `rodzajnik`, `zle`, `nie_wiem`; nauka `umiem`, `nie_umiem`.
- Brak sieci nie blokuje nauki: niewysłane odpowiedzi czekają w przeglądarce (do 500) i idą przy następnej udanej wysyłce.
- Serwer: `POST /api/answer` (walidacja pól, limit 120/min na IP), `GET /api/results` tylko z kluczem `X-Admin-Token` (ADMIN_TOKEN w .env na RPi), max 2000 ostatnich wpisów, filtr `student`.
- Baza SQLite w wolumenie Dockera - przeżywa przebudowę.
- Strona `/wyniki.html` (klucz wpisany raz, pamiętany w przeglądarce): wybór ucznia, rundy od najnowszej (data i godzina, talia, widok, liczba odpowiedzi, % dobrych, lista błędów), najtrudniejsze słowa.
- Ocena jest liczona w przeglądarce ucznia (to aplikacja domowa, nie egzamin).

### Kryteria akceptacji
- `python3 -m unittest discover -s results` przechodzi (walidacja, zapis, klucz, limit, HTTP).
- Po rundzie quizu wpisy są widoczne na `/wyniki.html` z poprawnymi godzinami (czas lokalny).

## Lekcje (od 1.9.0)
Cel: materiał będzie przybywał lekcja po lekcji; uczeń najpierw wybiera lekcję, potem ćwiczy jej talie.

- Ekran startowy "Lekcje": kafelek na lekcję - numer, tytuł, źródło (np. "Arriba Joven 1, s. 28 + karta La ropa"), miniatury, liczba kart, postęp "Umiesz X z Y" ucznia na tym urządzeniu.
- Lekcja 1: "Opis wyglądu, charakteru i ubrania" = talie La ropa, Descripción física, Carácter (+ Wszystko z tej lekcji).
- Po wybraniu lekcji widać dotychczasową aplikację (talie, widoki, quiz); przycisk "← Lekcje" wraca do panelu. Wybrana lekcja jest pamiętana na urządzeniu.
- Pod kafelkami informacja, że kolejne lekcje pojawią się tutaj (bez wymyślonych lekcji).
- Nowa lekcja = wpis w tablicy LESSONS w kodzie (karty z własnym prefiksem id, np. `l2r1`).
- Metering: każda odpowiedź ma pole `lesson` (np. `l1`); serwer przyjmuje karty i talie z dowolnej lekcji (id karty `[a-z][a-z0-9]{1,7}`, talia `[a-z0-9_]{1,24}`). Starsze wpisy bez lekcji traktowane jako `l1`. Raport pokazuje lekcję przy każdej rundzie.

### Kryteria akceptacji
- Testy serwera pokrywają pole `lesson`, migrację starej bazy i nowe formaty id.
- Panel działa na telefonie (375 px) bez przewijania w bok.

## Lekcja 2: Participios irregulares (od 1.10.0)
Źródło: lista nieregularnych imiesłowów od usera (2026-11-24), 16 czasowników (descubrir był na liście dwa razy - jedna karta).

- Talie wg końcówki: **-cho** (decir, hacer, satisfacer), **-ierto** (abrir, cubrir, descubrir), **-uelto** (volver, devolver, envolver, resolver), **-to** (escribir, describir, poner, romper, ver, morir) + Wszystko.
- Karta: obrazek czynności, bezokolicznik, znaczenie po polsku, participio, zdanie w pretérito perfecto z luką i jego tłumaczenie.
- Tryby (zamiast "Na przodzie" w tej lekcji): **Bezokolicznik → participio**, **Participio → bezokolicznik**, **Zdanie z luką** (np. "Hoy (yo) ___ (abrir) la ventana." → "he abierto"), **Mieszane**.
- Sprawdzanie (ostrzejsze niż słówka, bo ćwiczymy pisownię):
  - wielkość liter, spacje i ¡!¿? bez znaczenia; brak akcentu = zaliczone z uwagą;
  - **bez tolerancji literówek**, forma żeńska/mnoga participio nie jest przyjmowana;
  - forma regularna (abrido, hacido, ponido, vido, escribido...) = źle z podpowiedzią "To forma regularna, a abrir jest nieregularny";
  - w zdaniu z luką dobre participio ze złym lub brakującym "haber" (abierto, ha abierto zamiast he abierto) = źle z podpowiedzią o haber.
- Nauka, Wszystkie, "Nie wiem" z przepisaniem, dźwięk i wyniki działają jak w lekcji 1.
- Metering: tryby `inf`, `part`, `gap` w polu przodu; nowe wyniki quizu `regular` i `auxiliar`.

### Kryteria akceptacji
- `node --test` pokrywa sprawdzanie czasowników (participio, bezokolicznik, luka, forma regularna, haber).
- Testy serwera przyjmują nowe tryby i wyniki.
- Lekcja 2 działa na telefonie (375 px) bez przewijania w bok.

## Wylogowanie ucznia (od 1.11.0)
Na wspólnym urządzeniu uczeń kończy ćwiczenie przyciskiem „Wyloguj” (ekran „Kto ćwiczy?”, otwierany przyciskiem „Uczeń: …”).

### Kryteria akceptacji
- „Wyloguj” widać tylko, gdy ktoś jest zalogowany.
- Po wylogowaniu pole imienia jest puste, a lokalne postępy (kropki „umiesz”) są wyczyszczone; bez imienia nie da się ćwiczyć.
- Odpowiedzi wysłane i czekające w kolejce zostają przypisane do poprzedniego ucznia; wyniki na serwerze się nie zmieniają.

## Pipeline GitHub i auto-deploy na VPS (od 1.12.0)
Cel: każda zmiana jest sprawdzana automatycznie, a wydanie (tag) samo trafia na VPS Cyberfolks (fiszki.ktd.pl) - bez ręcznego `git pull` i bez dawania GitHubowi dostępu do serwera.

- **CI** (`.github/workflows/ci.yml`) na push do `main` i na PR: `node --test`, testy serwera i deployu (Python), lint (`node --check`, `py_compile`, zgodność wersji w stopce, `check.js?v=`, wyniki.html, README i CHANGELOG), build obu obrazów Dockera (bez publikacji).
- **Release** (`.github/workflows/release.yml`) na tag `vX.Y.Z`: najpierw całe CI, potem sprawdzenie, że tag = wersja w kodzie, i GitHub Release z wpisem z CHANGELOG. Bez zielonego CI nie ma Release.
- **Deploy pull** (`deploy/fiszki-deploy.sh` + timer systemd co 5 min na VPS): skrypt pyta publiczne API GitHuba o najnowszy Release. Jeśli to inny tag niż wdrożony - `git checkout` tagu, `docker compose up -d --build`, test zdrowia `http://127.0.0.1:8085/`. Gdy test nie przejdzie - powrót do poprzedniej wersji.
- Skrypt nie rusza plików lokalnych serwera (`.env`, `Caddyfile`, `docker-compose.override.yml`); przerywa, gdy pliki z repo są zmienione ręcznie. Przyjmuje tylko tagi `vX.Y.Z`. Dwa przebiegi naraz są zablokowane (`flock`).
- Port 8085 nasłuchuje tylko na `127.0.0.1` - z internetu wyłącznie HTTPS przez Caddy.

### Bezpieczeństwo
- Zero sekretów w GitHubie: workflowy używają tylko wbudowanego `GITHUB_TOKEN` (CI tylko odczyt, Release `contents: write`). GitHub nie ma klucza SSH ani dostępu do VPS; `ADMIN_TOKEN` zostaje w `.env` na serwerze.
- Akcje przypięte do SHA commita; Dependabot pilnuje ich aktualizacji i obrazów bazowych.
- Brak `pull_request_target` - kod z forków nie dostaje uprawnień zapisu.

### Poza zakresem
- Publikacja obrazów do GHCR (VPS buduje obrazy sam).
- SBOM (aplikacja nie jest dystrybuowana jako artefakt).
- Backup wolumenu `results-data`, hardening SSH na VPS (osobne zadania z notatki VPS).

### Kryteria akceptacji
- `python3 -m unittest discover -s deploy` przechodzi: wdrożenie nowego Release, brak zmian przy tej samej wersji, brak Release (404), odrzucenie złej nazwy tagu, przerwanie przy ręcznych zmianach, rollback po nieudanym teście zdrowia.
- Lint wersji wykrywa niezgodną wersję.
- Push tagu z zielonym CI daje Release; VPS wdraża go w ciągu 5 minut (weryfikacja po pierwszym wydaniu).

## Domyślne ustawienia lekcji (od 1.13.0)
Lekcja może mieć `defaults` (talia, przód/ćwiczenie, widok), stosowane przy każdym wejściu do tej lekcji z panelu lekcji.

### Kryteria akceptacji
- Lekcja 2 otwiera się na talii „Wszystko” (16 czasowników), ćwiczeniu „Mieszane” i widoku Quiz.
- W trakcie lekcji uczeń może zmienić talię, ćwiczenie i widok; wybór zostaje po odświeżeniu strony.
- Lekcja 1 nie ma `defaults`: przejmuje talię, ćwiczenie i widok z poprzednio otwartej lekcji, jeśli ma takie same (jak dotąd).

## Logowanie do wyników: e-mail + token, przypomnienie (od 1.14.0)
Cel: rodzic loguje się do `/wyniki.html` e-mailem i tokenem; gdy zapomni tokenu, dostaje go mailem. Przypomnienie, nie reset - token się nie zmienia.

Zakres: jeden rodzic (jeden `ADMIN_EMAIL` + `ADMIN_TOKEN` w `.env`), widzi wszystkich uczniów. Poza zakresem: wielu rodziców, zmiana tokenu z poziomu strony.

- `.env`: `ADMIN_EMAIL`, `ADMIN_TOKEN`, `SMTP_HOST`, `SMTP_PORT` (domyślnie 587), `SMTP_FROM` (wymagany, albo `SMTP_USER`), `SMTP_USER` + `SMTP_PASSWORD` (tylko SMTP z logowaniem), `SMTP_SECURITY` (`starttls` domyślnie, `ssl` dla 465, `none`), `SMTP_HELO` (domyślnie domena z `SMTP_FROM`), `PUBLIC_URL` (link w mailu, opcjonalny).
- Produkcja (VPS fiszki.ktd.pl): przekaźnik Google Workspace `smtp-relay.gmail.com:587`, STARTTLS, bez logowania (autoryzacja po IP VPS), nadawca z domeny `ktd.pl`, EHLO `ktd.pl`.
- `GET /api/results`: nagłówki `X-Admin-Email` + `X-Admin-Token`. Gdy `ADMIN_EMAIL` ustawiony, muszą pasować oba (e-mail bez względu na wielkość liter i spacje). Bez `ADMIN_EMAIL` działa sam token (zgodność wstecz do czasu uzupełnienia `.env`).
- `POST /api/remind {"email"}`: zawsze ta sama odpowiedź („Jeśli ten e-mail jest przypisany do wyników, przypomnienie przyjdzie za chwilę.”), żeby nie zdradzać, czy e-mail pasuje. Mail z tokenem idzie tylko na `ADMIN_EMAIL`, gdy podany e-mail pasuje i SMTP jest ustawiony. Wysyłka w tle (czas odpowiedzi nie zdradza wyniku).
- Limity przypomnień: 3 na godzinę z jednego IP (potem 429) i najwyżej 1 mail na 10 minut w ogóle.
- IP klienta za proxy (Caddy): nginx ufa `X-Forwarded-For` tylko od adresów prywatnych/lokalnych (od 1.14.1); limity działają na IP ucznia, nie proxy.
- `/wyniki.html`: pola e-mail i token (przeglądarka zapamiętuje oba), przycisk „Nie pamiętam tokenu” wysyła przypomnienie na wpisany e-mail.

### Kryteria akceptacji
- Zły e-mail albo zły token -> 401 „Zły e-mail lub token.”; oba dobre -> wyniki.
- Przypomnienie dla pasującego e-maila wysyła 1 mail z tokenem na `ADMIN_EMAIL`; dla innego e-maila nie wysyła nic, a odpowiedź jest identyczna.
- Drugi pasujący wniosek w ciągu 10 minut nie wysyła drugiego maila; czwarty wniosek z jednego IP w godzinę -> 429.
- Wysyłka SMTP sprawdzona testem na lokalnym serwerze SMTP (bez mockowania), także bez logowania z EHLO = domena nadawcy.
