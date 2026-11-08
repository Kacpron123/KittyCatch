# Python AI integration

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
