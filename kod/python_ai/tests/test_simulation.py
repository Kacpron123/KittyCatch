import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.data import load_game_data
from src.simulation import Simulation
from src.visualization import render_state, write_state_to_file


class SimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config, self.map_data = load_game_data()
        self.simulation = Simulation(copy.deepcopy(self.config), self.map_data, seed=7)

    def test_map_is_converted_to_godot_x_major_coordinates(self) -> None:
        self.assertEqual((self.simulation.width, self.simulation.height), (20, 15))
        self.assertEqual(self.simulation.grid[1][7], 0)
        self.assertEqual(self.simulation.grid[10][6], 1)

    def test_wave_cost_and_energy_refund_follow_balance_config(self) -> None:
        self.assertTrue(self.simulation.launch_wave(["SCOUT", "TANK"], 0.3))
        self.assertEqual(self.simulation.energy, 31)
        enemy = self.simulation.spawn_enemy("SCOUT")
        self.simulation._damage_enemy(enemy, 100)
        self.assertEqual(self.simulation.energy, 35)
        self.assertEqual(self.simulation.ai_money, 154)
        self.assertEqual(self.simulation.metrics["kills_total"], 1)

    def test_tower_action_spends_funds_and_rejects_repeated_cell(self) -> None:
        self.assertTrue(self.simulation.build_tower(10, 6, "BASIC"))
        self.assertEqual(self.simulation.ai_money, 80)
        rejected = self.simulation.apply_action(
            {"action": "build_tower", "tower_type": "BASIC", "x": 10, "y": 6}
        )
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["reason"], "cell_not_buildable")
        self.assertEqual(self.simulation.ai_money, 80)

    def test_tower_combat_kills_units_and_awards_configured_money(self) -> None:
        self.assertTrue(self.simulation.build_tower(10, 6, "BASIC"))
        self.simulation.spawn_enemy("SCOUT")
        for _ in range(150):
            self.simulation.step(0.1)
            if self.simulation.metrics["kills_total"]:
                break
        self.assertEqual(self.simulation.metrics["kills_total"], 1)
        self.assertEqual(self.simulation.ai_money, 84)
        self.assertGreaterEqual(self.simulation.energy, 44)

    def test_base_leak_accelerates_enemies_with_configured_cap(self) -> None:
        enemy = self.simulation.spawn_enemy("SCOUT")
        self.simulation._leak(enemy)
        self.assertEqual(self.simulation.enemy_speed_multiplier, 1.005)
        for _ in range(30):
            self.simulation._leak(self.simulation.spawn_enemy("SCOUT"))
        self.assertAlmostEqual(self.simulation.enemy_speed_multiplier, 1.1)
        self.assertEqual(self.simulation.base_health, 169)

    def test_rebalanced_base_and_units_are_loaded_for_training(self) -> None:
        self.assertEqual(self.simulation.base_health, 200)
        self.assertEqual(self.simulation.base_max_health, 200)
        self.assertEqual(self.simulation.spawn_enemy("TANK").hp, 60)
        self.assertEqual(self.simulation.spawn_enemy("SPEED").base_speed, 1.4)

    def test_scaled_tower_reach_includes_enemy_collision_radius(self) -> None:
        sim = self.simulation
        self.assertTrue(sim.build_tower(10, 6, "BASIC"))
        self.assertAlmostEqual(sim.towers[0].range_cells, 1.6)
        enemy = sim.spawn_enemy("SCOUT")
        enemy.x, enemy.y = 12, 6
        sim._fire_towers(0.1)
        self.assertFalse(sim.projectiles)
        enemy.x = 11.8  # Center is outside 1.6; the 0.25-cell hit area overlaps.
        sim._fire_towers(0.1)
        self.assertEqual(len(sim.projectiles), 1)

    def test_tower_preserves_order_of_entering_its_range(self) -> None:
        sim = self.simulation
        sim.build_tower(10, 6)
        first_spawned = sim.spawn_enemy("TANK")
        first_spawned.x, first_spawned.y = 15, 6
        first_inside = sim.spawn_enemy("SCOUT")
        first_inside.x, first_inside.y = 10.5, 6
        sim._fire_towers(0.1)
        first_spawned.x = 10.4
        sim._fire_towers(1)
        self.assertIs(sim.projectiles[-1].target, first_inside)

    def test_enemy_spread_is_perpendicular_to_route_and_bounded(self) -> None:
        sim = self.simulation
        enemy = sim.spawn_enemy("SCOUT")
        self.assertLessEqual(abs(enemy.path_offset), 0.25)
        enemy.path_offset = 0.25
        sim._move_enemies(0.1)
        self.assertAlmostEqual(enemy.y, 7.25)

    def test_reaching_goal_refunds_half_cost_rounded_up_once(self) -> None:
        for unit_type, expected_refund in (("SCOUT", 2), ("TANK", 3), ("SPEED", 4)):
            with self.subTest(unit_type=unit_type):
                config = copy.deepcopy(self.config)
                config["economy"]["player"]["energy_regen_per_second"] = 0
                sim = Simulation(config, self.map_data)
                sim.energy = 0
                enemy = sim.spawn_enemy(unit_type)
                enemy.distance = sim.route_length - 0.001
                sim.step(0.1)
                self.assertEqual(sim.energy, expected_refund)
                self.assertEqual(sim.metrics["leaks_total"], 1)
                self.assertEqual(sim.base_health, sim.base_max_health - 1)
                event = next(e for e in sim.events if e["kind"] == "base_damaged")
                self.assertEqual(event["player_energy_refunded"], expected_refund)
                sim._leak(enemy)
                self.assertEqual(sim.energy, expected_refund)
                self.assertEqual(sim.metrics["leaks_total"], 1)

    def test_goal_refund_respects_player_energy_limit(self) -> None:
        sim = self.simulation
        sim.energy = sim.max_energy - 1
        sim._leak(sim.spawn_enemy("TANK"))
        self.assertEqual(sim.energy, sim.max_energy)

    def test_snapshot_matches_godot_observation_shape(self) -> None:
        snapshot = self.simulation.to_dict()
        self.assertEqual(snapshot["protocol_version"], 2)
        self.assertEqual(snapshot["map"]["orientation"], "x_major")
        self.assertIn("feature_vector", snapshot)
        self.assertEqual(len(snapshot["feature_vector"]), 11)
        self.assertIn("ai_money_earned_total", snapshot["resources"])

    def test_from_godot_init_uses_ordered_route_and_starting_resources(self) -> None:
        init_message = {
            "type": "init",
            "protocol_version": 2,
            "episode_id": "godot-episode",
            "grid_orientation": "x_major",
            "map_size": {"width": self.simulation.width, "height": self.simulation.height},
            "map_grid": self.simulation.grid,
            "map": {
                "buildable_grid": self.simulation.buildable_grid,
                "route_grid": self.simulation.route_grid,
                "route_points": self.map_data["path"],
            },
            "unit_types": self.config["units"],
            "tower_types": self.config["towers"],
            "economy": self.config["economy"],
            "combat": self.config["combat"],
            "ai_money": 220,
            "player": {"energy": 35, "max_energy": 90},
            "base": {"health": 800, "max_health": 1000},
        }
        live_simulation = Simulation.from_init(init_message, seed=3)
        self.assertEqual(live_simulation.episode_id, "godot-episode")
        self.assertEqual(live_simulation.route_points[0], (1.0, 7.0))
        self.assertEqual(live_simulation.ai_money, 220)
        self.assertEqual(live_simulation.energy, 35)
        self.assertEqual(live_simulation.base_health, 800)

    def test_visualization_accepts_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "nested" / "frame.png"
            state_path = Path(directory) / "nested" / "state.json"
            snapshot = self.simulation.to_dict()
            render_state(snapshot, image_path)
            write_state_to_file(snapshot, state_path)
            self.assertTrue(image_path.is_file())
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["type"],
                "update",
            )


if __name__ == "__main__":
    unittest.main()
