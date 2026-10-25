# SPEC - Fiszki Arriba Joven

## Cel
Hania uczy się słówek z hiszpańskiego (Arriba Joven 1): ubrania, wygląd, charakter. Fiszki pomagają rozpoznawać słowa, a quiz uczy ich pisania.

## Widoki
1. **Nauka** - jedna karta naraz, odwracanie, "Umiem" / "Jeszcze nie", powtórka trudnych.
2. **Quiz** (od 1.3.0) - karta pokazuje przód, Hania wpisuje odpowiedź, aplikacja ją sprawdza.
3. **Wszystkie** - siatka kart do przeglądania.

## Quiz - zasady sprawdzania
- Przód = obrazek albo polski: odpowiedź po hiszpańsku. Przód = hiszpański: odpowiedź po polsku.
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
- Na końcu rundy: wynik i "Powtórz trudne".

## Kryteria akceptacji
- `node --test` przechodzi (test/check.test.js pokrywa zasady sprawdzania).
- Quiz działa na ekranie telefonu (375 px) bez przewijania w bok.
- Wersja w stopce, README i CHANGELOG jest ta sama.
