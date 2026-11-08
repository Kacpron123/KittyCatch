# KittyCatch

Reverse tower defense game.

## Godot ↔ AI protocol

Godot is the TCP client (default `127.0.0.1:8080`). Each message is one
UTF-8 JSON object followed by `\n`. `protocol_version: 2` identifies the
observation format. Godot sends an `init` once per episode and a complete
`update` snapshot every 0.5 seconds, plus snapshots immediately after AI
actions and wave starts. If the AI is disconnected, Godot keeps the latest
snapshot and sends it after reconnecting.

### Initialization

The `init` message contains:

- `episode_id`: identifier for the current game; pair it with `step` to label
  training transitions.
- `map_size` and `grid_orientation`: coordinates are zero-based and all grids
  are x-major (`grid[x][y]`).
- `map_grid`: live build state (`0` not buildable, `1` free buildable cell,
  `2` occupied by a tower).
- `map.buildable_grid`: static buildability mask; `map.route_grid`: sampled
  enemy route mask. Both use `1` for true and `0` for false.
- `map.route_points`: ordered route points in x/y grid coordinates, from spawn
  to base; use this order to simulate enemy movement.
- `map.cell_size_px`, `game_tile_size_px`, and `grid_origin_world`: convert
  grid coordinates to the Godot world scale.
- `unit_types`, `tower_types`, `economy`, and `combat`: current balance data.
- Initial AI funds, player energy, base health, speed modifier, action-space
  description, and `feature_schema`.

### Observations

Each `update` is a full snapshot, not a patch. Consumers can safely replace
their previous state with it. Important fields:

| Field | Contents |
|---|---|
| `episode_id`, `step`, `elapsed_seconds` | Episode and observation ordering |
| `resources.ai_money` | AI's currently spendable money |
| `resources.ai_money_earned_total`, `ai_money_spent_total` | Cumulative AI economy |
| `resources.player_energy`, `player_max_energy` | Player wave resource |
| `resources.base_health`, `base_max_health` | Remaining base health |
| `map.kill_grid`, `map.leak_grid` | Cumulative kill and base-leak counts per cell |
| `map.tower_type_grid` | Tower IDs per cell: `0` empty, `1` BASIC, `2` SNIPER |
| `units` | Live unit type, health, progress, speed, grid and world position |
| `towers` | Tower type, position, damage, range, attack speed, target progress |
| `wave` | Spawn status, queued and active unit counts/types, interval and timer |
| `terminal` | Whether the base has been destroyed |
| `counts` | Live unit and tower counts by type |
| `metrics` | Cumulative kills, leaks, damage, economy and action counts |
| `events` | Most recent 128 events, each with a unique `event_id` |
| `features` | Named, normalized scalar inputs |
| `feature_vector` | Fixed-order scalar inputs matching `feature_schema` |

`kill_grid` records where units were killed, and `leak_grid` records where they
reached the base. Event entries include the unit type, cell and world position,
money earned or base damage, and the episode event ID. The cumulative maps and
metrics remain useful if the AI misses individual events; deduplicate events
by `event_id`. Calculate transition rewards by differencing cumulative metrics
between received snapshots, rather than assuming every intermediate update was
received.

The first five vector values are fractions normalized to `[0, 1]`; unit and
tower counts are raw integers (scale them during training). The fixed scalar
feature order is:

1. AI money fraction
2. Player energy fraction
3. Base health fraction
4. Enemy speed bonus fraction
5. Buildable-cell occupancy fraction
6. Active SCOUT, TANK, and SPEED counts
7. BASIC and SNIPER tower counts
8. Whether a wave is active (`0` or `1`)

For a neural policy, use the scalar vector alongside the spatial grid channels
and live entity lists. A convolutional encoder can learn map placement and
kill/leak hot spots; a small set/attention encoder can handle variable counts
of units and towers. Keep reward components separate while experimenting:
base damage/leaks should matter more than money spent, while kills and action
validity can provide shaping. Spending is not inherently bad when it prevents
damage, and money is already an observation/resource rather than a reliable
standalone reward.

### AI actions

The AI can place a tower by sending:

```json
{"action":"build_tower","command_id":"episode-step-action","tower_type":"BASIC","x":3,"y":3}
```

`tower_type` accepts a name (`BASIC`, `SNIPER`) or enum index (`0`, `1`). `x`
and `y` are zero-based grid coordinates. Godot checks the tower type, buildable
cell, and available funds. The resulting `action_result` event reports
acceptance or a rejection reason and echoes `command_id` when provided. The AI
may choose to wait by sending no action.

Balance and economy values live in
[`godot_game/config/balance.json`](./godot_game/config/balance.json).
