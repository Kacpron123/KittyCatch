"""Run real headless Godot matches against the saved AI on a private TCP port."""
import argparse
import json
import logging
import random
import subprocess
import threading
import time
import hashlib
from pathlib import Path

from src.genetic_ai import GeneticAgent, Strategy, attack_schedule, rollout
from src.serwer import GameServer
from src.visualization import render_state_image
from PIL import Image, ImageDraw


def validate(executable: Path, source_path: Path, seeds: list[int], speed: float = 4, capture_seed: int | None = None):
    source = json.loads(source_path.read_text(encoding="utf-8"))
    data, config, map_data = source["strategy"], source["config"], source["map"]
    strategy = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
    fingerprint = source.get("config_sha256", "unknown")
    output = source_path.parent / f"godot_validation_{speed:g}x_{fingerprint[:8]}"
    output.mkdir(parents=True, exist_ok=True)
    project = Path(__file__).resolve().parents[1] / "godot_game"
    summary_path = source_path.parent / f"godot_validation_{speed:g}x_{fingerprint[:8]}.json"
    strategy_fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    previous = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    results = previous.get("scenarios", []) if previous.get("strategy_sha256") == strategy_fingerprint else []
    for scenario in seeds:
        profile, schedule = attack_schedule(config, scenario, source["settings"]["duration"])
        rng = random.Random(scenario)
        for wave in schedule:
            wave["spawn_order"] = list(wave["unit_types"])
            rng.shuffle(wave["spawn_order"])
        case_input, case_output = output / f"input_{scenario}.json", output / f"result_{scenario}.json"
        case_input.write_text(json.dumps({"seed": scenario, "duration": source["settings"]["duration"],
            "schedule": schedule}), encoding="utf-8")
        agent, actions, history, events, seen = GeneticAgent(strategy), [], [], [], set()
        snapshots = []

        def policy(message):
            if message.get("type") == "update":
                if scenario == capture_seed and (not snapshots or
                        message.get("elapsed_seconds", 0) - snapshots[-1].get("elapsed_seconds", 0) >= 0.49):
                    snapshots.append(message)
                history.append({"time": message.get("elapsed_seconds", 0), "step": message["step"],
                    "base_hp": message["base"]["health"], "kills": message["metrics"]["kills_total"],
                    "leaks": message["metrics"]["leaks_total"], "towers": len(message["towers"])})
                for event in message.get("events", []):
                    if event["event_id"] not in seen:
                        seen.add(event["event_id"])
                        events.append(event)
            action = agent(message)
            if action:
                actions.append({"time": message.get("elapsed_seconds", 0), **action})
            return action

        server = GameServer(port=0, policy=policy)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        deadline = time.monotonic() + 5
        while server._listener is None or server._listener.getsockname()[1] == 0:
            if time.monotonic() > deadline:
                raise RuntimeError("Private validation server did not start")
            time.sleep(0.01)
        port = server._listener.getsockname()[1]
        command = [str(executable), "--headless", "--path", str(project), "res://tools/ValidateDefense.tscn",
            "--log-file", str((output / f"engine_{scenario}.log").resolve()), "--", "--input", str(case_input.resolve()),
            "--output", str(case_output.resolve()), "--port", str(port), "--speed", str(speed)]
        try:
            with (output / f"process_{scenario}.log").open("w", encoding="utf-8") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                try:
                    code = process.wait(timeout=source["settings"]["duration"] / speed + 40)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise RuntimeError(f"Godot scenario {scenario} timed out; see {log.name}")
            if code or not case_output.exists():
                raise RuntimeError(f"Godot scenario {scenario} failed; see process_{scenario}.log")
        finally:
            server.stop()
            thread.join(timeout=2)
        actual = json.loads(case_output.read_text(encoding="utf-8"))
        state = actual["final_state"]
        local = rollout(strategy, config, map_data, scenario, duration=source["settings"]["duration"],
                        dt=source["settings"]["dt"])
        row = {"seed": scenario, "profile": profile, "godot_damage": state["metrics"]["base_damage_total"],
            "local_damage": local["damage"], "godot_kills": state["metrics"]["kills_total"],
            "local_kills": local["kills"], "godot_base_hp": state["base"]["health"],
            "godot_towers": len(state["towers"]), "accepted": state["metrics"]["ai_actions_accepted"],
            "rejected": state["metrics"]["ai_actions_rejected"], "actions": actions, "events": events,
            "history": history, "actual": actual, "private_port": port}
        if scenario == capture_seed:
            snapshots.append(state)
            frames, times = [], []
            for snapshot in snapshots:
                image = render_state_image(snapshot)
                canvas = Image.new("RGB", (image.width, image.height + 40), "#171923")
                canvas.paste(image, (0, 40))
                draw = ImageDraw.Draw(canvas)
                draw.text((12, 10), f"ACTUAL GODOT OBSERVATIONS | seed {scenario} | "
                    f"{snapshot.get('elapsed_seconds', 0):.1f}s | playback 3x", fill="white", font_size=18)
                frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
                times.append(snapshot.get("elapsed_seconds", 0))
            filename = f"godot_replay_{scenario}_{fingerprint[:8]}.gif"
            delays = [max(20, round((b-a) / 3 * 100) * 10) for a, b in zip(times, times[1:])] + [1500]
            frames[0].save(source_path.parent / filename, save_all=True, append_images=frames[1:],
                duration=delays, loop=0, disposal=2, optimize=False)
            row["animation"] = filename
            row["frame_count"] = len(frames)
        results = sorted([case for case in results if case["seed"] != scenario] + [row], key=lambda case: case["seed"])
        summary_path.write_text(json.dumps({
            "engine": str(executable), "time_scale": speed, "config_sha256": fingerprint,
            "strategy_sha256": strategy_fingerprint,
            "scenarios": results}, indent=2), encoding="utf-8")
        print(f"Godot seed {scenario} ({profile}): HP={row['godot_base_hp']}, damage={row['godot_damage']}, "
              f"kills={row['godot_kills']}, accepted={row['accepted']}, rejected={row['rejected']}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.json"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[100, 101, 102, 103, 104])
    parser.add_argument("--speed", type=float, default=4)
    parser.add_argument("--capture-seed", type=int, help="Render actual observations from this scenario as a GIF")
    args = parser.parse_args()
    if not 0 < args.speed <= 4:
        parser.error("--speed must be in (0, 4]")
    logging.basicConfig(level=logging.WARNING)
    validate(args.godot, args.input, args.seeds, args.speed, args.capture_seed)


if __name__ == "__main__":
    main()
