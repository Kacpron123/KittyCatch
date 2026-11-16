# Projekt 4 — materiały do zaliczenia

Wymagania źródłowe: `Instrukcja oddania projektu.pdf` oraz dokument DOCX
przedmiotu umieszczony w katalogu głównym repozytorium.

| Wymaganie | Materiał / realizacja |
|---|---|
| Sprawozdanie 5–10 stron | `sprawozdanie.pdf` — 9 stron, aktualne zasady |
| Prezentacja PDF | `prezentacja.pdf` — 15 slajdów głównych + 3 zapasowe, aktualne wyniki |
| Edytowalne slajdy i pomoc | `wyniki/prezentacja/` — PPTX, notatki, aktualna pomoc PDF |
| Cel, założenia, architektura, metoda AI | Sprawozdanie i schemat `genetic_analysis/architecture.png` |
| Rozwój jakości całej populacji | `wyniki/rozwoj_populacji.pdf`, 3 wykresy w `wyniki/wykresy/fitness_population_seed_*.png`; średnia, mediana, najlepszy, najgorszy, Q1–Q3 |
| Pełna analiza algorytmu | `wyniki/report.pdf`; surowe populacje w `wyniki/eksperyment/genetic_analysis/` |
| Plan losowy oraz strategia regułowa | 20 losowych planów × 20 scenariuszy; BASIC, SNIPER, MIXED |
| Zatrzymane jednostki, HP bazy i budżet | `wyniki/tabele/benchmark_metrics.csv` |
| Eksperymenty nad metodą | Trzy główne przebiegi i 12 prób ablacyjnych operatorów |
| Silnik i fizyka | Godot, TCP, kolizje, ruch, zasięg oraz pociski; testy w rzeczywistym silniku |
| Kompletny kod | `kod/godot_game/` i `kod/python_ai/`; bez cache silnika i środowiska w ZIP |
| Przykład bez ponownego uczenia | Gotowy model i migawki danych w `modele/` |
| Konfiguracja i dane | `dane/config/`, `dane/scenariusze.json`, przykładowa fala oraz surowe wyniki |
| Instrukcja i zależności | `uruchomienie/instrukcja_uruchomienia.pdf`, `uruchomienie/wymagania.txt` |
| Odtwarzalność | Parametry i ziarna w `wyniki/eksperyment/report.json`, hash konfiguracji i chromosomu |
| Autorzy i podział pracy | `project_metadata.json`, README i sprawozdanie |

Rozszerzony raport analityczny nie zastępuje sprawozdania z limitem stron.
Do krótkiego sprawozdania wybrano najważniejsze figury, a pełne pomiary
pozostają dostępne jako materiały uzupełniające.

Przed oddaniem podać numer zespołu z listy w Teams. Polecenie
`python uruchomienie/spakuj.py --team NUMER` uzupełnia metadane i stronę tytułową
oraz tworzy `projekt_<nr>_pon_8.zip` z jednym katalogiem głównym o tej samej nazwie.
`python uruchomienie/spakuj.py --check` sprawdza strukturę bez tworzenia ZIP-a.
Wyniki zostały dołączone do `wyniki/`; historyczne kopie w `archiwum/` oraz
robocze `godot_game/` i `python_ai/` nie trafiają do archiwum oddania.
Sprawozdanie i prezentacja trafiają do Teams jako część archiwum przesyłanego
przez jedną osobę z zespołu; repozytorium musi być dostępne dla prowadzącego.
