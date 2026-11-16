"""Collect full GA telemetry, random baselines and controlled operator ablations."""
import argparse
import hashlib
import json
import statistics
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path

from src.genetic_ai import Strategy, random_strategy, rollout, train


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def collect_main(source, folder):
    results = []
    config, map_data, settings = source["config"], source["map"], source["settings"]
    for expected in source["search_runs"]:
        seed = expected["seed"]
        cache_path = folder / f"run_{seed}.json"
        if cache_path.exists():
            saved = json.loads(cache_path.read_text(encoding="utf-8"))
            if saved["config_sha256"] == source["config_sha256"] and saved["strategy"] == expected["strategy"]:
                results.append(saved)
                print(f"Telemetry seed {seed}: using completed checkpoint", flush=True)
                continue
        records = []
        trace_path = folder / f"population_seed_{seed}.jsonl"
        if trace_path.exists():
            existing = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
            if (len(existing) == settings["generations"] and
                    existing[0].get("config_sha256") == source["config_sha256"] and
                    existing[-1]["best_genes"] == expected["strategy"]["genes"]):
                records = existing
        if records:
            best = Strategy(tuple(expected["strategy"]["tower_types"]),tuple(expected["strategy"]["genes"]),expected["strategy"]["duration"])
            history = [record["summary"] for record in records]
            print(f"Telemetry seed {seed}: reusing populations recorded during training", flush=True)
        else:
            with trace_path.open("w", encoding="utf-8") as stream:
                def capture(record):
                    stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                    stream.flush()
                    records.append(record)
                best, history = train(config, map_data, population_size=settings["population"],
                    generations=settings["generations"], slots=settings["slots"], duration=settings["duration"],
                    dt=settings["dt"], mutation_rate=settings["mutation_rate"], seeds=tuple(settings["train_seeds"]),
                    seed=seed, telemetry=capture,
                    progress=lambda row, s=seed: print(f"Telemetry {s}: epoch {row['generation']+1}/{settings['generations']} "
                        f"best={row['best']:.4f}, median={row['median']:.4f}, diversity={row['diversity']:.2f}", flush=True))
        if asdict(best) != {**expected["strategy"], "tower_types": tuple(expected["strategy"]["tower_types"]),
                            "genes": tuple(expected["strategy"]["genes"])}:
            raise RuntimeError("Instrumentation changed the saved run; production strategy was not replaced")
        test_cache, test_curve = {}, []
        for record in records:
            genes = tuple(record["best_genes"])
            if genes not in test_cache:
                policy = Strategy(best.tower_types, genes, best.duration)
                test_cache[genes] = [rollout(policy, config, map_data, s,
                    duration=settings["duration"], dt=settings["dt"]) for s in settings["test_seeds"]]
            episodes = test_cache[genes]
            test_curve.append({"generation": record["generation"], "training_fitness": record["summary"]["best"],
                "test_fitness": statistics.mean(e["fitness"] for e in episodes),
                "test_damage": statistics.mean(e["damage"] for e in episodes),
                "test_kills": statistics.mean(e["kills"] for e in episodes)})
        saved = {"seed": seed, "config_sha256": source["config_sha256"], "strategy": asdict(best),
            "history": history, "test_curve": test_curve, "telemetry": f"population_seed_{seed}.jsonl",
            "elapsed_seconds": records[-1]["elapsed_seconds"],
            "first_best_epoch": next(i for i, r in enumerate(history) if r["best"] == max(h["best"] for h in history))}
        write_json(cache_path, saved)
        results.append(saved)
    return results


def collect_random(source, folder, count):
    path = folder / "random_benchmark.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["config_sha256"] == source["config_sha256"] and saved["layout_count"] == count:
            return saved
    config, settings = source["config"], source["settings"]
    rows, policies = [], []
    for layout_seed in range(5000, 5000 + count):
        policy = random_strategy(config, source["map"], seed=layout_seed,
            slots=settings["slots"], duration=settings["duration"])
        policies.append({"layout_seed": layout_seed, "strategy": asdict(policy)})
        episodes = [{"layout_seed": layout_seed, **rollout(policy, config, source["map"], scenario,
            duration=settings["duration"], dt=settings["dt"])} for scenario in settings["test_seeds"]]
        rows.extend(episodes)
        print(f"Random layout {layout_seed}: mean damage={statistics.mean(e['damage'] for e in episodes):.2f}", flush=True)
    saved = {"config_sha256": source["config_sha256"], "layout_count": count, "strategies": policies,
        "mean_damage": statistics.mean(e["damage"] for e in rows),
        "std_damage": statistics.pstdev(e["damage"] for e in rows), "episodes": rows}
    write_json(path, saved)
    return saved


def collect_ablations(source, folder, executor=None):
    settings = source["settings"]
    groups = {"FULL": {}, "NO_MUTATION": {"mutation_rate": 0},
              "NO_CROSSOVER": {"crossover": False}, "NO_ELITISM": {"elite_count": 0}}
    results = []
    for name, options in groups.items():
        for seed in (42, 137, 2026):
            path = folder / f"ablation_{name}_{seed}.json"
            if path.exists():
                saved = json.loads(path.read_text(encoding="utf-8"))
                if saved["config_sha256"] == source["config_sha256"]:
                    results.append(saved)
                    continue
            parameters = {"population_size": 12, "generations": 12, "slots": settings["slots"],
                "duration": settings["duration"], "dt": settings["dt"], "seed": seed,
                "seeds": tuple(settings["train_seeds"]), "mutation_rate": settings["mutation_rate"], **options}
            best, history = train(source["config"], source["map"], **parameters, executor=executor,
                progress=lambda row, n=name, s=seed: print(f"Ablation {n}/{s}: epoch {row['generation']+1}/12 "
                    f"best={row['best']:.4f}", flush=True))
            episodes = [rollout(best, source["config"], source["map"], s,
                duration=settings["duration"], dt=settings["dt"]) for s in settings["test_seeds"]]
            saved = {"variant": name, "seed": seed, "config_sha256": source["config_sha256"],
                "parameters": parameters, "history": history, "strategy": asdict(best),
                "best_observed_fitness": max(r["best"] for r in history), "final_fitness": history[-1]["best"],
                "test_damage": statistics.mean(e["damage"] for e in episodes), "test_episodes": episodes}
            write_json(path, saved)
            results.append(saved)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.json"))
    parser.add_argument("--random-layouts", type=int, default=20)
    parser.add_argument("--phase", choices=("all", "main", "ablations", "random"), default="all")
    parser.add_argument("--workers", type=int, default=1, help="Parallel chromosome evaluation in ablations")
    args = parser.parse_args()
    if args.random_layouts < 2:
        parser.error("Use at least two random layouts")
    if args.workers < 1:
        parser.error("Workers must be positive")
    source = json.loads(args.input.read_text(encoding="utf-8"))
    folder = args.input.parent / "genetic_analysis"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "analysis.json"
    result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "config_sha256": source["config_sha256"], "production_strategy_sha256": fingerprint(source["strategy"])}
    if result["config_sha256"] != source["config_sha256"]:
        raise RuntimeError("Analysis folder belongs to a different balance configuration")
    if args.phase in ("all", "main"):
        result["runs"] = collect_main(source, folder)
        write_json(path, result)
    if args.phase in ("all", "random"):
        result["random"] = collect_random(source, folder, args.random_layouts)
        write_json(path, result)
    if args.phase in ("all", "ablations"):
        with ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else nullcontext() as executor:
            result["ablations"] = collect_ablations(source, folder, executor)
        write_json(path, result)
    source["genetic_analysis"] = {"path": "genetic_analysis/analysis.json", "telemetry_version": 1}
    if "random" in result:
        source["comparison"]["RANDOM"] = {key: result["random"][key] for key in ("mean_damage", "std_damage", "episodes")}
    write_json(args.input, source)
    print(f"Genetic analysis saved to {folder.resolve()}", flush=True)


if __name__ == "__main__":
    main()
