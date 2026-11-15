"""Reproducible genetic search for energy-constrained pigeon wave policies."""
from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from src.simulation import Simulation


@dataclass(frozen=True)
class Strategy:
    unit_types: tuple[str, ...]
    # Composition, energy threshold, spending fraction and cooldown, for each
    # of two phases (early and late game). All genes are normalized to [0, 1].
    genes: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.unit_types or len(self.genes) != 2 * (len(self.unit_types) + 3):
            raise ValueError("Strategy requires two phases and nonempty unit types")
        if any(not math.isfinite(g) or not 0 <= g <= 1 for g in self.genes):
            raise ValueError("Genes must be finite numbers between 0 and 1")

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Strategy:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(tuple(data["unit_types"]), tuple(data["genes"]))


class GeneticAgent:
    """Wave controller; construct a fresh agent for every episode."""

    def __init__(self, strategy: Strategy, units: dict[str, Any], duration: float = 90):
        self.strategy, self.units, self.duration = strategy, units, duration
        if not math.isfinite(duration) or duration <= 0 or any(
            name not in units or int(units[name]["energy_cost"]) <= 0 for name in strategy.unit_types
        ):
            raise ValueError("Duration and unit energy costs must be positive")
        self.next_wave_at = 0.0

    def predict(self, state: dict[str, Any]) -> dict[str, Any] | None:
        now = float(state.get("elapsed_seconds", 0))
        wave = state.get("wave", {})
        if state.get("terminal") or wave.get("active") or wave.get("queued_count", 0) or now < self.next_wave_at:
            return None
        resources = state.get("resources", {})
        energy = int(resources.get("player_energy", 0))
        maximum = int(resources.get("player_max_energy", 100))
        n = len(self.strategy.unit_types)
        offset = (n + 3) if now >= self.duration / 2 else 0
        genes = self.strategy.genes[offset:offset + n + 3]
        cheapest = min(int(self.units[t]["energy_cost"]) for t in self.strategy.unit_types)
        threshold = min(maximum, max(cheapest, round(genes[n] * maximum)))
        if energy < threshold:
            return None
        remaining = min(energy, max(cheapest, int(energy * (0.15 + 0.85 * genes[n + 1]))))
        selected: list[str] = []
        counts = [0] * n
        while True:
            affordable = [i for i, t in enumerate(self.strategy.unit_types)
                          if self.units[t]["energy_cost"] <= remaining and genes[i] > 0]
            if not affordable:
                break
            i = max(affordable, key=lambda j: genes[j] / (counts[j] + 1))
            name = self.strategy.unit_types[i]
            selected.append(name)
            counts[i] += 1
            remaining -= int(self.units[name]["energy_cost"])
        if not selected:
            return None
        return {"action": "launch_wave", "unit_types": selected, "cooldown": 12 * genes[n + 2]}

    def launch(self, sim: Simulation) -> dict[str, Any] | None:
        action = self.predict({"elapsed_seconds": sim.sim_time, "terminal": sim.episode_done,
            "wave": {"active": sim.wave_active, "queued_count": len(sim.queued_units)},
            "resources": {"player_energy": sim.energy, "player_max_energy": sim.max_energy}})
        if action and sim.launch_wave(action["unit_types"], spawn_interval=0.3):
            self.next_wave_at = sim.sim_time + action["cooldown"]
            return action
        return None


class Defense:
    """Seeded opponent: builds near the route and reinvests kill rewards."""

    def __init__(self, sim: Simulation, seed: int):
        rng = random.Random(seed)
        self.cells = []
        route = [sim._point_at(sim.route_length * i / 40) for i in range(41)]
        for x in range(sim.width):
            for y in range(sim.height):
                if sim.grid[x][y] == 1:
                    distance = min(math.dist((x, y), p) for p in route)
                    self.cells.append((distance + rng.uniform(0, 2.5), x, y))
        self.cells.sort()
        self.types = list(sim.tower_types)
        rng.shuffle(self.types)
        self.index = 0

    def build(self, sim: Simulation) -> None:
        while self.types:
            tower_type = self.types[self.index % len(self.types)]
            if sim.ai_money < sim.tower_types[tower_type]["cost"]:
                return
            cell = next(((x, y) for _, x, y in self.cells if sim.grid[x][y] == 1), None)
            if cell is None or not sim.build_tower(*cell, tower_type):
                return
            self.index += 1


def rollout(strategy: Strategy, config: dict, map_data: dict, seed: int, *,
            duration: float = 90, dt: float = 0.2, trace: bool = False) -> dict[str, Any]:
    if not math.isfinite(duration) or not math.isfinite(dt) or duration <= 0 or not 0 < dt <= 0.3:
        raise ValueError("Duration must be positive and dt in (0, 0.3]")
    sim = Simulation(config, map_data, seed=seed)
    agent = GeneticAgent(strategy, config["units"], duration)
    defense = Defense(sim, seed)
    defense.build(sim)
    history, waves = [], []
    spent = sent = 0
    for step in range(math.ceil(duration / dt)):
        if sim.episode_done:
            break
        if step % max(1, round(1 / dt)) == 0:
            defense.build(sim)
        action = agent.launch(sim)
        if action:
            cost = sum(config["units"][name]["energy_cost"] for name in action["unit_types"])
            spent += cost
            sent += len(action["unit_types"])
            if trace:
                waves.append({"time": sim.sim_time, "cost": cost, **action})
        sim.step(min(dt, duration - sim.sim_time), return_state=False)
        if trace:
            history.append({"time": sim.sim_time, "base_hp": sim.base_health,
                "energy": sim.energy, "kills": sim.metrics["kills_total"],
                "leaks": sim.metrics["leaks_total"], "alive": len(sim.enemies), "towers": len(sim.towers)})
    damage = sim.metrics["base_damage_total"]
    # Actual damage only; earlier destruction breaks ties. No credit for units
    # still travelling at the end of the evaluation window.
    fitness = damage + (0.5 * (1 - sim.sim_time / duration) if sim.episode_done else 0)
    result = {"seed": seed, "fitness": fitness, "damage": damage,
        "kills": sim.metrics["kills_total"], "sent": sent, "energy_spent": spent,
        "damage_per_energy": damage / max(spent, 1), "elapsed": sim.sim_time}
    if trace:
        result.update(history=history, waves=waves, final_state=sim.to_dict())
    return result


def baseline_strategies(unit_types: tuple[str, ...]) -> dict[str, Strategy]:
    n = len(unit_types)
    policies = {name: Strategy(unit_types, tuple(([float(i == j) for i in range(n)] + [0, 1, 0]) * 2))
                for j, name in enumerate(unit_types)}
    policies["MIXED"] = Strategy(unit_types, tuple(([1.0] * n + [0, 1, 0]) * 2))
    return policies


def train(config: dict, map_data: dict, *, population_size: int = 24, generations: int = 20,
          seeds: tuple[int, ...] = (11, 22, 33), seed: int = 42, duration: float = 90,
          dt: float = 0.2, mutation_rate: float = 0.15,
          progress: Callable[[dict], None] | None = None) -> tuple[Strategy, list[dict]]:
    if population_size < 4 or generations < 1 or not seeds or not 0 <= mutation_rate <= 1:
        raise ValueError("Need population >= 4, generations >= 1, seeds and mutation rate in [0, 1]")
    unit_types = tuple(config["units"])
    if not unit_types or any(int(unit["energy_cost"]) <= 0 for unit in config["units"].values()):
        raise ValueError("At least one unit with positive energy cost is required")
    rng = random.Random(seed)
    size = 2 * (len(unit_types) + 3)
    population = list(baseline_strategies(unit_types).values())[:population_size]
    while len(population) < population_size:
        population.append(Strategy(unit_types, tuple(rng.random() for _ in range(size))))
    cache: dict[Strategy, float] = {}
    history = []
    for generation in range(generations):
        for strategy in population:
            if strategy not in cache:
                cache[strategy] = statistics.mean(rollout(strategy, config, map_data, s,
                    duration=duration, dt=dt)["fitness"] for s in seeds)
        ranked = sorted(population, key=lambda s: cache[s], reverse=True)
        scores = [cache[s] for s in population]
        row = {"generation": generation, "best": max(scores), "mean": statistics.mean(scores),
            "worst": min(scores), "std": statistics.pstdev(scores),
            "diversity": len(set(population)) / population_size}
        history.append(row)
        if progress:
            progress(row)
        if generation == generations - 1:
            break
        next_population = ranked[:max(1, population_size // 8)]
        while len(next_population) < population_size:
            parents = [max(rng.sample(population, min(3, population_size)), key=lambda s: cache[s])
                       for _ in range(2)]
            genes = []
            for a, b in zip(parents[0].genes, parents[1].genes):
                value = a if rng.random() < 0.5 else b
                if rng.random() < mutation_rate:
                    value = min(1, max(0, value + rng.gauss(0, 0.2)))
                genes.append(value)
            next_population.append(Strategy(unit_types, tuple(genes)))
        population = next_population
    return ranked[0], history
