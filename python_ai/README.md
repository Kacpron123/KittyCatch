# Python AI integration

## Algorytm genetyczny: strategie wysyłania gołębi

Z katalogu `python_ai/` uruchom trening i generowanie raportu:

```bash
python train.py --population 24 --generations 20 --duration 90 --output training_results
```

Pełny raport zawiera opis wszystkich genów, parametry obu faz, ustawienia
jednostek i obrony, wyniki każdego scenariusza, bilans jednostek, wszystkie
fale oraz czasy i pozycje budowy wież. Opcja `--gif` zapisuje animację jednej
pełnej rozgrywki w `replay.gif` (odtwarzanie 3×). Raport pokazuje także
`spawn_timeline.png` i `unit_types.png`. Dodatkowe dane: `waves.csv`,
`spawns.csv`, `defense_builds.csv`, `detailed_report.json`.

Istniejący eksperyment można rozbudować bez ponownego treningu, zachowując
konfigurację i historię z `report.json`:

```bash
python -m src.experiment_report --input training_results/report.json --gif --replay-seed 101
```

Potrzebny jest Python 3.14 i Pillow (zależności z `pyproject.toml`, można też
uruchamiać polecenia przez `uv run`). Szybka próba:
`python train.py --population 8 --generations 3 --duration 45`.

Chromosom opisuje dwie fazy rozgrywki (zmiana w połowie czasu): proporcje
SCOUT/TANK/SPEED, próg energii rozpoczynający falę, część energii wydawaną
na falę i odstęp 0–12 sekund między startami fal. Reguły uwzględniają koszty,
regenerację, zwroty za zabite jednostki i trwającą kolejkę. Odstęp między
pojedynczymi gołębiami wynosi 0,3 s; kolejność tasuje symulator.

Selekcja turniejowa, krzyżowanie genów, mutacja i elitaryzm optymalizują
średnie obrażenia bazy w zadanym czasie. Wcześniejsze zniszczenie bazy
rozstrzyga remisy. Gołębie pozostające na trasie po upływie czasu nie dają
punktów. Populacja początkowa zawiera strategie porównawcze. Przeciwnik
stawia wieże w pobliżu trasy i reinwestuje nagrody za zabicia. Ziarno scenariusza
zmienia rozmieszczenie i kolejność typów wież oraz tasowanie fal.

Domyślnie trening używa ziaren 11, 22, 33, a test 101, 202, 303, 404, 505.
Opcje `--train-seeds`, `--test-seeds`, `--seed`, `--mutation-rate` i `--dt`
pozwalają zmienić eksperyment. Zbiory treningowe i testowe muszą być rozłączne.
Porównanie obejmuje strategie jednego typu i strategię mieszaną na tych samych
scenariuszach testowych. Test nie wpływa na wybór zwycięzcy treningu.

W katalogu wyników powstają:

- `best_strategy.json` — strategia do ponownego wykorzystania.
- `report.md`, `report.json` — porównanie, parametry, konfiguracja gry i przebieg.
- `generations.csv`, `comparison.csv`, `replay.csv` — dane do dalszej analizy.
- `evolution.png`, `diversity.png` — postęp uczenia i różnorodność populacji.
- `comparison.png` — średnie obrażenia na testach z zakresem minimum–maksimum.
- `combat.png`, `resources.png` — przebieg walki, energia i zdrowie bazy.
- `final_state.png` — mapa końcowa pierwszego scenariusza testowego.

Ocena zapisanej strategii bez ponownego treningu:

```bash
python train.py --strategy training_results/best_strategy.json --output evaluation
python -m unittest discover -s tests -v
```

`GeneticAgent(strategy, config["units"], duration).launch(simulation)` podejmuje
decyzję i wysyła falę w lokalnym symulatorze. Utwórz nowego agenta dla każdego
epizodu. Ten kontroler kieruje gołębiami lokalnie; protokół TCP Godota obsługuje
obecnie akcje budowy wież, więc nie podłączaj go jako polityki `GameServer`.

Algorytm znajduje najlepszą strategię spośród sprawdzonych kandydatów, bez
gwarancji globalnego optimum. Wyniki dotyczą przybliżonego symulatora,
wybranego czasu i modelu obrony; poprawę należy potwierdzić w Godocie.
Wykresy działają bez okna graficznego, z użyciem Pillow.

The Python project can receive live observations from Godot or run a local
training simulation. Both use newline-delimited UTF-8 JSON and the Godot
protocol version 2 state shape.

## Live TCP receiver

Start the passive receiver from `python_ai/`:

```bash
uv run python -m src.serwer
```

Godot connects to `127.0.0.1:8080`. The receiver logs episode updates and keeps
the latest `init` and `update` dictionaries in `GameServer`. A model can be
attached with the `policy` callback; it receives each decoded message and may
return an action dictionary or `None`:

```python
from src.serwer import GameServer


def choose_action(observation):
    if observation["type"] != "update":
        return None
    return {
        "action": "build_tower",
        "command_id": f"{observation['episode_id']}-{observation['step']}",
        "tower_type": "BASIC",
        "x": 3,
        "y": 3,
    }


GameServer(policy=choose_action).serve_forever()
```

`GameServer` parses multiple newline-delimited messages per TCP read, tolerates
split messages, validates JSON objects, and supports reconnects. A quick
one-shot connection test is available with
`uv run python -m src.serwer --build-once --tower-type BASIC --x 3 --y 3`.
Without a policy the receiver is passive and does not send actions.

## Local training simulation

Run a short simulation and save rendered frames plus JSON observations:

```bash
uv run python main.py --steps 600 --output frames
```

`src/simulation.py` consumes the checked-in balance and map configuration.
Its `Simulation` uses Godot's x-major `grid[x][y]` convention internally,
while `src/data.py` continues to read the map JSON's row-major layout.
`launch_wave()` charges the same unit energy costs; energy regenerates and
killed enemies refund the configured fraction. AI tower placements spend the
configured funds, kills pay each unit's configured reward, leaks damage the
base and increment the global enemy-speed multiplier, and towers use the
configured range, damage, and attack speed. Projectiles have a simple travel
time to keep combat closer to the live game.

The simulation exposes `to_dict()` snapshots with matching `map`, `resources`,
`units`, `towers`, `metrics`, `events`, `features`, and `feature_vector`
fields. The live Godot observation should remain authoritative; the local
simulation is an approximation for faster rollouts, not a pixel-perfect
replacement for Godot's physics and scene timing.

The Godot `init` message includes ordered `map.route_points` in x/y grid
coordinates. Use these points to preserve enemy direction; the route mask alone
does not identify the start and exit. It also provides `map.cell_size_px`,
`map.game_tile_size_px`, and `map.grid_origin_world`; the simulator uses the
pixel-size ratio to reproduce Godot's movement, range, and projectile speeds.

`src/simulator.py` remains as a compatibility import for older code.
`src/visualization.py` can render either a `Simulation` or a received Godot
snapshot, including tower ranges, kill/leak heatmaps, health and resource
summaries.
