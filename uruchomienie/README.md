# Instrukcja uruchomienia KittyCatch

## Środowisko

Windows, Python 3.14 i Godot 4.7.2 (testowano wersję .NET). Lista bibliotek i sprawdzone wersje są w wymagania.txt.
Archiwum rozpakuj w całości. Poniższe polecenia PowerShell zaczynają się w głównym katalogu projektu.

## Przykład bez trenowania

```powershell
python -m pip install -r uruchomienie/wymagania.txt
Set-Location kod/python_ai
python -m src.serwer --strategy ../../modele/best_strategy.json --host 127.0.0.1 --port 8080
```

Pozostaw terminal działający. W Godocie otwórz kod/godot_game/project.godot i uruchom F5. Wybierz poziom i wyślij falę gołębi.
AI samo stawia wieże. Port 8080 musi być wolny przed uruchomieniem serwera; Ctrl+C kończy poprzedni serwer.
Można również uruchomić skrypt uruchomienie/uruchom_ai.ps1. Nie trzeba ponownie trenować modelu.

## Ocena lokalna i testy

Z katalogu kod/python_ai:

```powershell
python train.py --strategy ../../modele/best_strategy.json --duration 120 --output ../../wyniki/ocena_lokalna --gif --pdf
python -m unittest discover -s tests -v
```

## Odtworzenie analizy i wykresów całej populacji

```powershell
python analyze_genetics.py --input ../../wyniki/eksperyment/report.json --workers 4
python -m src.genetic_report --input ../../wyniki/eksperyment/report.json
python population_quality.py --input ../../wyniki/eksperyment/report.json
python -m src.experiment_report --input ../../wyniki/eksperyment/report.json --gif --replay-seed 103
python -m src.pdf_report --input ../../wyniki/eksperyment/report.md
```

Analiza odczytuje zapisane populacje i checkpointy. Nowy pełny trening uruchamia się osobno:

```powershell
python train.py --population 32 --generations 30 --slots 10 --duration 120 --search-seeds 42 137 2026 --test-seeds 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 --workers 4 --record-populations --gif --pdf --output ../../wyniki/nowy_trening
```

## Rzeczywisty mecz bez okna

Zastąp ścieżkę do Godota swoją lokalizacją. Test używa prywatnego portu i nie steruje grą otwartą przez użytkownika.

```powershell
python validate_godot.py --godot C:/Godot/Godot.exe --input ../../wyniki/eksperyment/report.json --seeds 300 301 302 303 304 --speed 4
```

Kod korzysta z konfiguracji w kod/godot_game/config. Jej identyczna kopia jest w dane/config, a konfiguracja treningu w modele/balance_snapshot.json.
Po zmianie zasad wyniki wymagają nowej oceny. Gra implementuje ruch po trasie, kolizje, strefy wież i samosterujące pociski o skończonej prędkości.
Model jest przybliżeniem silnika; najtrudniejsze są fale TANK-ów i zgromadzona energia przeciwnika.

## Utworzenie archiwum do Teams

Wróć do głównego katalogu. Podaj prawdziwy numer zespołu, zgodny z listą w Teams:

```powershell
python uruchomienie/spakuj.py --team NUMER_ZESPOLU
```

Powstanie projekt_NUMER_pon_8.zip z jednym głównym folderem o tej samej nazwie. Plik przesyła jedna osoba reprezentująca zespół.
