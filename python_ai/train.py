"""Train, evaluate and replay pigeon strategies: python train.py --help."""
import argparse
import csv
import json
import statistics
from pathlib import Path

from src.data import load_game_data
from src.genetic_ai import Strategy, baseline_strategies, rollout, train
from src.training_plots import comparison_chart, line_chart
from src.visualization import render_state


def write_csv(path: Path, rows: list[dict]) -> None:
    if rows:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genetic optimization of pigeon waves")
    parser.add_argument("--population", type=int, default=24)
    parser.add_argument("--generations", type=int, default=20)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--dt", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-seeds", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--test-seeds", type=int, nargs="+", default=[101, 202, 303, 404, 505])
    parser.add_argument("--mutation-rate", type=float, default=0.15)
    parser.add_argument("--output", type=Path, default=Path("training_results"))
    parser.add_argument("--strategy", type=Path, help="Evaluate saved strategy instead of training")
    args = parser.parse_args()
    if set(args.train_seeds) & set(args.test_seeds):
        parser.error("Training and test seeds must be disjoint")
    config, map_data = load_game_data()
    args.output.mkdir(parents=True, exist_ok=True)
    settings = {"duration": args.duration, "dt": args.dt}
    try:
        if args.strategy:
            best, history = Strategy.load(args.strategy), []
        else:
            best, history = train(config, map_data, population_size=args.population,
                generations=args.generations, seeds=tuple(args.train_seeds), seed=args.seed,
                mutation_rate=args.mutation_rate, **settings,
                progress=lambda row: print(f"Generation {row['generation'] + 1}/{args.generations}: "
                    f"best={row['best']:.2f}, mean={row['mean']:.2f}", flush=True))
        best.save(args.output / "best_strategy.json")
        comparisons = {}
        for name, policy in {"GENETIC": best, **baseline_strategies(tuple(config["units"]))}.items():
            episodes = [rollout(policy, config, map_data, seed, **settings) for seed in args.test_seeds]
            comparisons[name] = {"mean_damage": statistics.mean(r["damage"] for r in episodes),
                "std_damage": statistics.pstdev(r["damage"] for r in episodes), "episodes": episodes}
        replay = rollout(best, config, map_data, args.test_seeds[0], trace=True, **settings)
    except ValueError as error:
        parser.error(str(error))
    report = {"settings": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "config": config, "map": map_data, "history": history, "comparison": comparisons,
        "replay": replay,
        "objective": "Mean base damage; early destruction breaks ties. No global optimum guarantee."}
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(args.output / "generations.csv", history)
    write_csv(args.output / "replay.csv", replay["history"])
    write_csv(args.output / "comparison.csv", [{"strategy": name, **episode}
        for name, stats in comparisons.items() for episode in stats["episodes"]])
    if history:
        line_chart(args.output / "evolution.png", "Genetic training: fitness", "Generation", "Fitness",
            {label: [(r["generation"], r[key]) for r in history]
             for label, key in (("Best", "best"), ("Mean", "mean"), ("Worst", "worst"))})
        line_chart(args.output / "diversity.png", "Population diversity", "Generation", "Unique fraction",
            {"Diversity": [(r["generation"], r["diversity"]) for r in history]})
    comparison_chart(args.output / "comparison.png", comparisons)
    for filename, title, keys in (
        ("combat.png", "Best strategy: combat", ("kills", "leaks", "alive", "towers")),
        ("resources.png", "Best strategy: resources", ("energy", "base_hp")),
    ):
        line_chart(args.output / filename, title, "Seconds", "Value",
            {key: [(r["time"], r[key]) for r in replay["history"]] for key in keys})
    render_state(replay["final_state"], args.output / "final_state.png")
    lines = ["# Wyniki optymalizacji fal golebi", "",
        "Cel: maksymalizacja srednich obrazen bazy w zadanym czasie.",
        "Wynik dotyczy lokalnego modelu i testowanego przeciwnika; nie gwarantuje globalnego optimum.", "",
        "| Strategia | Srednie obrazenia na testach | Odchylenie standardowe |",
        "|---|---:|---:|"]
    for name, stats in comparisons.items():
        lines.append(f"| {name} | {stats['mean_damage']:.2f} | {stats['std_damage']:.2f} |")
        print(f"{name}: holdout damage = {stats['mean_damage']:.2f} +/- {stats['std_damage']:.2f}")
    lines += ["", "![Porownanie](comparison.png)", "![Walka](combat.png)",
        "![Zasoby](resources.png)"]
    if history:
        lines += ["![Ewolucja](evolution.png)", "![Roznorodnosc](diversity.png)"]
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved strategy, reports, CSV and charts to {args.output.resolve()}")


if __name__ == "__main__":
    main()
