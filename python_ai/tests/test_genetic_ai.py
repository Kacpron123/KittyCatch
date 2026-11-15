import copy
import tempfile
import unittest
from pathlib import Path

from src.data import load_game_data
from src.genetic_ai import GeneticAgent, Strategy, baseline_strategies, rollout, train
from src.simulation import Simulation


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
        self.assertEqual(action["unit_types"], ["SCOUT"] * 8)
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


if __name__ == "__main__":
    unittest.main()
