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
