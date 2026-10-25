# Fiszki Arriba Joven (hiszpański)

Fiszki obrazek / słowo dla Hani, na podstawie podręcznika *Arriba Joven 1* (s. 28, ćw. 3.2 i 3.3) i karty „La ropa”.
91 kart w 3 taliach: La ropa, Descripción física, Carácter. Rysunki to SVG w kodzie, bez zewnętrznych obrazków.

Wersja: **1.3.0**

## Widoki
- **Nauka** - odwracanie kart, „Umiem” / „Jeszcze nie”.
- **Quiz** - wpisujesz odpowiedź, aplikacja sprawdza (akcenty i rodzajnik z podpowiedzią, zasady w SPEC.md).
- **Wszystkie** - siatka kart.

## Testy
```bash
node --test
```

## Uruchomienie lokalne
Otwórz `html/index.html` w przeglądarce.

## Serwer (RPi 192.168.1.4)
Adres: http://192.168.1.4:8085 (tylko sieć domowa / VPN). Na telefonie: „Dodaj do ekranu początkowego” - działa jak aplikacja.

Aktualizacja:
```bash
git archive HEAD | ssh raspi4@192.168.1.4 'mkdir -p ~/fiszki-hiszpanski && tar -x -C ~/fiszki-hiszpanski'
ssh raspi4@192.168.1.4 'cd ~/fiszki-hiszpanski && docker compose up -d --build'
```

Postęp nauki („Umiem”) zapisuje się w przeglądarce danego urządzenia.
