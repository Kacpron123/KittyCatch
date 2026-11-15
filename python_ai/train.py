"""Optimize AI tower placements; attackers are fixed scenario policies."""
import argparse
import json
import statistics
import hashlib
from dataclasses import asdict
from pathlib import Path

from src.data import load_game_data
from src.genetic_ai import Strategy, baseline_strategies, rollout, train
from src.experiment_report import build_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=int, default=32)
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("--slots", type=int, default=10)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--search-seeds", type=int, nargs="+", help="Independent genetic runs; choose the winner using training fitness")
    parser.add_argument("--previous-report", type=Path, help="Compare saved balance and reevaluate its strategy under current rules")
    parser.add_argument("--train-seeds", type=int, nargs="+", default=[10, 11, 12, 13, 14])
    parser.add_argument("--test-seeds", type=int, nargs="+", default=list(range(100, 110)))
    parser.add_argument("--mutation-rate", type=float, default=0.15)
    parser.add_argument("--output", type=Path, default=Path("training_results"))
    parser.add_argument("--strategy", type=Path, help="Evaluate a saved tower strategy")
    parser.add_argument("--gif", action="store_true")
    parser.add_argument("--pdf", action="store_true", help="Export PDF (requires reportlab)")
    args = parser.parse_args()
    if set(args.train_seeds) & set(args.test_seeds):
        parser.error("Training and test seeds must be disjoint")
    if args.pdf:
        try:
            from src.pdf_report import export_pdf
        except ImportError:
            parser.error("PDF export requires reportlab: python -m pip install reportlab")
    config, map_data = load_game_data()
    settings = {"duration": args.duration, "dt": args.dt}
    search_runs = []
    previous = json.loads(args.previous_report.read_text(encoding="utf-8")) if args.previous_report else None
    try:
        if args.strategy:
            best, history = Strategy.load(args.strategy), []
            if best.duration != args.duration:
                parser.error("--duration must match the saved strategy duration")
        else:
            for search_seed in dict.fromkeys(args.search_seeds or [args.seed]):
                candidate, candidate_history = train(config, map_data, population_size=args.population,
                    generations=args.generations, seeds=tuple(args.train_seeds), seed=search_seed,
                    slots=args.slots, mutation_rate=args.mutation_rate, **settings,
                    progress=lambda row, run_seed=search_seed: print(f"Run {run_seed} | generation {row['generation'] + 1}/{args.generations}: "
                        f"best={row['best']:.4f}, mean={row['mean']:.4f}", flush=True))
                search_runs.append({"seed": search_seed, "strategy": asdict(candidate),
                    "history": candidate_history, "training_fitness": candidate_history[-1]["best"]})
                # Save every completed run so a long experiment remains reviewable.
                args.output.mkdir(parents=True, exist_ok=True)
                candidate.save(args.output / f"strategy_seed_{search_seed}.json")
                (args.output / "search_runs.json").write_text(json.dumps(search_runs, indent=2), encoding="utf-8")
            winner = max(search_runs, key=lambda run: run["training_fitness"])
            data = winner["strategy"]
            best = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
            history = winner["history"]
            args.seed = winner["seed"]
        comparisons = {}
        policies = {"GENETIC": best, **baseline_strategies(config, map_data, len(best.genes) // 4, args.duration),
                    "NO_DEFENSE": None}
        for run in search_runs:
            data = run["strategy"]
            if run["seed"] != args.seed:
                policies[f"GA_{run['seed']}"] = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
        if previous and previous.get("role") == "tower_defense":
            data = previous["strategy"]
            policies["PREVIOUS"] = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
        for name, policy in policies.items():
            episodes = [rollout(policy, config, map_data, seed, **settings) for seed in args.test_seeds]
            comparisons[name] = {"mean_damage": statistics.mean(e["damage"] for e in episodes),
                "std_damage": statistics.pstdev(e["damage"] for e in episodes), "episodes": episodes}
            print(f"{name}: damage received = {comparisons[name]['mean_damage']:.2f}", flush=True)
        training_scores = [rollout(best, config, map_data, seed, **settings) for seed in args.train_seeds] if history else []
    except ValueError as error:
        parser.error(str(error))
    args.output.mkdir(parents=True, exist_ok=True)
    best.save(args.output / "best_strategy.json")
    report = {"role": "tower_defense", "strategy": asdict(best), "config": config, "map": map_data,
        "settings": {**{k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                     "slots": len(best.genes) // 4},
        "history": history, "comparison": comparisons, "training_scores": training_scores,
        "search_runs": search_runs, "previous_config": previous.get("config") if previous else None,
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "objective": "Minimize base damage received; kill fraction breaks ties. AI only builds towers."}
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    build_report(report, best, args.output, make_gif=args.gif)
    if args.pdf:
        export_pdf(args.output / "report.md", args.output / "report.pdf")
    print(f"Tower-defense experiment saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
