import copy
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.data import load_game_data
from src.wave_ai import GeneticAgent, Strategy, baseline_strategies, rollout, train
from src.simulation import Simulation
from src.wave_report import build_report, decode
from PIL import Image


class GeneticTests(unittest.TestCase):
    def setUp(self):
        self.config, self.map_data = load_game_data()
        self.types = tuple(self.config["units"])
        self.policy = baseline_strategies(self.types)["SCOUT"]

    def test_launch_respects_energy_queue_and_cooldown(self):
        genes = (1, 0, 0, 0, 1, 1) * 2
        agent = GeneticAgent(Strategy(self.types, genes), self.config["units"])
        sim = Simulation(self.config, self.map_data)
        action = agent.launch(sim)
        self.assertEqual(action["unit_types"], ["SCOUT"] * 10)
        self.assertEqual(sim.energy, 0)
        self.assertIsNone(agent.launch(sim))
        sim.wave_active = False
        sim.queued_units.clear()
        sim.energy = 100
        sim.sim_time = 11
        self.assertIsNone(agent.launch(sim))
        sim.sim_time = 12
        self.assertIsNotNone(agent.launch(sim))

    def test_rollout_is_reproducible_and_accounts_for_every_unit(self):
        first = rollout(self.policy, self.config, self.map_data, 17, duration=35, trace=True)
        self.assertEqual(first, rollout(self.policy, self.config, self.map_data, 17, duration=35, trace=True))
        state = first["final_state"]
        self.assertEqual(first["sent"], first["kills"] + first["damage"] +
                         len(state["units"]) + state["wave"]["queued_count"])
        self.assertEqual(first["energy_spent"], sum(w["cost"] for w in first["waves"]))
        self.assertGreater(first["sent"], 0)
        self.assertTrue(all(0 <= row["energy"] <= 100 for row in first["history"]))

    def test_no_defense_causes_real_damage(self):
        config = copy.deepcopy(self.config)
        config["towers"] = {}
        result = rollout(self.policy, config, self.map_data, 1, duration=40)
        self.assertGreater(result["damage"], 0)
        self.assertEqual(result["fitness"], result["damage"])

    def test_training_is_reproducible_and_elitist(self):
        kwargs = dict(population_size=4, generations=3, seeds=(3,), duration=30)
        best, history = train(self.config, self.map_data, **kwargs)
        self.assertEqual((best, history), train(self.config, self.map_data, **kwargs))
        self.assertEqual([r["best"] for r in history], sorted(r["best"] for r in history))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "strategy.json"
            best.save(path)
            self.assertEqual(best, Strategy.load(path))

    def test_fast_steps_match_normal_simulation(self):
        a, b = (Simulation(self.config, self.map_data) for _ in range(2))
        for sim in (a, b):
            sim.launch_wave(["SCOUT", "TANK"])
            sim.build_tower(10, 6)
        for _ in range(100):
            a.step()
            self.assertIsNone(b.step(return_state=False))
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_invalid_parameters(self):
        for dt in (0, -1, 0.4, float("nan")):
            with self.assertRaises(ValueError):
                rollout(self.policy, self.config, self.map_data, 1, dt=dt)
        with self.assertRaises(ValueError):
            train(self.config, self.map_data, population_size=1)
        with self.assertRaises(ValueError):
            Strategy(self.types, (float("nan"),) * 12)

    def test_complete_trace_survives_event_history_limit(self):
        config = copy.deepcopy(self.config)
        config["towers"] = {}
        result = rollout(self.policy, config, self.map_data, 1, duration=200, trace=True)
        self.assertGreater(len(result["events"]), Simulation.max_event_history)
        kinds = Counter(e["kind"] for e in result["events"])
        self.assertEqual(kinds["base_damaged"], result["damage"])
        self.assertEqual(kinds["wave_started"], len(result["waves"]))
        self.assertEqual(kinds["unit_spawned"], result["sent"] - len(result["final_state"]["wave"]["queued_units"]))

    def test_decoded_genes_and_report_gif(self):
        phases = decode(self.policy, self.config, 2)
        self.assertEqual(phases[0]["energy_threshold"], 4)
        self.assertEqual(phases[0]["spend_fraction"], 1)
        self.assertEqual(phases[1]["start"], 1)
        episode = rollout(self.policy, self.config, self.map_data, 1, duration=2)
        source = {"settings": {"duration": 2, "dt": 0.2, "test_seeds": [1]},
            "config": self.config, "map": self.map_data,
            "comparison": {"GENETIC": {"mean_damage": 0, "std_damage": 0, "episodes": [episode]}}}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            report = build_report(source, self.policy, output, make_gif=True)
            with Image.open(output / "replay.gif") as gif:
                self.assertGreater(gif.n_frames, 1)
                self.assertEqual(gif.n_frames, report["gif"]["frames"])
                gif.seek(gif.n_frames - 1)
                self.assertEqual(gif.info["duration"], 1500)
            for filename in ("report.md", "detailed_report.json", "waves.csv", "spawns.csv",
                             "defense_builds.csv", "spawn_timeline.png", "unit_types.png"):
                self.assertTrue((output / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
