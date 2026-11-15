"""Genetic tower placement policy shared by local training and Godot TCP."""
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
    tower_types: tuple[str, ...]
    # Four genes per build slot: type, normalized x, normalized y, earliest time.
    genes: tuple[float, ...]
    duration: float = 90
    role: str = "tower_defense"

    def __post_init__(self):
        if self.role != "tower_defense" or not self.tower_types or len(set(self.tower_types)) != len(self.tower_types):
            raise ValueError("Expected a tower_defense strategy with unique tower types")
        if not self.genes or len(self.genes) % 4:
            raise ValueError("Chromosome must contain four genes per build slot")
        if not math.isfinite(self.duration) or self.duration <= 0:
            raise ValueError("Strategy duration must be positive")
        if any(not math.isfinite(g) or not 0 <= g <= 1 for g in self.genes):
            raise ValueError("Genes must be finite values in [0, 1]")

    def save(self, path: str | Path):
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("role") != "tower_defense":
            raise ValueError("This file is not a tower-defense strategy; retrain with train.py")
        return cls(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])

    def decode(self, width: int, height: int) -> list[dict]:
        plans = []
        for i in range(0, len(self.genes), 4):
            kind, x, y, time = self.genes[i:i + 4]
            plans.append({"slot": i // 4, "tower_type": self.tower_types[min(len(self.tower_types) - 1,
                int(kind * len(self.tower_types)))], "x": round(x * (width - 1)),
                "y": round(y * (height - 1)), "earliest": time * self.duration})
        return sorted(plans, key=lambda p: (p["earliest"], p["slot"]))


class GeneticAgent:
    """Callable GameServer policy. Builds only; waits for command acknowledgement."""

    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.episode = None
        self.specs: dict = {}
        self.plans: list[dict] = []
        self.completed: set[int] = set()
        self.pending: dict | None = None
        self.next_build_at = 0.0
        self.last_step = -1
        self.sequence = 0

    def __call__(self, message: dict) -> dict | None:
        return self.predict(message)

    def predict(self, state: dict[str, Any]) -> dict[str, Any] | None:
        if state.get("type") == "init":
            episode = state.get("episode_id", "episode")
            if episode != self.episode:
                self.completed.clear()
                self.pending = None
                self.next_build_at = 0.0
                self.last_step = -1
            self.episode = episode
            self.specs = state.get("tower_types", {})
            if any(t not in self.specs or int(self.specs[t].get("cost", -1)) < 0
                   for t in self.strategy.tower_types):
                raise ValueError("Godot tower types/costs do not match the saved chromosome")
            grid = state.get("map_grid", [])
            if not grid or not grid[0]:
                raise ValueError("init must include an x-major map_grid")
            self.plans = self.strategy.decode(len(grid), len(grid[0]))
            return None
        if state.get("type") != "update" or not self.plans or state.get("terminal"):
            return None
        if state.get("episode_id", "episode") != self.episode:
            return None  # Wait for init: no inference from a different episode.
        step = int(state.get("step", 0))
        if step <= self.last_step:
            return None
        self.last_step = step
        now = float(state.get("elapsed_seconds", 0))
        grid = state.get("map_grid", [])
        if not grid:
            return None
        if self.pending:
            p = self.pending
            result = next((e for e in reversed(state.get("events", []))
                           if e.get("kind") == "action_result" and e.get("command_id") == p["command_id"]), None)
            if result:
                if result.get("accepted"):
                    self.completed.add(p["slot"])
                self.pending = None
            elif now - p["sent_at"] < 2:
                return None
            else:
                # Lost acknowledgement: authoritative occupied grid confirms
                # completion; otherwise the slot can be retried on fresh state.
                if grid[p["x"]][p["y"]] == 2:
                    self.completed.add(p["slot"])
                self.pending = None
        if now + 1e-9 < self.next_build_at:
            return None
        money = int(state.get("resources", {}).get("ai_money", state.get("ai_money", 0)))
        for plan in self.plans:
            if plan["slot"] in self.completed or plan["earliest"] > now + 1e-9:
                continue
            if int(self.specs[plan["tower_type"]]["cost"]) > money:
                continue
            # Resolve blocked/occupied chromosome targets against the current
            # observation, never an optimistic local copy of the Godot map.
            cells = ((x, y) for x, column in enumerate(grid) for y, value in enumerate(column) if value == 1)
            cell = min(cells, key=lambda c: ((c[0] - plan["x"]) ** 2 + (c[1] - plan["y"]) ** 2, c), default=None)
            if cell is None:
                return None
            self.sequence += 1
            action = {"action": "build_tower", "command_id": f"ga-{self.episode}-{step}-{self.sequence}-s{plan['slot']}",
                "tower_type": plan["tower_type"], "x": cell[0], "y": cell[1]}
            self.pending = {**action, "slot": plan["slot"], "sent_at": now}
            self.next_build_at = now + 0.5
            return action
        return None


def init_message(sim: Simulation) -> dict:
    return {**sim.to_dict(), "type": "init", "tower_types": sim.tower_types,
            "unit_types": sim.unit_types}


def attack_schedule(config: dict, seed: int, duration: float) -> tuple[str, list[dict]]:
    """Fixed requested waves independent of the chromosome; same energy rules."""
    names = list(config["units"])
    if not names or any(int(config["units"][n]["energy_cost"]) <= 0 for n in names):
        raise ValueError("Need units with positive energy costs")
    profiles = names + ["MIXED", "BURST"]
    profile = profiles[seed % len(profiles)]
    rng = random.Random(seed)
    waves, now = [], 0.0
    maximum = int(config["economy"]["player"].get("max_energy", 100))
    while now < duration:
        units, budget = [], min(maximum, 35 if profile != "BURST" else 65)
        while True:
            choices = [n for n in names if (profile in ("MIXED", "BURST") or n == profile)
                       and config["units"][n]["energy_cost"] <= budget]
            if not choices:
                break
            name = rng.choice(choices)
            units.append(name)
            budget -= config["units"][name]["energy_cost"]
        if units:
            waves.append({"scheduled_time": now, "unit_types": units,
                          "cost": sum(config["units"][n]["energy_cost"] for n in units)})
        now += rng.uniform(11, 16) if profile != "BURST" else rng.uniform(20, 26)
    return profile, waves


def rollout(strategy: Strategy | None, config: dict, map_data: dict, seed: int, *,
            duration: float = 90, dt: float = 0.1, trace: bool = False,
            on_frame: Callable[[dict], None] | None = None, frame_interval: float = 0.5) -> dict:
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(dt) or not 0 < dt <= 0.3:
        raise ValueError("Need positive duration and dt in (0, 0.3]")
    if not math.isfinite(frame_interval) or frame_interval <= 0:
        raise ValueError("Frame interval must be positive")
    sim = Simulation(config, map_data, seed=seed)
    agent = GeneticAgent(strategy) if strategy else None
    if agent:
        agent(init_message(sim))
    profile, schedule = attack_schedule(config, seed, duration)
    index = sent = spawned = 0
    next_decision = next_frame = 0.0
    events, waves, history = [], [], []
    last_event = 0
    if on_frame:
        on_frame(sim.to_dict())
        next_frame = frame_interval
    last_frame_step = 0
    for _ in range(math.ceil(duration / dt)):
        if sim.episode_done:
            break
        if index < len(schedule) and sim.sim_time + 1e-9 >= schedule[index]["scheduled_time"] and not sim.wave_active:
            wave = schedule[index]
            if sim.launch_wave(wave["unit_types"]):
                sent += len(wave["unit_types"])
                if trace:
                    waves.append({**wave, "time": sim.sim_time, "spawn_order": list(sim.queued_units)})
                index += 1
        if agent and sim.sim_time + 1e-9 >= next_decision:
            action = agent(sim.to_dict())
            if action:
                sim.apply_action(action)
            next_decision += 0.5
        # Count spawns from queue changes, avoiding serialization on every tick.
        queued_before = len(sim.queued_units)
        sim.step(min(dt, duration - sim.sim_time), return_state=False)
        spawned += queued_before - len(sim.queued_units)
        if trace:
            events.extend(e for e in sim.events if int(e["event_id"].rsplit(":", 1)[1]) > last_event)
            last_event = sim._event_sequence
            history.append({"time": sim.sim_time, "base_hp": sim.base_health, "ai_money": sim.ai_money,
                "energy": sim.energy, "kills": sim.metrics["kills_total"], "leaks": sim.metrics["leaks_total"],
                "alive": len(sim.enemies), "towers": len(sim.towers)})
        if on_frame and sim.sim_time + 1e-9 >= next_frame:
            on_frame(sim.to_dict())
            last_frame_step = sim.step_number
            next_frame += frame_interval
    if on_frame and last_frame_step != sim.step_number:
        on_frame(sim.to_dict())
    damage, kills = sim.metrics["base_damage_total"], sim.metrics["kills_total"]
    result = {"seed": seed, "profile": profile, "fitness": -damage + 0.1 * kills / max(spawned, 1),
        "damage": damage, "base_hp": sim.base_health, "kills": kills, "sent": sent, "spawned": spawned,
        "tower_count": len(sim.towers), "money_spent": sim.metrics["ai_money_spent_total"],
        "money_left": sim.ai_money, "rejected": sim.metrics["ai_actions_rejected"], "elapsed": sim.sim_time}
    if trace:
        result.update(history=history, waves=waves, schedule=schedule, events=events, final_state=sim.to_dict())
    return result


def baseline_strategies(config: dict, map_data: dict, slots: int = 10, duration: float = 90) -> dict:
    sim = Simulation(config, map_data)
    names = tuple(config["towers"])
    samples = [sim._point_at(sim.route_length * i / 40) for i in range(41)]
    cells = [(x, y) for x, col in enumerate(sim.grid) for y, v in enumerate(col) if v == 1]
    if not names or not cells or slots < 1:
        raise ValueError("Need tower types, free buildable cells and positive slots")
    policies = {}
    for label in names + ("MIXED",):
        genes, used, coverage = [], set(), [0] * len(samples)
        for i in range(slots):
            name = names[i % len(names)] if label == "MIXED" else label
            radius = config["towers"][name]["range"] * sim.cells_per_game_tile
            available = [c for c in cells if c not in used] or cells
            cell = max(available, key=lambda c: sum(1 / (1 + coverage[j]) for j, p in enumerate(samples)
                                                   if math.dist(c, p) <= radius))
            used.add(cell)
            for j, point in enumerate(samples):
                coverage[j] += math.dist(cell, point) <= radius
            genes.extend(((names.index(name) + 0.5) / len(names), cell[0] / max(1, sim.width - 1),
                          cell[1] / max(1, sim.height - 1), 0))
        policies[label] = Strategy(names, tuple(genes), duration)
    return policies


def train(config: dict, map_data: dict, *, population_size: int = 32, generations: int = 30,
          seeds: tuple[int, ...] = (10, 11, 12, 13, 14), seed: int = 42, duration: float = 90,
          dt: float = 0.1, mutation_rate: float = 0.15, slots: int = 10,
          progress: Callable[[dict], None] | None = None) -> tuple[Strategy, list[dict]]:
    if population_size < 4 or generations < 1 or not seeds or not 0 <= mutation_rate <= 1 or slots < 1:
        raise ValueError("Need population >= 4, generations >= 1, seeds, slots >= 1 and mutation rate in [0,1]")
    rng = random.Random(seed)
    policies = baseline_strategies(config, map_data, slots, duration)
    population = list(policies.values())[:population_size]
    while len(population) < population_size:
        # Seed useful early builds while exploring locations, types and delays.
        genes = tuple(rng.random() * (0.2 if i % 4 == 3 else 1) for i in range(slots * 4))
        population.append(Strategy(tuple(config["towers"]), genes, duration))
    cache, history = {}, []
    for generation in range(generations):
        for policy in population:
            if policy not in cache:
                cache[policy] = statistics.mean(rollout(policy, config, map_data, s, duration=duration, dt=dt)["fitness"] for s in seeds)
        ranked = sorted(population, key=lambda p: cache[p], reverse=True)
        scores = [cache[p] for p in population]
        row = {"generation": generation, "best": max(scores), "mean": statistics.mean(scores),
            "worst": min(scores), "std": statistics.pstdev(scores), "diversity": len(set(population)) / population_size}
        history.append(row)
        if progress:
            progress(row)
        if generation + 1 == generations:
            break
        children = ranked[:max(1, population_size // 8)]
        while len(children) < population_size:
            parents = [max(rng.sample(population, 3), key=lambda p: cache[p]) for _ in range(2)]
            genes = []
            for a, b in zip(parents[0].genes, parents[1].genes):
                value = rng.choice((a, b))
                if rng.random() < mutation_rate:
                    value = min(1, max(0, value + rng.gauss(0, 0.15)))
                genes.append(value)
            children.append(Strategy(tuple(config["towers"]), tuple(genes), duration))
        population = children
    return ranked[0], history
