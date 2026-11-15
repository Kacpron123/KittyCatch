import copy
import json
import socket
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.data import load_game_data
from src.experiment_report import build_report
from src.genetic_ai import GeneticAgent, Strategy, attack_schedule, init_message, rollout, train
from src.serwer import GameServer
from src.simulation import Simulation


class TowerGeneticTests(unittest.TestCase):
    def setUp(self):
        self.config, self.map_data = load_game_data()
        self.sim = Simulation(self.config, self.map_data)
        # Two overlapping requested locations; second must use a new free cell.
        self.strategy = Strategy(tuple(self.config["towers"]), (0, 10/19, 6/14, 0) * 2, 40)

    def state(self):
        return self.sim.to_dict()

    def test_predict_only_builds_affordable_free_cells_and_waits_for_ack(self):
        agent = GeneticAgent(self.strategy)
        self.assertIsNone(agent(init_message(self.sim)))
        action = agent(self.state())
        self.assertEqual(action["action"], "build_tower")
        self.assertEqual((action["x"], action["y"]), (10, 6))
        self.assertNotIn("unit_types", action)
        self.assertIsNone(agent(self.state()))
        self.sim.step(0.5, return_state=False)
        self.assertIsNone(agent(self.state()))  # New state without acknowledgement.
        self.assertTrue(self.sim.apply_action(action)["accepted"])
        self.sim.step(0.1, return_state=False)
        second = agent(self.state())
        self.assertIsNotNone(second)
        self.assertNotEqual((action["x"], action["y"]), (second["x"], second["y"]))
        self.assertIn(0, agent.completed)
        self.assertTrue(self.sim.apply_action(second)["accepted"])

    def test_budget_time_and_episode_reset(self):
        strategy = Strategy(self.strategy.tower_types, (0, 0, 0, 0.5), 40)
        agent = GeneticAgent(strategy)
        agent(init_message(self.sim))
        self.assertIsNone(agent(self.state()))
        self.sim.sim_time, self.sim.step_number = 20, 20
        self.sim.ai_money = 49
        self.assertIsNone(agent(self.state()))
        self.sim.ai_money = 50
        self.sim.step_number += 1
        action = agent(self.state())
        self.assertIsNotNone(action)
        rejected = self.sim.apply_action({**action, "x": -1})
        self.assertFalse(rejected["accepted"])
        self.sim.step_number += 1
        self.sim.sim_time += 0.5
        self.assertIsNotNone(agent(self.state()))  # A rejection does not consume a slot.
        new_episode = Simulation(self.config, self.map_data, seed=23)
        agent(init_message(new_episode))
        self.assertIsNone(agent.pending)
        self.assertEqual(agent.completed, set())
        self.assertIsNone(agent(new_episode.to_dict()))

    def test_saved_strategy_rejects_old_wave_role(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "strategy.json"
            self.strategy.save(path)
            self.assertEqual(Strategy.load(path), self.strategy)
            path.write_text('{"unit_types":["SCOUT"],"genes":[0]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                Strategy.load(path)

    def test_schedule_and_training_are_reproducible(self):
        for seed, profile in zip(range(10, 15), ("SCOUT", "TANK", "SPEED", "MIXED", "BURST")):
            self.assertEqual(attack_schedule(self.config, seed, 40)[0], profile)
        result = rollout(self.strategy, self.config, self.map_data, 10, duration=40, trace=True)
        self.assertEqual(result, rollout(self.strategy, self.config, self.map_data, 10, duration=40, trace=True))
        self.assertEqual(result["rejected"], 0)
        state = result["final_state"]
        self.assertEqual(result["spawned"], result["kills"] + result["damage"] + len(state["units"]))
        kwargs = dict(population_size=4, generations=2, slots=2, seeds=(10,), duration=10)
        best, history = train(self.config, self.map_data, **kwargs)
        self.assertEqual((best, history), train(self.config, self.map_data, **kwargs))
        self.assertGreaterEqual(history[-1]["best"], history[0]["best"])

    def test_actual_policy_json_round_trip_through_server(self):
        agent = GeneticAgent(self.strategy)
        server = GameServer(policy=agent)
        endpoint, client = socket.socketpair()
        client.settimeout(1)
        try:
            server._handle_line(endpoint, json.dumps(init_message(self.sim)).encode())
            server._handle_line(endpoint, json.dumps(self.state()).encode())
            payload = client.recv(4096)
            self.assertTrue(payload.endswith(b"\n"))
            action = json.loads(payload)
            self.assertTrue(self.sim.apply_action(action)["accepted"])
            self.sim.step(0.5, return_state=False)
            server._handle_line(endpoint, json.dumps(self.state()).encode())
            second = json.loads(client.recv(4096))
            self.assertEqual(second["action"], "build_tower")
            self.assertNotEqual(action["command_id"], second["command_id"])
            self.assertTrue(self.sim.apply_action(second)["accepted"])
        finally:
            endpoint.close()
            client.close()

    def test_tower_report_and_gif(self):
        episode = rollout(self.strategy, self.config, self.map_data, 10, duration=2)
        source = {"role": "tower_defense", "settings": {"duration": 2, "dt": 0.1, "test_seeds": [10]},
            "config": self.config, "map": self.map_data, "history": [],
            "comparison": {"GENETIC": {"mean_damage": 0, "std_damage": 0, "episodes": [episode]}}}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            report = build_report(source, self.strategy, output, make_gif=True)
            with Image.open(output / "replay.gif") as gif:
                self.assertEqual(gif.n_frames, report["gif"]["frames"])
                self.assertGreater(gif.n_frames, 1)
            text = (output / "report.md").read_text(encoding="utf-8")
            self.assertIn("AI broni bazy", text)
            self.assertIn("build_tower", text)
            self.assertTrue((output / "builds.csv").is_file())
            self.assertTrue((output / "timeline.png").is_file())

    def test_validation(self):
        for dt in (0, -1, float("nan"), 0.4):
            with self.assertRaises(ValueError):
                rollout(self.strategy, self.config, self.map_data, 1, dt=dt)
        with self.assertRaises(ValueError):
            Strategy(("BASIC",), (0, 0, 0))
        with self.assertRaises(ValueError):
            train(self.config, self.map_data, slots=0)


if __name__ == "__main__":
    unittest.main()
