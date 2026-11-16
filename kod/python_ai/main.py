import argparse
from pathlib import Path

from src.data import load_game_data
from src.simulation import Simulation
from src.visualization import render_state, write_state_to_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the KittyCatch training simulation")
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--output", type=Path, default=Path("frames"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    config, map_data = load_game_data()
    sim = Simulation(config, map_data)

    sim.build_tower(10, 6, "BASIC")
    if not sim.launch_wave(["SCOUT", "SCOUT", "TANK", "SPEED"], spawn_interval=0.3):
        raise RuntimeError("Demo wave could not be launched; check configured energy costs")

    for index in range(args.steps):
        sim.step(dt=0.1)
        if index % 5 == 0 or sim.episode_done:
            render_state(sim, args.output / f"frame_{index:05d}.png")
            write_state_to_file(sim, args.output / f"state_{index:05d}.json")
        if sim.episode_done:
            break

    print(
        f"Simulation finished at {sim.sim_time:.1f}s: "
        f"AI funds={sim.ai_money}, base HP={sim.base_health}, "
        f"kills={sim.metrics['kills_total']}, leaks={sim.metrics['leaks_total']}. "
        f"Frames saved to {args.output}."
    )


if __name__ == "__main__":
    main()
