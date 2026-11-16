# Python AI: obrona bazy i socket Godota

Układ do oddania jest opisany w głównym [README](../README.md). W repo są to robocze źródła;
aktualny komplet do przekazania obejmuje `kod/`, `dane/`, `modele/`, `wyniki/` i `uruchomienie/`.
W kopii `kod/python_ai` uruchamiaj serwer z modelem `../../modele/best_strategy.json`;
instrukcja PDF znajduje się w `../../uruchomienie/`.
Rozwój jakości **całej populacji dla wszystkich trzech przebiegów** opisano w
[`wyniki/rozwoj_populacji.pdf`](../wyniki/rozwoj_populacji.pdf): średnia, mediana, najlepszy,
najgorszy i kwartyle 25–75%, wraz z CSV wszystkich 90 populacji.

## Ponowny trening po zmianie zasad — 16.11.2026

Nowy eksperyment: [`training_results/rebalance_2026-11-16_0f863932/`](training_results/rebalance_2026-11-16_0f863932/).
Zawiera nowy [raport PDF](training_results/rebalance_2026-11-16_0f863932/report.pdf),
trzy układy wież, pełną telemetrię populacji i wyniki walidacji w Godocie.
Trening: 3 ziarna × 32 osobniki × 30 pokoleń, epizody po 120 s,
5 scenariuszy treningowych i 20 osobnych testowych. Zwycięzcę wybiera fitness treningowy.

```powershell
python train.py --population 32 --generations 30 --duration 120 --search-seeds 42 137 2026 --test-seeds 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 --previous-report training_results/report.json --workers 4 --record-populations --gif --pdf --output training_results/nowy_eksperyment
```

`--workers` przyspiesza ocenę niezależnych chromosomów, zachowując deterministyczny wynik.
`--record-populations` zapisuje chromosomy, rodziców, maski krzyżowania i mutacje podczas treningu;
analiza może wykorzystać ten zapis bez powtarzania wyszukiwania.
Prezentacja, pomoc do prezentacji i dokumenty bezpośrednio w `training_results/`
opisują poprzedni eksperyment i poprzednie zasady. Aktualne liczby są w nowym podfolderze.

## Prezentacja na zajęcia

W `training_results/` znajdują się `prezentacja.pdf` i edytowalna
`prezentacja.pptx`: 15 slajdów na około 10–12 minut z pokazem gry oraz
3 slajdy zapasowe. W PowerPoint slajdy zapasowe są domyślnie ukryte.
`prezentacja_notatki.md` zawiera podział między prelegentów i wskazówki;
te same notatki są osadzone w PPTX. `prezentacja_demo.gif` jest zapasowym
pokazem prawdziwych obserwacji Godota i jest również osadzony w PPTX.
`prezentacja_pomoc.pdf` wyjaśnia prostym językiem pojęcia, wzory i liczby
slajd po slajdzie. Zawiera też przykłady krzyżowania i mutacji, gotowe
wypowiedzi oraz odpowiedzi na pytania prowadzącego.

Ponowne zbudowanie obu formatów z tych samych danych:

```powershell
python -m pip install -r requirements-presentation.txt
python build_presentation.py
python build_presentation_guide.py
```

PDF zawiera nieruchomy kadr demonstracji. Do pokazu na żywo uruchom serwer
z `models/best_strategy.json` i projekt w Godocie. Prezentacja jest datowana
na 16 listopada 2026; teksty, liczby, diagramy i notatki w PPTX są edytowalne.

## Sprawozdanie i analiza genetyczna

Metadane autorów i podział pracy zapisano w `../project_metadata.json`.
`training_results/sprawozdanie.pdf` jest krótkim dokumentem zaliczeniowym
(wymagane 5–10 stron), a `training_results/report.pdf` pełnym załącznikiem
analitycznym z figurami, chromosomami i wynikami eksperymentów.

Pełna telemetria, porównanie z 20 losowymi układami i 12 prób ablacyjnych:

```powershell
python analyze_genetics.py
python -m src.genetic_report
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 103
python -m src.pdf_report --input training_results/report.md
python -m src.course_report
```

Analiza odtwarza zapisane przebiegi z `report.json`, sprawdza zgodność
chromosomów końcowych i nie wybiera modelu ponownie według testów.
Późniejsza krzywa testowa poszczególnych epok jest analizą post hoc.
`--phase main`, `--phase random` i `--phase ablations` pozwalają wykonać
wybraną część; ukończone próby mają checkpointy i są ponownie używane.

W `training_results/genetic_analysis/` powstają populacje JSONL, genotypy CSV,
rodowody potomków, maski krzyżowania, mutacje przed/po i figury PNG.
`genetic_evolution.gif` pokazuje zmiany planu i chromosomu w kolejnych epokach.
Wymagania do odtworzenia eksportu: `requirements-analysis.txt` (Python 3.14).

Gotowy przykład bez treningu znajduje się w wersjonowanym `models/`:

```powershell
python -m src.serwer --strategy models/best_strategy.json
python train.py --strategy models/best_strategy.json --duration 120 --output evaluation
```

Model ma horyzont 120 s; migawki konfiguracji i mapy oraz identyfikator
eksperymentu są zapisane obok chromosomu. Zmiana balansu wymaga ponownej oceny.

AI **stawia wieże**. Gracz/przeciwnik wysyła gołębie. Algorytm genetyczny
optymalizuje plan obrony: typ wieży, współrzędne i najwcześniejszy czas budowy.
Do Godota wysyła wyłącznie `build_tower`.

## Uruchomienie od początku

Wszystkie poniższe polecenia wykonuj z katalogu `python_ai/`.
Potrzebny jest Python 3.14 i Pillow. Zależności projektu można przygotować
przez `uv sync`, a polecenia poprzedzać `uv run`.

1. Wytrenuj strategię lokalnie:

   ```powershell
   python train.py --population 32 --generations 30 --slots 10 --duration 90 --gif
   ```

2. Uruchom serwer z zapisanym chromosomem:

   ```powershell
   python -m src.serwer --strategy training_results/best_strategy.json --host 127.0.0.1 --port 8080
   ```

3. Otwórz `godot_game/project.godot` w Godocie i uruchom projekt (F5).
   Godot łączy się do Pythona jako klient TCP. W grze wysyłaj fale gołębi;
   model będzie wybierał wieże i odsyłał komendy ich budowy.

Serwer loguje odebrane stany i wysłane akcje. Ctrl+C kończy jego działanie.
Host i port Godota są ustawione w `godot_game/autoloads/NetworkManager.gd`;
muszą odpowiadać argumentom serwera. Godot ponawia połączenie co 2 s.

## Test socketu i przykład akcji

Bez treningu można odebrać same obserwacje:

```powershell
python -m src.serwer
```

Albo wysłać jedną ręcznie określoną akcję po pierwszym `update`:

```powershell
python -m src.serwer --build-once --tower-type BASIC --x 3 --y 3
```

Wybierz jedno polecenie serwera, następnie uruchom grę. Współrzędne wybierz
z wolnych pól budowy (`map_grid[x][y] == 1`), przy wystarczających środkach AI.
Nie łącz `--strategy` z `--build-once`.

Wiadomości to obiekty JSON UTF-8, każdy zakończony `\n`. Godot wysyła
`init` i automatyczne `update`; protokół nie wymaga zapytania o stan.
Python odsyła na tym samym połączeniu:

```json
{"action":"build_tower","command_id":"example-1","tower_type":"BASIC","x":3,"y":3}
```

Godot sprawdza koszt, typ i pole, a wynik zwraca w zdarzeniu `action_result`
z `accepted`, `reason` i tym samym `command_id`. `None` z polityki oznacza
oczekiwanie i brak wiadomości. Nazwy wież: BASIC, SNIPER. Siatka jest
x-major, indeksowana od zera. Dokładny schemat: [README repozytorium](../README.md).

## Własna polityka

`GameServer` obsługuje fragmenty wiadomości, kilka JSON-ów w jednym odczycie
i ponowne połączenia. Przechowuje `latest_init` i `latest_observation`.
Bez polityki jest pasywny. Gotowy agent jest callbackiem serwera:

```python
from src.genetic_ai import GeneticAgent, Strategy
from src.serwer import GameServer

policy = GeneticAgent(Strategy.load("training_results/best_strategy.json"))
GameServer(policy=policy).serve_forever()
```

Agent otrzymuje `init` ze specyfikacją wież, a potem wybiera akcje z obserwacji.
Kontroluje fundusze, zajętość pól i potwierdzenia. Deduplikuje obserwacje,
resetuje plan po zmianie epizodu i nie wysyła więcej niż jednej komendy na
0,5 s. Po 2 s bez potwierdzenia sprawdza zajętość pola; wolny cel pozwala
ponowić slot, zajęty oznacza jego zakończenie. Godot ostatecznie zatwierdza akcję.

## Chromosom i trening

Każdy slot budowy to cztery geny w [0,1]: typ wieży, x, y, czas.
Domyślnie 10 slotów daje 40 genów. Typ wybierany jest z `tower_types`,
współrzędne skalowane do wymiarów mapy, czas do długości epizodu.
Zajęte lub niedostępne pole zastępowane jest najbliższym wolnym polem budowy.
Model czeka na pieniądze, ale może wykonać tańszy gotowy slot wcześniej.

Fitness = `-leaks + 0.1 * kills / max(spawned, 1)`: ochrona bazy jest celem,
a udział zabitych gołębi rozstrzyga remisy. Selekcja turniejowa, krzyżowanie
jednostajne, mutacja Gaussa i elitaryzm wybierają najlepszy sprawdzony plan.
Nie ma gwarancji globalnego optimum.

Trening: ziarna 10–14. Test: ziarna 100–109, rozłączne z treningiem.
Profile przeciwnika: SCOUT, TANK, SPEED, MIXED i BURST (seed modulo 5).
Harmonogram żądanych fal jest ustalany niezależnie od chromosomu. Koszty,
regeneracja i zwroty energii są aktywne, więc faktyczne starty fal mogą się
różnić w zależności od przebiegu obrony. AI nie optymalizuje tych fal.

Szybka próba i testy:

```powershell
python train.py --population 8 --generations 3 --duration 45 --slots 6
python train.py --help
python -m unittest discover -s tests -v
```

Niezależne przebiegi pozwalają znaleźć i porównać kilka układów. Zwycięzca
jest wybierany według treningu, przed oceną testową:

```powershell
python train.py --search-seeds 42 137 2026 --population 24 --generations 24 --duration 120 --gif --pdf
```

Każdy przebieg zapisuje `strategy_seed_N.json`; raport zawiera numerowane mapy
`layout_seed_N.png` oraz wykres `search_runs.png`. Opcja
`--previous-report ścieżka/report.json` dodaje różnice balansu i ponownie
ocenia poprzedni chromosom według aktualnych reguł. HP bazy jest wspólne dla
Godota i symulatora: `base.health` w `godot_game/config/balance.json`.

## Kalibracja i testy w Godocie

Fizyczny zasięg uwzględnia skalę wieży: `combat.tower_range_scale=0.4`.
Nominalne 2 kafle BASIC dają zatem 51,2 px, a 4,5 kafla SNIPER 115,2 px.
Model uwzględnia też promień gołębia 8 px, boczny rozrzut ±8 px oraz
kolejność wchodzenia celów w strefę wieży. Parametry są w sekcji `combat`.

Scena `res://tools/ExportTrainingState.tscn` eksportuje rzeczywistą geometrię
i pomiar zasięgu z silnika; domyślny plik to `godot_game/.godot/training_init.json`.
Nie wysyła wiadomości do serwera gracza. Argument `--output` przyjmuje pełną
ścieżkę wyjściowego JSON-a.

Rzeczywiste mecze bez okna graficznego, na prywatnym porcie TCP:

```powershell
python validate_godot.py --godot C:/sciezka/do/Godot.exe --seeds 300 301 302 303 304 --speed 1
```

`--speed 4` skraca test przy 240 krokach fizyki/s. Pliki wynikowe mają hash
konfiguracji i strategii; raport dołącza tylko pasujące pomiary. Różnicę
model–silnik pokazuje jawnie. Mecze nie wpływają na wybór chromosomu.

Próba dużych zgromadzonych fal, poza treningiem:

```powershell
python stress_test.py
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 103
python -m src.pdf_report --input training_results/report.md
```

Test przeciążeniowy ładuje energię gracza do wybranego maksimum 100/300/1000,
wysyła gołębie co 0,1 s i skraca odstępy między żądanymi falami o połowę.
To jawnie inny stan początkowy od standardowych 40 energii. Wyniki są
zapisywane w `stress_test.json`, `stress_test.csv`, `stress_test.png`.

## Raport, GIF i PDF

W `training_results/` powstają:

- `best_strategy.json` — chromosom obrony do socketu.
- `report.md`, `report.json`, `detailed_report.json` — opis, konfiguracja i zdarzenia.
- `builds.csv`, `waves.csv`, `spawns.csv` — budowy AI i działania przeciwnika.
- `generations.csv`, `comparison.csv`, `replay.csv` — wyniki i przebieg.
- `evolution.png`, `diversity.png`, `comparison.png` — trening i porównanie.
- `timeline.png`, `combat.png`, `resources.png`, `base_health.png`, `final_state.png`.

Opcja `--gif` dodaje `replay.gif`: jedną lokalną rozgrywkę, odtwarzaną 3×.
PDF wymaga dodatkowo ReportLab:

```powershell
python -m pip install reportlab
python train.py --gif --pdf
```

Ponowne wygenerowanie raportu i PDF bez treningu:

```powershell
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 100
python -m src.pdf_report --input training_results/report.md
```

Ponowna ocena chromosomu (czas musi odpowiadać zapisanemu planowi):

```powershell
python train.py --strategy training_results/best_strategy.json --duration 90 --output evaluation --gif
```

Poprzedni eksperyment z optymalizacją wysyłania gołębi miał odwrócone role.
Jego wyniki zachowano w `training_results/wave_experiment/`. Moduły
`wave_ai.py` i `wave_report.py` zachowują możliwość analizy starego modelu;
nie są polityką socketu ani domyślnym treningiem.

## Lokalny symulator

```powershell
python main.py --steps 600 --output frames
```

`src/simulation.py` korzysta z `godot_game/config/balance.json` i `map_data.json`.
Wewnątrz używa `grid[x][y]`; plik mapy jest konwertowany z układu wierszowego.
`Simulation.from_init(message)` odtwarza konfigurację z wiadomości Godota.
Trasa powinna zawierać uporządkowane `map.route_points`; sama maska nie
rozstrzyga, który koniec jest początkiem.

`launch_wave()` pobiera energię, regeneracja i zwroty za zabicia działają
według balansu. Budowanie zużywa środki AI; zabicia dają nagrody, przecieki
uszkadzają bazę i zwiększają prędkość gołębi. Zasięg i ruch uwzględniają
przelicznik `game_tile_size_px / cell_size_px`; prędkość pocisków jest
przeliczana z pikseli na komórki mapy.

Dotarcie gołębia do celu zwraca graczowi `ceil(koszt energii / 2)`:
Przy aktualnych kosztach: SCOUT 2, TANK 3, SPEED 4 energii, do wybranego limitu energii.
Zdarzenie `base_damaged` zawiera `player_energy_refunded` z naliczonym zwrotem.

`to_dict()` zwraca stan w kształcie protokołu v2: `map`, `resources`, `units`,
`towers`, `metrics`, `events`, `features`, `feature_vector`. `step(return_state=False)`
pozwala trenować bez serializacji na każdym kroku. `src/simulator.py` pozostaje
zgodnym importem klasy. `src/visualization.py` renderuje obiekt symulacji lub
słownik obserwacji, zasięgi wież i mapy zabójstw/przecieków.

Symulator przybliża fizykę i czas scen Godota. GIF i wynik treningu pochodzą
z symulacji lokalnej; działanie strategii w rzeczywistym meczu wymaga testu
w uruchomionym Godocie. Zapisane wyniki dotyczą badanej mapy i profili fal.
