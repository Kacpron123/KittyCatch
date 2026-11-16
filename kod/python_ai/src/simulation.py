from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any


Grid = list[list[int]]
Point = tuple[float, float]


def _x_major_grid(grid: list[list[int]], width: int, height: int) -> Grid:
    if len(grid) == width and all(len(column) == height for column in grid):
        return [[int(value) for value in column] for column in grid]
    if len(grid) == height and all(len(row) == width for row in grid):
        return [[int(grid[y][x]) for y in range(height)] for x in range(width)]
    raise ValueError(f"Grid dimensions do not match {width}x{height}")


def _route_mask(points: list[list[float]], width: int, height: int) -> Grid:
    mask = [[0 for _ in range(height)] for _ in range(width)]
    for start, end in zip(points, points[1:]):
        x0, y0 = round(start[0]), round(start[1])
        x1, y1 = round(end[0]), round(end[1])
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx - dy
        while True:
            if 0 <= x0 < width and 0 <= y0 < height:
                mask[x0][y0] = 1
            if x0 == x1 and y0 == y1:
                break
            double_error = 2 * error
            if double_error > -dy:
                error -= dy
                x0 += sx
            if double_error < dx:
                error += dx
                y0 += sy
    if len(points) == 1:
        x, y = round(points[0][0]), round(points[0][1])
        if 0 <= x < width and 0 <= y < height:
            mask[x][y] = 1
    return mask


def _route_points_from_mask(mask: Grid) -> list[Point]:
    cells = {
        (x, y)
        for x, column in enumerate(mask)
        for y, value in enumerate(column)
        if value
    }
    if not cells:
        return []

    def neighbors(cell: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = cell
        return [
            neighbor
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if neighbor in cells
        ]

    endpoints = sorted(cell for cell in cells if len(neighbors(cell)) == 1)
    if not endpoints:
        raise ValueError("Route mask has no endpoint; provide ordered route points")

    path = [endpoints[0]]
    previous: tuple[int, int] | None = None
    current = path[0]
    while True:
        next_cells = [cell for cell in neighbors(current) if cell != previous]
        if not next_cells:
            break
        next_cell = next_cells[0]
        if next_cell in path:
            break
        path.append(next_cell)
        previous, current = current, next_cell

    if len(path) != len(cells):
        raise ValueError(
            "Route mask is branched or disconnected; provide ordered route points"
        )
    return [(float(x), float(y)) for x, y in path]


@dataclass
class Enemy:
    unit_type: str
    x: float
    y: float
    hp: int
    max_hp: int
    base_speed: float
    energy_cost: int
    ai_reward: int
    progress: float = 0.0
    distance: float = 0.0
    alive: bool = True
    path_offset: float = 0.0


@dataclass
class Tower:
    x: int
    y: int
    tower_type: str
    damage: int
    range_cells: float
    range_tiles: float
    attack_speed: float
    cooldown: float = 0.0
    targets: list[Enemy] = field(default_factory=list)


@dataclass
class Projectile:
    x: float
    y: float
    target: Enemy
    damage: int


class Simulation:
    """Approximate Godot's tower defense rules using x-major grid coordinates."""

    protocol_version = 2
    max_event_history = 128

    def __init__(
        self,
        config_data: dict[str, Any],
        map_data: dict[str, Any],
        *,
        seed: int = 0,
    ) -> None:
        self.config = config_data
        self.map_data = map_data
        raw_grid = map_data.get("grid", map_data.get("map_grid"))
        if not isinstance(raw_grid, list) or not raw_grid:
            raise ValueError("Map data must include a non-empty grid")

        if map_data.get("grid_orientation") == "x_major":
            self.width = len(raw_grid)
            self.height = len(raw_grid[0])
            self.grid = _x_major_grid(raw_grid, self.width, self.height)
        else:
            self.height = len(raw_grid)
            self.width = len(raw_grid[0])
            self.grid = _x_major_grid(raw_grid, self.width, self.height)

        map_config = config_data.get("map", {})
        self.game_tile_size_px = float(
            map_config.get("game_tile_size_px", map_config.get("tile_size_px", 64))
        )
        self.cell_size_px = float(
            map_config.get("cell_size_px", self.game_tile_size_px)
        )
        if self.cell_size_px <= 0 or self.game_tile_size_px <= 0:
            raise ValueError("Map and gameplay tile sizes must be positive")
        self.cells_per_game_tile = self.game_tile_size_px / self.cell_size_px
        self.tile_size = int(self.cell_size_px)
        self.grid_origin_world = (0.0, 0.0)
        self.buildable_grid = [
            [1 if value == 1 else 0 for value in column] for column in self.grid
        ]
        points = map_data.get("path", map_data.get("route_points", []))
        self.route_points: list[Point] = [
            (float(point[0]), float(point[1])) for point in points
        ]
        if not self.route_points and map_data.get("route_grid"):
            self.route_grid = _x_major_grid(
                map_data["route_grid"], self.width, self.height
            )
            self.route_points = _route_points_from_mask(self.route_grid)
        else:
            self.route_grid = _route_mask(
                [list(point) for point in self.route_points], self.width, self.height
            )
        if len(self.route_points) < 2:
            raise ValueError("Map must provide at least two ordered route points")

        self._route_lengths = [0.0]
        for start, end in zip(self.route_points, self.route_points[1:]):
            self._route_lengths.append(
                self._route_lengths[-1] + math.dist(start, end)
            )
        self.route_length = self._route_lengths[-1]
        if self.route_length <= 0:
            raise ValueError("Route must have a positive length")

        economy = config_data.get("economy", {})
        player_economy = economy.get("player", {})
        ai_economy = economy.get("ai", {})
        combat = config_data.get("combat", {})
        self.tower_range_scale = float(combat.get("tower_range_scale", 1.0))
        self.enemy_hit_radius_cells = float(combat.get("enemy_hit_radius_px", 0)) / self.cell_size_px
        self.enemy_path_spread_cells = float(combat.get("enemy_path_spread_px", 0)) / self.cell_size_px
        self.initial_ai_money = int(ai_economy.get("starting_money", 150))
        self.ai_money = self.initial_ai_money
        self.energy = int(player_economy.get("starting_energy", 40))
        self.max_energy = int(player_economy.get("max_energy", 100))
        self.energy_regen_per_second = float(
            player_economy.get("energy_regen_per_second", 1.0)
        )
        self.kill_energy_refund_fraction = float(
            player_economy.get("kill_energy_refund_fraction", 0.6)
        )
        self.base_max_health = int(config_data.get("base", {}).get("health", 1000))
        self.base_health = self.base_max_health
        self.enemy_speed_bonus_per_base_hit = float(
            combat.get("enemy_speed_bonus_per_base_hit", 0.005)
        )
        self.max_enemy_speed_bonus = float(
            combat.get("max_enemy_speed_bonus", 0.1)
        )
        self.enemy_speed_multiplier = 1.0

        self.unit_types = config_data.get("units", {})
        self.tower_types = config_data.get("towers", {})
        self.enemies: list[Enemy] = []
        self.towers: list[Tower] = []
        self.projectiles: list[Projectile] = []
        self.queued_units: deque[str] = deque()
        self.wave_active = False
        self.spawn_interval = 0.3
        self.spawn_time_left = 0.0
        self.energy_fractional = 0.0
        self.sim_time = 0.0
        self.step_number = 0
        self.episode_id = f"simulation-{seed}"
        self.episode_done = False
        self._rng = random.Random(seed)
        self._spread_rng = random.Random(seed + 104729)
        self._event_sequence = 0
        self.events: deque[dict[str, Any]] = deque(maxlen=self.max_event_history)
        self.kill_grid = self._empty_grid()
        self.leak_grid = self._empty_grid()
        self.tower_type_grid = self._empty_grid()
        self.kills_by_type = {name: 0 for name in self.unit_types}
        self.leaks_by_type = {name: 0 for name in self.unit_types}
        self.metrics: dict[str, int] = {
            "kills_total": 0,
            "leaks_total": 0,
            "base_damage_total": 0,
            "ai_money_earned_total": 0,
            "ai_money_spent_total": 0,
            "ai_actions_accepted": 0,
            "ai_actions_rejected": 0,
        }

    @classmethod
    def from_init(cls, message: dict[str, Any], *, seed: int = 0) -> Simulation:
        map_info = message.get("map", {})
        map_grid = message.get("map_grid")
        if not isinstance(map_grid, list):
            raise ValueError("Godot init message is missing map_grid")
        width = int(message.get("map_size", {}).get("width", len(map_grid)))
        height = int(
            message.get("map_size", {}).get("height", len(map_grid[0]) if map_grid else 0)
        )
        config = {
            "economy": message.get("economy", {}),
            "combat": message.get("combat", {}),
            "units": message.get("unit_types", {}),
            "towers": message.get("tower_types", {}),
            "map": message.get("map_config", {"tile_size_px": 64}),
            "base": message.get("base", {}),
        }
        map_data = {
            "grid": map_info.get("buildable_grid", map_grid),
            "path": map_info.get("route_points", message.get("route_points", [])),
            "route_grid": map_info.get("route_grid", []),
            "grid_orientation": message.get("grid_orientation", "x_major"),
        }
        config["map"] = {
            "tile_size_px": map_info.get("game_tile_size_px", 64),
            "game_tile_size_px": map_info.get("game_tile_size_px", 64),
            "cell_size_px": map_info.get("cell_size_px", 32),
        }
        if not map_data["path"] and not map_data["route_grid"]:
            raise ValueError("Godot init message must include route_points or map.route_grid")
        simulation = cls(config, map_data, seed=seed)
        simulation.width = width
        simulation.height = height
        origin = map_info.get("grid_origin_world", [0.0, 0.0])
        simulation.grid_origin_world = (float(origin[0]), float(origin[1]))
        simulation.ai_money = int(message.get("ai_money", message.get("money", simulation.ai_money)))
        simulation.initial_ai_money = simulation.ai_money
        player = message.get("player", {})
        simulation.energy = int(player.get("energy", simulation.energy))
        simulation.max_energy = int(player.get("max_energy", simulation.max_energy))
        base = message.get("base", {})
        simulation.base_health = int(base.get("health", simulation.base_health))
        simulation.base_max_health = int(base.get("max_health", simulation.base_max_health))
        simulation.episode_id = str(message.get("episode_id", simulation.episode_id))
        return simulation

    def _empty_grid(self) -> Grid:
        return [[0 for _ in range(self.height)] for _ in range(self.width)]

    def _cell(self, x: float, y: float) -> tuple[int, int]:
        return math.floor(x), math.floor(y)

    def _point_at(self, distance: float) -> Point:
        distance = min(max(distance, 0.0), self.route_length)
        for index in range(1, len(self.route_points)):
            if distance <= self._route_lengths[index]:
                start = self.route_points[index - 1]
                end = self.route_points[index]
                segment_length = self._route_lengths[index] - self._route_lengths[index - 1]
                ratio = (distance - self._route_lengths[index - 1]) / segment_length
                return (
                    start[0] + (end[0] - start[0]) * ratio,
                    start[1] + (end[1] - start[1]) * ratio,
                )
        return self.route_points[-1]

    def _record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self._event_sequence += 1
        event.update(
            {
                "event_id": f"{self.episode_id}:{self._event_sequence}",
                "step": self.step_number,
                "elapsed_seconds": self.sim_time,
            }
        )
        self.events.append(event)
        return event

    def launch_wave(self, unit_types: list[str], spawn_interval: float = 0.3) -> bool:
        if self.episode_done:
            return False
        normalized = [str(unit_type).upper() for unit_type in unit_types]
        if not normalized or any(unit not in self.unit_types for unit in normalized):
            return False
        cost = sum(int(self.unit_types[unit].get("energy_cost", 0)) for unit in normalized)
        if cost <= 0 or self.energy < cost:
            return False
        self.energy -= cost
        self._rng.shuffle(normalized)
        self.queued_units.clear()
        self.queued_units.extend(normalized)
        self.spawn_interval = max(float(spawn_interval), 0.01)
        self.spawn_time_left = self.spawn_interval
        self.wave_active = True
        self._record_event(
            {"kind": "wave_started", "unit_types": normalized, "energy_cost": cost}
        )
        return True

    def spawn_enemy(self, unit_type: str) -> Enemy:
        normalized = unit_type.upper()
        if normalized not in self.unit_types:
            raise ValueError(f"Unknown unit type: {unit_type}")
        stats = self.unit_types[normalized]
        start_x, start_y = self.route_points[0]
        enemy = Enemy(
            unit_type=normalized,
            x=start_x,
            y=start_y,
            hp=int(stats["hp"]),
            max_hp=int(stats["hp"]),
            base_speed=float(stats["speed"]),
            energy_cost=int(stats.get("energy_cost", 0)),
            ai_reward=int(stats.get("ai_reward", 0)),
            path_offset=self._spread_rng.uniform(-self.enemy_path_spread_cells, self.enemy_path_spread_cells),
        )
        self.enemies.append(enemy)
        self._record_event(
            {"kind": "unit_spawned", "unit_type": normalized, "grid_x": round(start_x), "grid_y": round(start_y)}
        )
        return enemy

    def build_tower(self, x: int, y: int, tower_type: str = "BASIC") -> bool:
        return bool(
            self.apply_action(
                {
                    "action": "build_tower",
                    "tower_type": tower_type,
                    "x": x,
                    "y": y,
                    "command_id": f"sim-{self.step_number}-{self._event_sequence}",
                }
            )["accepted"]
        )

    def apply_action(self, action: dict[str, Any]) -> dict[str, Any]:
        tower_type = str(action.get("tower_type", "")).upper()
        x, y = action.get("x"), action.get("y")
        reason = "built"
        cost = 0
        accepted = False
        if action.get("action") != "build_tower":
            reason = "unsupported_action"
        elif tower_type not in self.tower_types:
            reason = "unknown_tower_type"
        elif not isinstance(x, int) or isinstance(x, bool) or not isinstance(y, int) or isinstance(y, bool):
            reason = "invalid_coordinates"
        elif not (0 <= x < self.width and 0 <= y < self.height):
            reason = "cell_not_buildable"
        elif self.grid[x][y] != 1:
            reason = "cell_not_buildable"
        else:
            stats = self.tower_types[tower_type]
            cost = int(stats.get("cost", -1))
            if cost < 0:
                reason = "invalid_tower_cost"
            elif self.ai_money < cost:
                reason = "insufficient_funds"
            else:
                self.ai_money -= cost
                self.metrics["ai_money_spent_total"] += cost
                self.grid[x][y] = 2
                self.tower_type_grid[x][y] = list(self.tower_types).index(tower_type) + 1
                self.towers.append(
                    Tower(
                        x=x,
                        y=y,
                        tower_type=tower_type,
                        damage=int(stats["damage"]),
                        range_cells=float(stats["range"]) * self.cells_per_game_tile * self.tower_range_scale,
                        range_tiles=float(stats["range"]),
                        attack_speed=max(float(stats.get("attack_speed", 1.0)), 0.01),
                    )
                )
                accepted = True

        metric = "ai_actions_accepted" if accepted else "ai_actions_rejected"
        self.metrics[metric] += 1
        return self._record_event(
            {
                "kind": "action_result",
                "action": "build_tower",
                "accepted": accepted,
                "reason": reason,
                "tower_type": tower_type,
                "grid_x": x if isinstance(x, int) else -1,
                "grid_y": y if isinstance(y, int) else -1,
                "cost": cost if accepted else 0,
                "command_id": str(action.get("command_id", "")),
            }
        )

    def _move_enemies(self, dt: float) -> None:
        for enemy in self.enemies[:]:
            enemy.distance += (
                enemy.base_speed
                * self.cells_per_game_tile
                * self.enemy_speed_multiplier
                * dt
            )
            if enemy.distance >= self.route_length:
                enemy.distance = self.route_length
                enemy.x, enemy.y = self.route_points[-1]
                enemy.progress = 1.0
                self._leak(enemy)
                self.enemies.remove(enemy)
            else:
                enemy.x, enemy.y = self._point_at(enemy.distance)
                before = self._point_at(max(0, enemy.distance - 0.001))
                after = self._point_at(min(self.route_length, enemy.distance + 0.001))
                dx, dy = after[0] - before[0], after[1] - before[1]
                length = math.hypot(dx, dy)
                if length:
                    enemy.x -= dy / length * enemy.path_offset
                    enemy.y += dx / length * enemy.path_offset
                enemy.progress = enemy.distance / self.route_length

    def _fire_towers(self, dt: float) -> None:
        for tower in self.towers:
            inside = [enemy for enemy in self.enemies if enemy.alive and
                      math.hypot(tower.x - enemy.x, tower.y - enemy.y) <= tower.range_cells + self.enemy_hit_radius_cells]
            inside_ids = {id(enemy) for enemy in inside}
            tower.targets = [enemy for enemy in tower.targets if id(enemy) in inside_ids]
            queued_ids = {id(enemy) for enemy in tower.targets}
            tower.targets.extend(enemy for enemy in inside if id(enemy) not in queued_ids)
            if not tower.targets:
                # Godot stops the timer when no target is present and fires
                # immediately when a new target enters the area.
                tower.cooldown = 0.0
                continue
            tower.cooldown = max(0.0, tower.cooldown - dt)
            if tower.cooldown > 0.0:
                continue
            target = tower.targets[0]
            tower.cooldown = 1.0 / tower.attack_speed
            self.projectiles.append(Projectile(float(tower.x), float(tower.y), target, tower.damage))

    def _move_projectiles(self, dt: float) -> None:
        for projectile in self.projectiles[:]:
            target = projectile.target
            if not target.alive:
                self.projectiles.remove(projectile)
                continue
            dx, dy = target.x - projectile.x, target.y - projectile.y
            distance = math.hypot(dx, dy)
            travel = (400.0 / self.cell_size_px) * dt
            hit_distance = 12.0 / self.cell_size_px
            if distance <= max(travel, hit_distance):
                self._damage_enemy(target, projectile.damage)
                self.projectiles.remove(projectile)
            elif distance > 0:
                projectile.x += dx / distance * travel
                projectile.y += dy / distance * travel

    def _damage_enemy(self, enemy: Enemy, amount: int) -> None:
        if not enemy.alive:
            return
        enemy.hp -= amount
        if enemy.hp <= 0:
            enemy.hp = 0
            enemy.alive = False
            self.ai_money += enemy.ai_reward
            self.metrics["kills_total"] += 1
            self.metrics["ai_money_earned_total"] += enemy.ai_reward
            self.kills_by_type[enemy.unit_type] += 1
            refund = math.floor(enemy.energy_cost * self.kill_energy_refund_fraction)
            self.energy = min(self.max_energy, self.energy + refund)
            x, y = self._cell(enemy.x, enemy.y)
            self._increment_grid(self.kill_grid, x, y)
            self.enemies.remove(enemy)
            self._record_event(
                {
                    "kind": "unit_killed",
                    "unit_type": enemy.unit_type,
                    "grid_x": x,
                    "grid_y": y,
                    "ai_money_earned": enemy.ai_reward,
                    "player_energy_refunded": refund,
                }
            )

    def _leak(self, enemy: Enemy) -> None:
        if not enemy.alive:
            return
        enemy.alive = False
        refund = (enemy.energy_cost + 1) // 2
        self.energy = min(self.max_energy, self.energy + refund)
        self.base_health = max(0, self.base_health - 1)
        self.metrics["leaks_total"] += 1
        self.metrics["base_damage_total"] += 1
        self.leaks_by_type[enemy.unit_type] += 1
        self.enemy_speed_multiplier = min(
            self.enemy_speed_multiplier + self.enemy_speed_bonus_per_base_hit,
            1.0 + self.max_enemy_speed_bonus,
        )
        x, y = self._cell(enemy.x, enemy.y)
        self._increment_grid(self.leak_grid, x, y)
        self.episode_done = self.base_health <= 0
        self._record_event(
            {
                "kind": "base_damaged",
                "unit_type": enemy.unit_type,
                "grid_x": x,
                "grid_y": y,
                "base_damage": 1,
                "player_energy_refunded": refund,
                "enemy_speed_multiplier": self.enemy_speed_multiplier,
            }
        )

    def _increment_grid(self, grid: Grid, x: int, y: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            grid[x][y] += 1

    def step(self, dt: float = 0.1, ai_action: dict[str, Any] | None = None, *, return_state: bool = True) -> dict[str, Any] | None:
        if dt <= 0:
            raise ValueError("dt must be positive")
        if self.episode_done:
            return self.to_dict() if return_state else None

        if ai_action is not None:
            self.apply_action(ai_action)
        self.sim_time += dt
        self.step_number += 1
        if self.energy < self.max_energy:
            self.energy_fractional += self.energy_regen_per_second * dt
            energy_gained = math.floor(self.energy_fractional)
            if energy_gained:
                self.energy = min(self.max_energy, self.energy + energy_gained)
                self.energy_fractional -= energy_gained
                if self.energy >= self.max_energy:
                    self.energy_fractional = 0.0

        if self.wave_active:
            self.spawn_time_left -= dt
            if self.spawn_time_left <= 0:
                if self.queued_units:
                    self.spawn_enemy(self.queued_units.popleft())
                    self.spawn_time_left += self.spawn_interval
                else:
                    self.wave_active = False

        self._move_enemies(dt)
        self._fire_towers(dt)
        self._move_projectiles(dt)
        return self.to_dict() if return_state else None

    def _tower_counts(self) -> dict[str, int]:
        counts = {name: 0 for name in self.tower_types}
        for tower in self.towers:
            counts[tower.tower_type] += 1
        return counts

    def _enemy_counts(self) -> dict[str, int]:
        counts = {name: 0 for name in self.unit_types}
        for enemy in self.enemies:
            counts[enemy.unit_type] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        enemy_counts = self._enemy_counts()
        tower_counts = self._tower_counts()
        total_buildable = sum(value == 1 for column in self.buildable_grid for value in column)
        money_fraction = self.ai_money / max(self.ai_money + self.metrics["ai_money_spent_total"], 1)
        energy_fraction = self.energy / max(self.max_energy, 1)
        health_fraction = self.base_health / max(self.base_max_health, 1)
        speed_bonus_fraction = (self.enemy_speed_multiplier - 1.0) / max(
            self.max_enemy_speed_bonus, 0.0001
        )
        occupancy_fraction = len(self.towers) / max(total_buildable, 1)
        features = {
            "ai_money_fraction": money_fraction,
            "player_energy_fraction": energy_fraction,
            "base_health_fraction": health_fraction,
            "enemy_speed_bonus_fraction": speed_bonus_fraction,
            "buildable_occupancy_fraction": occupancy_fraction,
        }
        feature_vector = [
            money_fraction,
            energy_fraction,
            health_fraction,
            speed_bonus_fraction,
            occupancy_fraction,
            float(enemy_counts.get("SCOUT", 0)),
            float(enemy_counts.get("TANK", 0)),
            float(enemy_counts.get("SPEED", 0)),
            float(tower_counts.get("BASIC", 0)),
            float(tower_counts.get("SNIPER", 0)),
            float(self.wave_active),
        ]
        units = [
            {
                "type": enemy.unit_type,
                "type_id": list(self.unit_types).index(enemy.unit_type),
                "health": enemy.hp,
                "max_health": enemy.max_hp,
                "health_fraction": enemy.hp / max(enemy.max_hp, 1),
                "progress": enemy.progress,
                "speed": enemy.base_speed
                * self.game_tile_size_px
                * self.enemy_speed_multiplier,
                "grid_x": math.floor(enemy.x),
                "grid_y": math.floor(enemy.y),
                "x": round(
                    self.grid_origin_world[0] + enemy.x * self.cell_size_px
                ),
                "y": round(
                    self.grid_origin_world[1] + enemy.y * self.cell_size_px
                ),
            }
            for enemy in self.enemies
        ]
        towers = [
            {
                "type": tower.tower_type,
                "type_id": list(self.tower_types).index(tower.tower_type),
                "x": tower.x,
                "y": tower.y,
                "damage": tower.damage,
                "range": tower.range_tiles,
                "range_cells": tower.range_cells,
                "attack_speed": tower.attack_speed,
                "target_progress": -1.0,
            }
            for tower in self.towers
        ]
        metrics = dict(self.metrics)
        metrics["kills_by_type"] = dict(self.kills_by_type)
        metrics["leaks_by_type"] = dict(self.leaks_by_type)
        return {
            "protocol_version": self.protocol_version,
            "type": "update",
            "episode_id": self.episode_id,
            "step": self.step_number,
            "elapsed_seconds": self.sim_time,
            "map_grid": self.grid,
            "ai_money": self.ai_money,
            "enemy_speed_multiplier": self.enemy_speed_multiplier,
            "resources": {
                "ai_money": self.ai_money,
                "ai_money_earned_total": self.metrics["ai_money_earned_total"],
                "ai_money_spent_total": self.metrics["ai_money_spent_total"],
                "player_energy": self.energy,
                "player_max_energy": self.max_energy,
                "base_health": self.base_health,
                "base_max_health": self.base_max_health,
            },
            "player": {"energy": self.energy, "max_energy": self.max_energy},
            "base": {"health": self.base_health, "max_health": self.base_max_health},
            "wave": {
                "active": self.wave_active,
                "queued_units": list(self.queued_units),
                "queued_count": len(self.queued_units),
                "active_unit_count": len(units),
                "spawn_interval": self.spawn_interval,
                "spawn_time_left": self.spawn_time_left,
            },
            "terminal": self.episode_done,
            "map": {
                "width": self.width,
                "height": self.height,
                "orientation": "x_major",
                "cell_size_px": self.cell_size_px,
                "game_tile_size_px": self.game_tile_size_px,
                "grid_origin_world": list(self.grid_origin_world),
                "buildable_grid": self.buildable_grid,
                "available_buildable_cells": total_buildable - len(self.towers),
                "route_grid": self.route_grid,
                "tower_type_grid": self.tower_type_grid,
                "kill_grid": self.kill_grid,
                "leak_grid": self.leak_grid,
            },
            "units": units,
            "towers": towers,
            "counts": {"enemies_by_type": enemy_counts, "towers_by_type": tower_counts},
            "metrics": metrics,
            "events": list(self.events),
            "features": features,
            "feature_vector": feature_vector,
        }


Simulator = Simulation
