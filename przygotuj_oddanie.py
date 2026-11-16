"""Assemble the course directory layout from the current source and experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python_ai"))
from src.pdf_report import export_pdf


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build(experiment):
    source = json.loads((experiment / "report.json").read_text(encoding="utf-8"))
    meta = json.loads((ROOT / "project_metadata.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "godot_game/config/balance.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if digest != source["config_sha256"]:
        raise ValueError("Experiment does not match the current game rules")
    for name in ("sprawozdanie.pdf", "prezentacja.pdf", "report.pdf", "rozwoj_populacji.pdf"):
        if not (experiment / name).is_file():
            raise FileNotFoundError(experiment / name)
    backup = ROOT / "archiwum" / ("przed_uporzadkowaniem_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    backup.mkdir(parents=True)
    old_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Both absolute paths are checked before any directory move on Windows.
    for name in ("kod", "dane", "modele", "wyniki", "uruchomienie", "sprawozdanie.pdf", "prezentacja.pdf", "README.md"):
        original, destination = (ROOT / name).resolve(), (backup / name).resolve()
        if not original.is_relative_to(ROOT) or not destination.is_relative_to(backup):
            raise ValueError("Archive path escaped the repository")
        if original.exists():
            original.rename(destination)
    excluded = shutil.ignore_patterns(".godot", ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        "training_results", "frames", "models", "*.pyc", "*.tmp", "~$*", ".env", ".env.*")
    for name in ("godot_game", "python_ai"):
        shutil.copytree(ROOT / name, ROOT / "kod" / name, ignore=excluded)
    copy(ROOT / "project_metadata.json", ROOT / "kod/project_metadata.json")
    protocol = backup / "kod/PROTOKOL_SOCKET.md"
    write(ROOT / "kod/PROTOKOL_SOCKET.md", protocol.read_text(encoding="utf-8") if protocol.exists() else old_readme)
    for file in (ROOT / "python_ai/models").iterdir():
        if file.is_file():
            copy(file, ROOT / "modele" / file.name)
    for name in ("balance.json", "map_data.json"):
        copy(ROOT / "godot_game/config" / name, ROOT / "dane/config" / name)
    copy(experiment / "godot_validation_4x_0f863932/input_303.json", ROOT / "dane/przykladowa_fala_mieszana.json")
    write(ROOT / "dane/scenariusze.json", json.dumps({"config_sha256": digest,
        "training_seeds": source["settings"]["train_seeds"], "test_seeds": source["settings"]["test_seeds"],
        "profiles_by_seed_modulo_5": ["SCOUT", "TANK", "SPEED", "MIXED", "BURST"],
        "duration_seconds": source["settings"]["duration"], "dt_seconds": source["settings"]["dt"]}, indent=2))
    write(ROOT / "dane/README.md", "# Dane wejściowe\n\n`config/` zawiera aktualny balans i mapę. "
        "Identyczne pliki wykonawcze znajdują się w `kod/godot_game/config/`. "
        "`scenariusze.json` opisuje podział trening–test i profile. `przykladowa_fala_mieszana.json` "
        "zawiera harmonogram wykorzystany w rzeczywistym meczu Godota. "
        "Faktyczne wysłanie jednostki nadal wymaga energii.\n")
    result = ROOT / "wyniki"
    shutil.copytree(experiment, result / "eksperyment", ignore=shutil.ignore_patterns("*preview*", "__pycache__", "~$*"))
    for name in ("report.pdf", "rozwoj_populacji.pdf"):
        copy(experiment / name, result / name)
    for file in experiment.glob("*.png"):
        if "preview" not in file.name:
            copy(file, result / "wykresy" / file.name)
    figures = json.loads((experiment / "genetic_analysis/figure_summary.json").read_text(encoding="utf-8"))
    for item in figures["figures"]:
        copy(experiment / "genetic_analysis" / item["file"], result / "wykresy" / item["file"])
    for file in (experiment / "genetic_analysis").glob("fitness_population_seed_*.png"):
        copy(file, result / "wykresy" / file.name)
    copy(experiment / "genetic_analysis/fitness_distribution.png", result / "wykresy/rozwoj_jakosci_calej_populacji.png")
    for folder in (experiment, experiment / "genetic_analysis"):
        for file in folder.glob("*.csv"):
            copy(file, result / "tabele" / file.name)
        for file in folder.glob("*.gif"):
            copy(file, result / "animacje" / file.name)
    for file in (backup / "wyniki").rglob("Zrzut*.png"):
        copy(file, result / "zrzuty_ekranu" / file.name)
    copy(experiment / "godot_layout.png", result / "zrzuty_ekranu/uklad_z_meczu_godota.png")
    for name in ("prezentacja.pptx", "prezentacja_notatki.md", "presentation_manifest.json"):
        copy(experiment / name, result / "prezentacja" / name)
    for name in ("sprawozdanie.pdf", "prezentacja.pdf"):
        copy(experiment / name, ROOT / name)
    notes = json.loads((experiment / "presentation_manifest.json").read_text(encoding="utf-8"))
    glossary = """# Pomoc do aktualnej prezentacji

## Pojęcia prostymi słowami

Chromosom to plan budowy wież, zapisany jako 40 liczb. Gen to jedna liczba określająca typ, x, y lub najwcześniejszy czas budowy.
Osobnik to jeden taki plan. Populacja to 32 plany rozpatrywane w danej epoce. Epoka to ocena całej populacji; 30 epok obejmuje 29 zmian pokolenia.

Fitness to ocena obrony: −przecieki + 0,1 × zabite / wysłane. Większa liczba jest lepsza; −8 jest lepsze od −12. Fitness uśredniamy po 5 scenariuszach treningowych.
Selekcja turniejowa wybiera najlepszego spośród 3 wylosowanych kandydatów na rodzica.
Krzyżowanie 50:50 wybiera każdy gen od jednego z dwóch rodziców. Nie uśrednia ich wartości: z genów 0,2 i 0,8 wybierze 0,2 albo 0,8.
Mutacja z prawdopodobieństwem 15% dodaje do genu losowy szum; np. 0,40 + 0,07 = 0,47. Wynik ograniczamy do [0,1]. To nie znaczy, że 15% dzieci jest lepszych.
Elitaryzm kopiuje 4 najlepsze plany bez zmian. Chroni najlepszy wynik, lecz nie wymusza poprawy średniej całej populacji.

Średnia obejmuje wszystkie 32 oceny. Mediana to środek uporządkowanych ocen. Kwartyle Q1–Q3 obejmują środkowe 50% osobników, a nie przedział ufności.
Spadek średniej jest możliwy, bo krzyżowanie i mutacja tworzą również słabszych potomków. Rozwój populacji oglądamy przez kilka miar naraz.
Ziarno losowania pozwala odtworzyć przebieg. Oddzielny test sprawdza model na scenariuszach niewykorzystanych do wyboru zwycięzcy.
Ablacja to wyłączenie jednego operatora przy zachowaniu porównywalnych warunków. Mała liczba powtórzeń nie daje uniwersalnego rankingu metod.

## Najważniejsze aktualne liczby

Trening: 3 przebiegi × 32 osobniki × 30 epok; 5 scenariuszy treningowych i 20 testowych.
Wybrany model: 8,60 średnich obrażeń; poprzedni na nowych zasadach: 12,10. To około 29% mniej obrażeń.
Najlepsza reguła BASIC: 11,80; losowe rozmieszczenia: 46,1225 z 400 prób. Nie są to wyniki procentowe.
Walidacja silnika: 6 meczów, 64 łączne obrażenia i 0 odrzuconych budów. Fala TANK-ów jest najtrudniejsza.
GA_2026 miał w teście 8,50, lecz zwycięzca 137 został wybrany wcześniej według treningu. Nie zmieniamy wyboru po obejrzeniu testu.

"""
    for slide in notes["slides"]:
        glossary += f"## Slajd {slide['slide']}: {slide['title']}\n\n{slide['notes']}\n\n"
    guide = result / "prezentacja/prezentacja_pomoc.md"
    write(guide, glossary)
    export_pdf(guide, guide.with_suffix(".pdf"))
    requirements = "Pillow==12.3.0\nreportlab==5.0.1\npython-pptx==1.0.2\nPyMuPDF==1.28.2\npypdf==6.19.0\n"
    write(ROOT / "uruchomienie/wymagania.txt", requirements)
    write(ROOT / "kod/python_ai/requirements-analysis.txt", requirements)
    instruction = """# Instrukcja uruchomienia KittyCatch

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
"""
    write(ROOT / "uruchomienie/README.md", instruction)
    export_pdf(ROOT / "uruchomienie/README.md", ROOT / "uruchomienie/instrukcja_uruchomienia.pdf")
    write(ROOT / "uruchomienie/uruchom_ai.ps1", "$ErrorActionPreference = 'Stop'\n$projectRoot = Split-Path -Parent $PSScriptRoot\nPush-Location (Join-Path $projectRoot 'kod/python_ai')\ntry { python -m src.serwer --strategy ../../modele/best_strategy.json --host 127.0.0.1 --port 8080 } finally { Pop-Location }\n")
    copy(ROOT / "spakuj_oddanie.py", ROOT / "uruchomienie/spakuj.py")
    team = meta.get("team_number") or "DO UZUPEŁNIENIA — numer z listy w Teams"
    readme = f"""# Projekt 4 — Tower defense: optymalizacja rozmieszczenia obrony

KittyCatch, przedmiot „{meta['course']}”. Numer zespołu: **{team}**. Zajęcia: **poniedziałek, 8:00**.

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
Repozytorium: {meta['repository']}. Dostęp dla prowadzącego należy zapewnić zgodnie z instrukcją.
Parametry, ziarna, populacje i wyniki silnika są w `wyniki/eksperyment/`. Protokół socketu: `kod/PROTOKOL_SOCKET.md`.

W repo dodatkowo pozostają robocze `godot_game/` i `python_ai/`; do ZIP-a trafia aktualna kopia w `kod/`.
Poprzedni układ materiałów zachowano w `archiwum/`; archiwum historyczne i robocze kopie nie trafiają do paczki.
"""
    write(ROOT / "README.md", readme)
    write(result / "README.md", "# Wyniki aktualnego eksperymentu\n\n"
        "- `rozwoj_populacji.pdf`: jakość całych populacji dla trzech ziaren.\n"
        "- `report.pdf`: pełny raport analityczny.\n- `wykresy/`: wykresy PNG.\n"
        "- `tabele/`: CSV, w tym 2880 ocen osobników i 90 statystyk populacji.\n"
        "- `zrzuty_ekranu/`: zachowane zrzuty użytkownika i układ z rzeczywistego meczu.\n"
        "- `animacje/`: mecz Godota, lokalna symulacja i ewolucja.\n"
        "- `prezentacja/`: PPTX, notatki i aktualna pomoc PDF.\n"
        "- `eksperyment/`: kompletny zapis eksperymentu z konfiguracją, genami i telemetrią.\n")
    write(ROOT / "kod/README.md", "# Kod projektu\n\n`godot_game/` to gra w Godocie; `python_ai/` zawiera serwer AI, symulator, GA, "
        "eksperymenty, testy i generatory materiałów. Gotowy model jest w `../modele/`, wyniki w `../wyniki/`. "
        "Uruchamiaj według `../uruchomienie/README.md`. W repo są także robocze kopie kodu; "
        "narzędzie przygotuj_oddanie.py aktualizuje ten katalog przed pakowaniem.\n")
    copy(ROOT / "python_ai/README.md", ROOT / "kod/python_ai/DOKUMENTACJA_PYTHON.md")
    write(ROOT / "kod/python_ai/README.md", "# Python AI w paczce zaliczeniowej\n\n"
        "Pełna instrukcja paczki: [uruchomienie](../../uruchomienie/README.md). "
        "Zależności: `../../uruchomienie/wymagania.txt`. Z tego katalogu:\n\n"
        "```powershell\npython -m src.serwer --strategy ../../modele/best_strategy.json\n```\n\n"
        "Gra: `../godot_game/project.godot`. Wyniki: `../../wyniki/eksperyment/`. "
        "Rozwój całej populacji: [PDF](../../wyniki/rozwoj_populacji.pdf). "
        "`src/` zawiera symulator, GA, serwer i generatory raportów; `tests/` zawiera 37 testów. "
        "Szersza dokumentacja roboczego repozytorium jest w DOKUMENTACJA_PYTHON.md; "
        "jej przykłady z models/ i training_results/ odnoszą się do układu roboczego. "
        "W paczce stosuj powyższe ścieżki do modele/ i wyniki/.\n")
    files = [ROOT / name for name in ("sprawozdanie.pdf", "prezentacja.pdf", "modele/best_strategy.json", "dane/config/balance.json")]
    write(ROOT / "uruchomienie/manifest.json", json.dumps({"config_sha256": digest,
        "source_experiment": str(experiment.relative_to(ROOT)),
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}, indent=2))
    print(f"Submission layout prepared. Previous files preserved at {backup.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("python_ai/training_results/rebalance_2026-11-16_0f863932"))
    args = parser.parse_args()
    build((ROOT / args.input).resolve())
