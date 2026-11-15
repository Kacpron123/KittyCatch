"""Evaluate saved layouts against precharged, dense waves at all energy limits."""
import argparse
import copy
import json
from pathlib import Path

from PIL import Image, ImageDraw

from src.experiment_report import csv_file
from src.genetic_ai import Strategy, baseline_strategies, rollout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.json"))
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    policies = {}
    for run in source["search_runs"]:
        data = run["strategy"]
        policies[f"GA_{run['seed']}"] = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
    policies["MIXED"] = baseline_strategies(source["config"], source["map"], source["settings"]["slots"], source["settings"]["duration"])["MIXED"]
    limits = source["config"]["difficulty"]["player_energy_limits"]
    rows = []
    for difficulty, capacity in limits.items():
        config = copy.deepcopy(source["config"])
        config["economy"]["player"]["max_energy"] = capacity
        config["economy"]["player"]["starting_energy"] = capacity
        for name, strategy in policies.items():
            for seed in range(200, 205):
                result = rollout(strategy, config, source["map"], seed, duration=source["settings"]["duration"],
                    dt=0.1, spawn_interval=0.1, attack_options={"wave_budget": capacity, "interval_scale": 0.5})
                rows.append({"strategy": name, "difficulty": difficulty, "capacity": capacity, **result})
            print(f"Stress {difficulty}/{name}: mean damage={sum(r['damage'] for r in rows[-5:])/5:.1f}", flush=True)
    output = args.input.parent
    report = {"description": "Precharged stress test; excluded from training and model selection",
        "config_sha256": source["config_sha256"],
        "starting_energy": "equal to difficulty capacity", "spawn_interval": 0.1,
        "wave_budget": "equal to difficulty capacity", "interval_scale": 0.5,
        "seeds": list(range(200, 205)), "duration": source["settings"]["duration"], "rows": rows}
    (output / "stress_test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    csv_file(output / "stress_test.csv", rows)
    image = Image.new("RGB", (1100, 180 + 85 * len(policies)), "#171923")
    draw = ImageDraw.Draw(image)
    draw.text((35, 22), "Stress: mean base damage, precharged dense waves", fill="white", font_size=24)
    for column, (difficulty, capacity) in enumerate(limits.items()):
        x = 260 + column * 270
        draw.text((x, 85), f"{difficulty} / {capacity} energy", fill="white", font_size=18)
        for i, name in enumerate(policies):
            y = 135 + i * 85
            values = [r["damage"] for r in rows if r["strategy"] == name and r["difficulty"] == difficulty]
            mean = sum(values) / len(values)
            maximum = config["base"]["health"]
            ratio = min(1, mean / maximum)
            color = (int(40 + 170*ratio), int(150 - 80*ratio), int(160 - 75*ratio))
            draw.rectangle((x, y, x+235, y+62), fill=color)
            draw.text((x+15, y+16), f"{mean:.1f} HP", fill="white", font_size=23)
            if column == 0:
                draw.text((35, y+20), name, fill="white", font_size=19)
    image.save(output / "stress_test.png")


if __name__ == "__main__":
    main()
