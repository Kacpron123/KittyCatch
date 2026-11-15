# Projekt 4 — materiały do zaliczenia

Wymagania źródłowe: `Instrukcja oddania projektu.pdf` oraz dokument DOCX
przedmiotu umieszczony w katalogu głównym repozytorium.

| Wymaganie | Materiał / realizacja |
|---|---|
| Sprawozdanie 5–10 stron | `python_ai/training_results/sprawozdanie.pdf` |
| Prezentacja PDF | `python_ai/training_results/prezentacja.pdf` (15 slajdów głównych + 3 zapasowe) |
| Edytowalne slajdy i notatki | `prezentacja.pptx`, `prezentacja_notatki.md`, animacja `prezentacja_demo.gif` |
| Cel, założenia, architektura, metoda AI | Sprawozdanie i schemat `genetic_analysis/architecture.png` |
| Wykresy rozwoju algorytmu | Osobny `report.pdf`, figury i pełne populacje w `genetic_analysis/` |
| Plan losowy oraz strategia regułowa | 20 losowych planów × 20 scenariuszy; BASIC, SNIPER, MIXED |
| Zatrzymane jednostki, HP bazy i budżet | Tabele metryk i `benchmark_metrics.csv` |
| Eksperymenty nad metodą | Trzy główne przebiegi i 12 prób ablacyjnych operatorów |
| Silnik i fizyka | Godot, TCP, kolizje, ruch, zasięg oraz pociski; testy w rzeczywistym silniku |
| Przykład bez ponownego uczenia | Gotowy model i migawki danych w `python_ai/models/` |
| Konfiguracja i dane | `godot_game/config/`, migawki modelu i surowe wyniki eksperymentu |
| Zależności i odtwarzalność | README, `requirements-analysis.txt`, parametry i ziarna w JSON |
| Autorzy i podział pracy | `project_metadata.json`, README i sprawozdanie |

Rozszerzony raport analityczny nie zastępuje sprawozdania z limitem stron.
Do krótkiego sprawozdania wybrano najważniejsze figury, a pełne pomiary
pozostają dostępne jako materiały uzupełniające.

Przed oddaniem uzupełnić numer zespołu w `project_metadata.json`, przejrzeć
prezentację i ułożyć archiwum według instrukcji: `projekt_<nr>_pon_8.zip`
z katalogiem głównym o tej samej nazwie. Wyniki w `training_results/` są
ignorowane przez Git, więc trzeba dołączyć je do przekazywanych materiałów.
Sprawozdanie i prezentacja trafiają do Teams jako część archiwum przesyłanego
przez jedną osobę z zespołu; repozytorium musi być dostępne dla prowadzącego.
