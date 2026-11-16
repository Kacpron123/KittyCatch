# Projekt 4 — Tower defense: optymalizacja rozmieszczenia obrony

KittyCatch, przedmiot „Sztuczna inteligencja w grach i rozszerzonej rzeczywistości”. Numer zespołu: **4**. Zajęcia: **poniedziałek, 8:00**.

- **Aleksander Kopyto** — algorytm genetyczny i AI.
- **Kacper Mazurek** — gra.

AI dobiera typ, miejsce i czas budowy wież przy ograniczonych środkach. Gracz wysyła gołębie.
Optymalizacja używa własnego algorytmu genetycznego, symulatora Python i komunikacji JSON/TCP z Godotem.

## Materiały zgodne z instrukcją oddania

| Plik / katalog | Zawartość |
|---|---|
| [sprawozdanie.pdf](sprawozdanie.pdf) | Krótkie sprawozdanie zaliczeniowe: 9 stron |
| [prezentacja.pdf](prezentacja.pdf) | Aktualna prezentacja: 15 slajdów głównych i 3 zapasowe |
| kod/ | Kompletny aktualny kod Python i projekt Godota z konfiguracją |
| dane/ | Mapa, balans, podział scenariuszy i przykładowa fala |
| modele/ | Wytrenowany chromosom, konfiguracja treningu, mapa i karta modelu |
| wyniki/ | Wykresy, CSV, zrzuty, animacje, raport analityczny i pełna telemetria |
| uruchomienie/ | Instrukcja PDF, wymagania.txt, launcher AI i skrypt pakowania |

## Rozwój jakości całej populacji

[Osobny PDF](wyniki/rozwoj_populacji.pdf) pokazuje wszystkie trzy treningi: najlepszy, średnia, mediana, najgorszy i pasmo Q1–Q3.
[Wykres wybranego treningu](wyniki/wykresy/rozwoj_jakosci_calej_populacji.png) obejmuje 32 osobniki w każdej z 30 epok.
[Statystyki 90 populacji](wyniki/tabele/population_quality.csv), [wszystkie 2880 ocen osobników](wyniki/tabele/populations.csv).
Q1–Q3 obejmuje środkowe 50% populacji; nie jest przedziałem ufności. Wyższy fitness jest lepszy.

## Aktualne wyniki

Trening: 3 × 32 osobniki × 30 epok, 5 scenariuszy treningowych, 20 oddzielnych testowych.
Wybrany model (seed 137): **8,60** średnich obrażeń. Poprzedni model na nowych zasadach: **12,10**;
reguła BASIC: **11,80**; losowe układy: **46,1225**. Zwycięzcę wybrano na treningu, bez strojenia na teście.
Sześć meczów Godota: zero odrzuconych komend budowy. To najlepszy sprawdzony plan, bez gwarancji globalnego optimum.
[Pełny raport analityczny](wyniki/report.pdf) stanowi osobny załącznik i nie zastępuje krótkiego sprawozdania.
[Edytowalne slajdy i aktualna pomoc](wyniki/prezentacja/) oraz [animacje](wyniki/animacje/).

## Uruchomienie bez uczenia

Wymagane: Python 3.14, Godot 4.7.2 (testowano .NET), Pillow 12.3.0, ReportLab 5.0.1.
Do regenerowania slajdów: python-pptx 1.0.2; do kontroli PDF: PyMuPDF 1.28.2 i pypdf 6.19.0.
Dokładne zależności: [uruchomienie/wymagania.txt](uruchomienie/wymagania.txt).
Z głównego katalogu projektu w PowerShell:

```powershell
python -m pip install -r uruchomienie/wymagania.txt
Set-Location kod/python_ai
python -m src.serwer --strategy ../../modele/best_strategy.json
```

Następnie otwórz `kod/godot_game/project.godot` w Godocie i naciśnij F5. Wyślij falę; AI automatycznie buduje wieże.
[Pełna instrukcja uruchomienia](uruchomienie/instrukcja_uruchomienia.pdf) obejmuje też testy, ponowny trening i walidację silnika.
Silnik realizuje ruch po trasie, kolizje, strefy zasięgu, wybór celu oraz samosterujące pociski z czasem lotu.
Limity energii gracza: trudny 100, średni 300, łatwy 1000. Zwrot przy dotarciu do bazy: ceil(koszt/2),
czyli SCOUT 2, TANK 3, SPEED 4 przy aktualnym balansie.

## Oddanie i odtwarzalność

Numer zespołu jest w `project_metadata.json`. Nazwa wymagana przez instrukcję: `projekt_<numer>_pon_8.zip`,
wewnątrz jeden katalog `projekt_<numer>_pon_8/`. Z głównego katalogu:

```powershell
python uruchomienie/spakuj.py --team NUMER_ZESPOLU
```

Skrypt sprawdza PDF-y, zależności, zgodność balansu/modelu oraz integralność ZIP-a.
Repozytorium: https://github.com/Kacpron123/KittyCatch. Dostęp dla prowadzącego należy zapewnić zgodnie z instrukcją.
Parametry, ziarna, populacje i wyniki silnika są w `wyniki/eksperyment/`. Protokół socketu: `kod/PROTOKOL_SOCKET.md`.

W repo dodatkowo pozostają robocze `godot_game/` i `python_ai/`; do ZIP-a trafia aktualna kopia w `kod/`.
Poprzedni układ materiałów zachowano w `archiwum/`; archiwum historyczne i robocze kopie nie trafiają do paczki.
