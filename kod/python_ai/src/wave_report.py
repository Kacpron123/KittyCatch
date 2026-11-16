"""Detailed experiment report and a rendered replay of a saved experiment."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw

from src.wave_ai import Strategy, rollout
from src.training_plots import COLORS, line_chart
from src.visualization import render_state_image


def table(headers, rows):
    return ["| " + " | ".join(map(str, headers)) + " |",
            "| " + " | ".join("---" for _ in headers) + " |"] + [
                "| " + " | ".join(map(str, row)) + " |" for row in rows] + [""]


def csv_file(path, rows):
    if rows:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def decode(strategy, config, duration):
    n = len(strategy.unit_types)
    maximum = config["economy"]["player"]["max_energy"]
    cheapest = min(config["units"][name]["energy_cost"] for name in strategy.unit_types)
    phases = []
    for i in range(2):
        genes = strategy.genes[i * (n + 3):(i + 1) * (n + 3)]
        total = sum(genes[:n])
        phases.append({"phase": i + 1, "start": i * duration / 2, "end": (i + 1) * duration / 2,
            "weights": dict(zip(strategy.unit_types, genes[:n])),
            "relative_weights": {name: genes[j] / total if total else 0 for j, name in enumerate(strategy.unit_types)},
            "energy_threshold": min(maximum, max(cheapest, round(genes[n] * maximum))),
            "spend_fraction": 0.15 + 0.85 * genes[n + 1], "cooldown_seconds": 12 * genes[n + 2]})
    return phases


def timeline(path, events, types, duration):
    image = Image.new("RGB", (1200, 350), "#171923")
    draw = ImageDraw.Draw(image)
    draw.text((35, 20), "Actual pigeon spawns over time", fill="white", font_size=24)
    for i in range(7):
        x = 140 + 1000 * i / 6
        draw.line((x, 70, x, 275), fill="#34394b")
        draw.text((x - 12, 285), f"{duration * i / 6:.0f}s", fill="white", font_size=16)
    middle = 640
    draw.line((middle, 60, middle, 275), fill="#ffdc85", width=2)
    draw.text((middle + 8, 60), "Phase 2", fill="#ffdc85", font_size=16)
    for i, name in enumerate(types):
        y = 110 + i * (140 / max(1, len(types) - 1))
        draw.text((25, y - 8), name, fill=COLORS[i % len(COLORS)], font_size=18)
        for event in events:
            if event["kind"] == "unit_spawned" and event["unit_type"] == name:
                x = 140 + 1000 * event["elapsed_seconds"] / duration
                draw.line((x, y - 14, x, y + 14), fill=COLORS[i % len(COLORS)], width=3)
    image.save(path)


def build_report(source: dict, strategy: Strategy, output: Path, *, make_gif=False, replay_seed=None):
    output.mkdir(parents=True, exist_ok=True)
    config, map_data, settings = source["config"], source["map"], source["settings"]
    duration, dt = settings["duration"], settings["dt"]
    seeds = settings["test_seeds"]
    # The displayed run is selected by seed, never by maximizing test damage.
    replay_seed = seeds[0] if replay_seed is None else replay_seed
    phases = decode(strategy, config, duration)
    frames = []
    frame_times = []

    def capture(state):
        frame = render_state_image(state)
        frame.thumbnail((1050, 680), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (frame.width, frame.height + 65), "#171923")
        canvas.paste(frame, (0, 0))
        draw = ImageDraw.Draw(canvas)
        phase = 1 if state["elapsed_seconds"] < duration / 2 else 2
        draw.text((12, frame.height + 8),
            f"Seed {replay_seed} | t={state['elapsed_seconds']:.1f}s | Phase {phase} | Playback 3x",
            fill="white", font_size=17)
        draw.text((12, frame.height + 34), "SCOUT: salmon   TANK: red   SPEED: orange   Blue/purple: towers",
                  fill="#c5cad6", font_size=15)
        frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
        frame_times.append(state["elapsed_seconds"])

    episodes = [rollout(strategy, config, map_data, seed, duration=duration, dt=dt, trace=True)
                for seed in seeds]
    replay = rollout(strategy, config, map_data, replay_seed, duration=duration, dt=dt, trace=True,
                     on_frame=capture if make_gif else None)
    if frames:
        delays = [max(20, round((b - a) / 3 * 1000 / 10) * 10)
                  for a, b in zip(frame_times, frame_times[1:])] + [1500]
        frames[0].save(output / "replay.gif", save_all=True, append_images=frames[1:],
                       duration=delays, loop=0, disposal=2, optimize=False)
    state = replay["final_state"]
    render_state_image(state).save(output / "final_state.png")
    csv_file(output / "replay.csv", replay["history"])
    for filename, title, keys in (
        ("combat.png", "Best strategy: combat", ("kills", "leaks", "alive", "towers")),
        ("resources.png", "Best strategy: resources", ("energy", "base_hp")),
    ):
        line_chart(output / filename, title, "Seconds", "Value",
            {key: [(r["time"], r[key]) for r in replay["history"]] for key in keys})
    names = strategy.unit_types
    wave_rows = []
    for i, wave in enumerate(replay["waves"], 1):
        counts = Counter(wave["unit_types"])
        wave_rows.append({"wave": i, "time": round(wave["time"], 4), "phase": wave["phase"],
            **{name: counts[name] for name in names}, "cost": wave["cost"],
            "energy_before": wave["energy_before"], "energy_after": wave["energy_after"],
            "spawn_order": ", ".join(wave["spawn_order"])})
    csv_file(output / "waves.csv", wave_rows)
    events = replay["events"]
    spawn_events = [e for e in events if e["kind"] == "unit_spawned"]
    csv_file(output / "spawns.csv", [{"time": round(e["elapsed_seconds"], 4),
        "unit_type": e["unit_type"], "event_id": e["event_id"]} for e in spawn_events])
    tower_rows = []
    for episode in episodes + ([] if replay_seed in seeds else [replay]):
        for e in episode["events"]:
            if e["kind"] == "action_result" and e["accepted"]:
                tower_rows.append({"seed": episode["seed"], "time": round(e["elapsed_seconds"], 4),
                    "type": e["tower_type"], "x": e["grid_x"], "y": e["grid_y"], "cost": e["cost"]})
    csv_file(output / "defense_builds.csv", tower_rows)
    timeline(output / "spawn_timeline.png", events, names, duration)
    cumulative = {name: [(0, 0)] for name in names}
    counts = Counter()
    for event in spawn_events:
        name = event["unit_type"]
        now = event["elapsed_seconds"]
        cumulative[name].append((now, counts[name]))
        counts[name] += 1
        cumulative[name].append((now, counts[name]))
    for name in names:
        cumulative[name].append((replay["elapsed"], counts[name]))
    line_chart(output / "unit_types.png", "Actual spawns by type (cumulative)", "Seconds", "Pigeons", cumulative)
    detail = {"strategy": asdict(strategy), "decoded_phases": phases, "settings": settings,
        "config": config, "map": map_data, "test_episodes": episodes, "replay": replay,
        "gif": {"file": "replay.gif", "frames": len(frames), "playback_speed": 3} if frames else None}
    (output / "detailed_report.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")

    lines = ["# Kompletny raport strategii wysyłania gołębi", "",
        "## Wynik i zakres eksperymentu", "",
        "Najlepsza strategia oznacza zwycięzcę przeprowadzonego treningu. "
        "Algorytm nie dowodzi globalnego optimum. Wyniki pochodzą z lokalnego symulatora, nie z uruchomienia Godota.", ""]
    comparisons = source["comparison"]
    lines += table(["Strategia", "Średnie obrażenia", "Odchylenie standardowe", "Min–maks"], [
        [name, f"{stats['mean_damage']:.2f}", f"{stats['std_damage']:.2f}",
         f"{min(e['damage'] for e in stats['episodes'])}–{max(e['damage'] for e in stats['episodes'])}"]
        for name, stats in comparisons.items()])
    lines += ["![Porównanie strategii](comparison.png)", "", "## Parametry treningu", ""]
    lines += table(["Parametr", "Wartość"], [[key, settings.get(key, "brak danych")]
        for key in ("population", "generations", "duration", "dt", "seed", "mutation_rate", "train_seeds", "test_seeds")])
    lines += ["Selekcja: turniej 3 osobników. Krzyżowanie: niezależny wybór genu jednego z rodziców (50/50). "
        "Mutacja: szum Gaussa σ=0,2, ograniczenie do [0,1]. Elitaryzm: max(1, populacja // 8). "
        "Osobniki oceniane są na tych samych ziarnach treningowych; wyniki testowe nie wybierają chromosomu.", "",
        "Fitness = obrażenia bazy + 0,5 × (1 − czas / limit), wyłącznie gdy baza zostanie zniszczona. "
        "W pozostałych przypadkach fitness to same obrażenia. Maksymalizowana jest średnia po scenariuszach treningowych. "
        "Gołębie w kolejce i na trasie po limicie nie otrzymują punktów.", ""]
    if source.get("history"):
        lines += [f"Najlepszy fitness treningowy: {source['history'][0]['best']:.2f} → "
                  f"{source['history'][-1]['best']:.2f}.", "", "![Ewolucja](evolution.png)", "",
                  "![Różnorodność](diversity.png)", ""]
    lines += ["## Chromosom zwycięzcy", "", "```json", json.dumps(asdict(strategy), indent=2), "```", "",
        f"Chromosom ma {len(strategy.genes)} genów. Kolejność w każdej fazie: "
        f"wagi {', '.join(names)}, próg energii, ułamek wydatku, odstęp między startami fal. "
        "Wszystkie geny należą do [0,1]. Faza 2 zaczyna się w połowie limitu czasu; "
        "nie przerywa już rozpoczętej fali.", ""]
    lines += table(["Gen (indeks od 0)", "Znaczenie", "Faza 1", "Faza 2"], [
        [f"{i} / {i + len(names) + 3}", label, f"{strategy.genes[i]:.9f}",
         f"{strategy.genes[i + len(names) + 3]:.9f}"]
        for i, label in enumerate(list(names) + ["Próg energii", "Wydatek", "Odstęp"])])
    lines += table(["Faza", "Czas [s]", "Wagi typów", "Próg energii", "Wydatek energii", "Odstęp [s]"], [
        [p["phase"], f"{p['start']:g}–{p['end']:g}",
         ", ".join(f"{k}: {v:.4f}" for k, v in p["weights"].items()), p["energy_threshold"],
         f"{100 * p['spend_fraction']:.2f}%", f"{p['cooldown_seconds']:.4f}"] for p in phases])
    lines += ["Próg = min(maksimum energii, max(koszt najtańszego typu, round(gen × maksimum))). "
        "Budżet = min(energia, max(koszt najtańszego typu, int(energia × (0,15 + 0,85 × gen)))). "
        "Odstęp = 12 × gen sekund od poprzedniego startu. Dodatkowo trzeba poczekać na opróżnienie kolejki.", "",
        "Wagi nie są gwarantowanymi procentami składu. Kolejna jednostka maksymalizuje "
        "waga / (liczba już wybranych + 1) spośród typów mieszczących się w pozostałym budżecie. "
        "Waga zero wyklucza typ. Mała dodatnia waga może nie dać żadnej jednostki przy małych falach. "
        "Kolejność wybranych jednostek jest następnie tasowana.", "",
        "## Ustawienia jednostek, obrony i ekonomii", ""]
    lines += table(["Typ gołębia", "HP", "Szybkość [kafle/s]", "Koszt energii", "Nagroda obrony"], [
        [name, u["hp"], u["speed"], u["energy_cost"], u["ai_reward"]] for name, u in config["units"].items()])
    lines += table(["Wieża", "Koszt", "Zasięg [kafle]", "Obrażenia", "Ataki/s"], [
        [name, t["cost"], t["range"], t["damage"], t["attack_speed"]] for name, t in config["towers"].items()])
    lines += ["Pełna konfiguracja użyta w eksperymencie:", "", "```json",
        json.dumps({k: config[k] for k in ("economy", "combat", "base", "map") if k in config}, indent=2), "```", "",
        f"Zdrowie startowe bazy: {config.get('base', {}).get('health', 1000)}. "
        "Każdy gołąb docierający do bazy zabiera 1 HP, niezależnie od typu. "
        "Wysyłanie jednostek: co 0,3 s, z kwantyzacją do kroku symulacji. "
        "Przy domyślnym dt=0,2 s rzeczywiste odstępy mogą wynosić 0,2 lub 0,4 s.", "",
        "Obrońca sortuje pola budowy według odległości od trasy (41 próbek) plus "
        "losowy składnik jednostajny 0–2,5 komórki. Typy wież tasuje raz na scenariusz, "
        "potem buduje cyklicznie. Stawia wieże od razu i kontroluje środki co około 1 s; "
        "reinwestuje nagrody za zabicia. Jeśli nie stać go na następny typ, czeka. "
        "Ziarno określa rozmieszczenie, kolejność typów wież i tasowanie fal. "
        "Wspólne ziarno nie gwarantuje identycznych późniejszych wież, bo strategie dają różne nagrody za zabicia.", "",
        "## Wyniki każdego scenariusza testowego", ""]
    lines += table(["Seed", "Obrażenia", "Zabite", "Zamówione", "Energia wydana", "Obrażenia/energia", "Wieże", "Kolejność wież"], [
        [e["seed"], e["damage"], e["kills"], e["sent"], e["energy_spent"], f"{e['damage_per_energy']:.4f}",
         len(e["final_state"]["towers"]), " → ".join(e["defense_type_order"])] for e in episodes])
    lines += ["## Jedna pełna rozgrywka", "",
        f"Pokazany seed: **{replay_seed}**, wskazany jawnie lub pierwszy z listy testowej. "
        "Nie wybieramy do animacji najlepszego wyniku testowego. "
        f"Czas: {replay['elapsed']:.1f} s; obrażenia: {replay['damage']}; zabicia: {replay['kills']}; "
        f"HP bazy na końcu: {state['base']['health']}.", ""]
    if frames:
        lines += ["![Rozgrywka najlepszej strategii](replay.gif)", "",
            f"Animacja: {len(frames)} klatek, próbki co około 0,5 s czasu symulacji, odtwarzanie 3× "
            "(poza pauzą na końcu). Końcowa klatka odpowiada dokładnie końcowemu stanowi symulacji.", ""]
    lines += ["### Typy gołębi w kolejnych fazach", ""]
    phase_rows = []
    for p in phases:
        selected = Counter(t for w in replay["waves"] if w["phase"] == p["phase"] for t in w["unit_types"])
        spawned = Counter(e["unit_type"] for e in spawn_events if
            (1 if e["elapsed_seconds"] < duration / 2 else 2) == p["phase"])
        for name in names:
            phase_rows.append([p["phase"], name, selected[name], spawned[name]])
    lines += table(["Faza", "Typ", "Zamówione na starcie fal", "Faktycznie wysłane w tej fazie"], phase_rows)
    lines += ["Faza zamówienia może różnić się od fazy faktycznego wysłania, jeśli kolejka przekracza granicę faz. "
        "Niewykorzystane typy pozostają jawnie pokazane z wartością zero.", "",
        "![Momenty wysłania](spawn_timeline.png)", "", "![Liczba jednostek według typu](unit_types.png)", "",
        "### Bilans jednostek po zakończeniu", ""]
    selected = Counter(t for w in replay["waves"] for t in w["unit_types"])
    alive = Counter(u["type"] for u in state["units"])
    queued = Counter(state["wave"]["queued_units"])
    lines += table(["Typ", "Zamówione", "Wysłane", "Zabite", "Dotarły do bazy", "Na trasie", "W kolejce"], [
        [name, selected[name], counts[name], state["metrics"]["kills_by_type"][name],
         state["metrics"]["leaks_by_type"][name], alive[name], queued[name]] for name in names])
    lines += ["### Harmonogram wszystkich fal", ""]
    lines += table(["Fala", "Start [s]", "Faza", *names, "Koszt", "Energia przed → po"], [
        [w["wave"], f"{w['time']:.1f}", w["phase"], *[w[n] for n in names], w["cost"],
         f"{w['energy_before']} → {w['energy_after']}"] for w in wave_rows])
    lines += ["Dokładna kolejność jednostek po tasowaniu: [waves.csv](waves.csv). "
        "Rzeczywisty czas pojawienia się każdego gołębia: [spawns.csv](spawns.csv).", "",
        "### Wszystkie budowy wież w pokazanej rozgrywce", ""]
    lines += table(["Czas [s]", "Typ", "x", "y", "Koszt"], [
        [f"{r['time']:.1f}", r["type"], r["x"], r["y"], r["cost"]]
        for r in tower_rows if r["seed"] == replay_seed])
    lines += ["Współrzędne komórek od zera; siatka x-major. "
        "[Budowy wież we wszystkich scenariuszach](defense_builds.csv).", "",
        "![Walka](combat.png)", "", "![Zasoby](resources.png)", "", "![Stan końcowy](final_state.png)", "",
        "## Pliki i odtwarzalność", "",
        "- [Chromosom](best_strategy.json)",
        "- [Pełne dane raportu, fazy, zdarzenia, obrona i przebiegi testowe](detailed_report.json)",
        "- [Oryginalne dane eksperymentu](report.json)",
        "- [Dane treningu](generations.csv), [porównanie](comparison.csv), [przebieg](replay.csv)", "",
        "Ponowne wygenerowanie raportu i GIF-a z zapisanej konfiguracji eksperymentu:", "", "```powershell",
        f"python -m src.experiment_report --input {output.as_posix()}/report.json --gif --replay-seed {replay_seed}",
        "```", "",
        "Ograniczenia: jedna mapa, jeden model obrońcy, skończona liczba ziaren, "
        "dwie fazy strategii oraz przybliżona fizyka i czas walki. "
        "Brak punktów za gołębie nadal na trasie oznacza, że wynik zależy od limitu czasu. "
        "Nie przeprowadzono oceny przeciwko wszystkim możliwym ustawieniom przeciwnika.", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return detail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.json"))
    parser.add_argument("--gif", action="store_true")
    parser.add_argument("--replay-seed", type=int)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    strategy = (Strategy(tuple(source["strategy"]["unit_types"]), tuple(source["strategy"]["genes"]))
                if "strategy" in source else Strategy.load(args.input.parent / "best_strategy.json"))
    detail = build_report(source, strategy, args.input.parent, make_gif=args.gif, replay_seed=args.replay_seed)
    print(f"Report: {args.input.parent / 'report.md'}; replay damage: {detail['replay']['damage']}")
    if detail["gif"]:
        print(f"GIF: {args.input.parent / 'replay.gif'} ({detail['gif']['frames']} frames)")


if __name__ == "__main__":
    main()
