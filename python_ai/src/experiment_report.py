"""Detailed report for tower-defense AI, including local replay and TCP usage."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw

from src.genetic_ai import Strategy, rollout
from src.training_plots import COLORS, comparison_chart, line_chart
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


def event_timeline(path, builds, events, duration):
    labels = ["BASIC", "SNIPER", "SCOUT", "TANK", "SPEED"]
    image = Image.new("RGB", (1200, 470), "#171923")
    draw = ImageDraw.Draw(image)
    draw.text((30, 20), "AI tower builds and opponent pigeon spawns", fill="white", font_size=24)
    for i in range(7):
        x = 140 + 1000 * i / 6
        draw.line((x, 70, x, 400), fill="#34394b")
        draw.text((x - 15, 420), f"{duration * i / 6:.0f}s", fill="white", font_size=16)
    for i, name in enumerate(labels):
        y = 110 + i * 65
        color = COLORS[i % len(COLORS)]
        draw.text((25, y - 8), name, fill=color, font_size=18)
        times = [r["time"] for r in builds if r["type"] == name]
        times += [e["elapsed_seconds"] for e in events if e["kind"] == "unit_spawned" and e["unit_type"] == name]
        for time in times:
            x = 140 + 1000 * time / duration
            draw.line((x, y - 14, x, y + 14), fill=color, width=3)
    image.save(path)


def build_report(source: dict, strategy: Strategy, output: Path, *, make_gif=False, replay_seed=None):
    if source.get("role") != "tower_defense":
        raise ValueError("Expected a tower-defense report; old wave experiments are archived separately")
    output.mkdir(parents=True, exist_ok=True)
    config, map_data, settings = source["config"], source["map"], source["settings"]
    duration, dt = settings["duration"], settings["dt"]
    seeds = settings["test_seeds"]
    replay_seed = seeds[0] if replay_seed is None else replay_seed
    frames, frame_times = [], []

    def capture(state):
        frame = render_state_image(state)
        frame.thumbnail((1050, 680), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (frame.width, frame.height + 65), "#171923")
        canvas.paste(frame, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, frame.height + 8),
            f"AI BUILDS TOWERS | Seed {replay_seed} | t={state['elapsed_seconds']:.1f}s | Playback 3x",
            fill="white", font_size=17)
        draw.text((12, frame.height + 34), "Blue: BASIC | Purple: SNIPER | Pigeons are the opponent",
                  fill="#c5cad6", font_size=15)
        frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
        frame_times.append(state["elapsed_seconds"])

    episodes = [rollout(strategy, config, map_data, seed, duration=duration, dt=dt, trace=True) for seed in seeds]
    replay = rollout(strategy, config, map_data, replay_seed, duration=duration, dt=dt, trace=True,
                     on_frame=capture if make_gif else None)
    if frames:
        delays = [max(20, round((b - a) / 3 * 100) * 10) for a, b in zip(frame_times, frame_times[1:])] + [1500]
        frames[0].save(output / "replay.gif", save_all=True, append_images=frames[1:], duration=delays,
                       loop=0, disposal=2, optimize=False)
    state = replay["final_state"]
    plans = strategy.decode(state["map"]["width"], state["map"]["height"])
    tower_rows = []
    for episode in episodes + ([] if replay_seed in seeds else [replay]):
        for event in episode["events"]:
            if event["kind"] == "action_result" and event["accepted"]:
                tower_rows.append({"seed": episode["seed"], "time": round(event["elapsed_seconds"], 4),
                    "slot": int(event["command_id"].rsplit("-s", 1)[1]), "type": event["tower_type"],
                    "x": event["grid_x"], "y": event["grid_y"], "cost": event["cost"],
                    "command_id": event["command_id"]})
    builds = [r for r in tower_rows if r["seed"] == replay_seed]
    names = tuple(config["units"])
    wave_rows = []
    for i, wave in enumerate(replay["waves"], 1):
        counts = Counter(wave["unit_types"])
        wave_rows.append({"wave": i, "scheduled_time": round(wave["scheduled_time"], 4),
            "actual_time": round(wave["time"], 4), **{n: counts[n] for n in names},
            "energy_cost": wave["cost"], "spawn_order": ", ".join(wave["spawn_order"])})
    csv_file(output / "builds.csv", tower_rows)
    csv_file(output / "waves.csv", wave_rows)
    csv_file(output / "replay.csv", replay["history"])
    csv_file(output / "generations.csv", source["history"])
    csv_file(output / "comparison.csv", [{"strategy": name, **episode}
        for name, stats in source["comparison"].items() for episode in stats["episodes"]])
    spawns = [e for e in replay["events"] if e["kind"] == "unit_spawned"]
    csv_file(output / "spawns.csv", [{"time": e["elapsed_seconds"], "type": e["unit_type"]} for e in spawns])
    render_state_image(state).save(output / "final_state.png")
    event_timeline(output / "timeline.png", builds, replay["events"], duration)
    comparison_chart(output / "comparison.png", source["comparison"], defense=True)
    for filename, title, keys in (
        ("combat.png", "Defense: kills, leaks, units and towers", ("kills", "leaks", "alive", "towers")),
        ("resources.png", "AI funds and opponent energy", ("ai_money", "energy")),
        ("base_health.png", "Defended base health", ("base_hp",)),
    ):
        line_chart(output / filename, title, "Seconds", "Value",
            {key: [(r["time"], r[key]) for r in replay["history"]] for key in keys})
    if source["history"]:
        line_chart(output / "evolution.png", "Tower-defense training: maximize fitness", "Generation", "Fitness",
            {label: [(r["generation"], r[key]) for r in source["history"]]
             for label, key in (("Best", "best"), ("Mean", "mean"), ("Worst", "worst"))})
        line_chart(output / "diversity.png", "Population diversity", "Generation", "Unique fraction",
            {"Diversity": [(r["generation"], r["diversity"]) for r in source["history"]]})
    detail = {"role": "tower_defense", "strategy": asdict(strategy), "decoded_build_plan": plans,
        "config": config, "map": map_data, "settings": settings, "test_episodes": episodes,
        "replay": replay, "gif": {"file": "replay.gif", "frames": len(frames), "playback_speed": 3} if frames else None}
    (output / "detailed_report.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")

    lines = ["# Raport AI: optymalizacja stawiania wież", "", "## Role i cel eksperymentu", "",
        "**AI broni bazy: wybiera typ, miejsce i czas budowy wież. Gołębie wysyła przeciwnik.** "
        "Jedyną akcją modelu jest `build_tower`, zgodna z istniejącym socketem Godota. "
        "Wcześniejszy eksperyment optymalizujący fale miał odwrócone role i nie stanowi wyniku tego treningu.", "",
        "Cel: minimalizacja obrażeń otrzymanych przez bazę. Fitness = −liczba przecieków + "
        "0,1 × zabite / max(faktycznie wysłane gołębie, 1). Wyższy fitness jest lepszy; "
        "na wykresie porównawczym niższe obrażenia są lepsze. Premia za zabicia rozstrzyga remisy. "
        "Podstawowym kryterium selekcji jest średnia fitness po ziarnach treningowych.", "",
        "## Wyniki na oddzielnych scenariuszach testowych", ""]
    lines += table(["Strategia obrony", "Śr. obrażenia ↓", "Odchylenie", "Min–maks", "Śr. zabicia", "Śr. wieże"], [
        [name, f"{stats['mean_damage']:.2f}", f"{stats['std_damage']:.2f}",
         f"{min(e['damage'] for e in stats['episodes'])}–{max(e['damage'] for e in stats['episodes'])}",
         f"{sum(e['kills'] for e in stats['episodes']) / len(stats['episodes']):.1f}",
         f"{sum(e['tower_count'] for e in stats['episodes']) / len(stats['episodes']):.1f}"]
        for name, stats in source["comparison"].items()])
    lines += ["GENETIC: zwycięzca treningu. BASIC / SNIPER / MIXED: heurystyki pokrycia trasy, "
        "odpowiednio jeden typ lub typy naprzemienne; wszystkie mają tyle samo slotów budowy. "
        "NO_DEFENSE: kontrola bez wież. Chromosom nie jest wybierany na podstawie testu.", "",
        "![Porównanie obrażeń otrzymanych](comparison.png)", "", "## Parametry treningu", ""]
    lines += table(["Parametr", "Wartość"], [[key, settings.get(key, "brak danych")]
        for key in ("population", "generations", "slots", "duration", "dt", "seed", "mutation_rate", "train_seeds", "test_seeds")])
    lines += ["Selekcja turniejowa: 3 osobniki. Krzyżowanie: niezależnie każdy gen od jednego z rodziców (50/50). "
        "Mutacja: szum Gaussa σ=0,15 i obcięcie do [0,1]. Elitaryzm: max(1, populacja // 8). "
        "Populacja początkowa zawiera heurystyki pokrycia trasy. Losowe plany zaczynają od czasów w pierwszych 20% epizodu.", ""]
    if not source["history"]:
        lines += ["Ten raport jest ponowną oceną zapisanej strategii; nie uruchomiono nowego treningu. "
                  "Parametry populacji i pokoleń w argumentach nie opisują pochodzenia zapisanego chromosomu.", ""]
    else:
        lines += [f"Fitness najlepszego osobnika: {source['history'][0]['best']:.4f} → {source['history'][-1]['best']:.4f}.", "",
                  "![Ewolucja](evolution.png)", "", "![Różnorodność](diversity.png)", ""]
    lines += ["## Chromosom i jego interpretacja", "",
        f"Chromosom ma **{len(strategy.genes)} genów**, czyli **{len(strategy.genes) // 4} slotów budowy**. "
        "Każda czwórka to `[typ, x, y, najwcześniejszy_czas]`. Kolejność typów: "
        f"{', '.join(strategy.tower_types)}. Slot nie jest gwarancją zbudowania wieży: potrzeba środków, "
        "wolnego pola i potwierdzenia poprzedniej komendy.", "",
        "Typ = min(liczba_typów − 1, int(gen × liczba_typów)). "
        "x = round(gen × (szerokość − 1)), y = round(gen × (wysokość − 1)). "
        "Najwcześniejszy czas = gen × limit epizodu. Sloty są przeglądane według czasu, potem indeksu. "
        "Jeśli wybrane pole jest niedostępne, model wybiera najbliższe aktualnie wolne pole budowy "
        "według odległości kwadratowej; remisy rozstrzyga (x,y). "
        "Nie blokuje tańszych gotowych slotów, gdy na droższy brakuje pieniędzy.", "",
        "```json", json.dumps(asdict(strategy), indent=2), "```", "",
        "### Odkodowany plan budowy (przed korektą zajętych pól)", ""]
    lines += table(["Slot (od 0)", "Indeksy genów", "Typ", "Cel x", "Cel y", "Najwcześniej [s]"], [
        [p["slot"], f"{4*p['slot']}–{4*p['slot']+3}", p["tower_type"], p["x"], p["y"], f"{p['earliest']:.3f}"] for p in plans])
    lines += ["## Ustawienia przeciwnika: fale gołębi", "",
        "Scenariusz = ziarno + profil. Profil wybierany przez seed modulo 5: "
        "0: SCOUT, 1: TANK, 2: SPEED, 3: MIXED, 4: BURST. "
        "SCOUT/TANK/SPEED używają jednego typu, MIXED i BURST losują skład. "
        "Budżet żądanej fali to 35 energii, a BURST 65, ograniczony maksimum energii gracza. "
        "Planowany start pierwszej fali: 0 s. Następne odstępy: losowo 11–16 s, BURST 20–26 s.", "",
        "Harmonogram żądań generowany jest przed epizodem, niezależnie od chromosomu. "
        "Koszty i regeneracja obowiązują normalnie: jeśli brakuje energii lub kolejka trwa, "
        "przeciwnik czeka. Zabicia zwracają energię graczowi, więc rzeczywiste czasy i liczba wysłanych fal "
        "mogą różnić się między strategiami. Nie traktujemy takich przebiegów jako identycznych fal w identycznym czasie.", ""]
    lines += table(["Seed", "Profil", "Obrażenia ↓", "HP bazy", "Zabicia", "Wysłane", "Wieże", "Wydatek AI", "Odrzucone"], [
        [e["seed"], e["profile"], e["damage"], e["base_hp"], e["kills"], e["spawned"],
         e["tower_count"], e["money_spent"], e["rejected"]] for e in episodes])
    lines += ["## Balans gry i ekonomia", ""]
    lines += table(["Wieża", "Koszt", "Zasięg [kafle]", "Obrażenia", "Ataki/s"], [
        [name, t["cost"], t["range"], t["damage"], t["attack_speed"]] for name, t in config["towers"].items()])
    lines += table(["Gołąb", "HP", "Szybkość [kafle/s]", "Koszt energii", "Nagroda dla AI"], [
        [name, u["hp"], u["speed"], u["energy_cost"], u["ai_reward"]] for name, u in config["units"].items()])
    lines += ["```json", json.dumps({k: config[k] for k in ("economy", "combat", "base", "map") if k in config}, indent=2),
        "```", "", f"Zdrowie startowe bazy: {config.get('base', {}).get('health', 1000)}. "
        "Każdy przeciek zadaje 1 obrażenie. Wieże finansowane są z funduszy AI oraz nagród za zabicia. "
        "Energia służy wyłącznie przeciwnikowi do wysyłania gołębi.", "",
        "## Jedna rozgrywka zwycięskiej obrony", "",
        f"Seed **{replay_seed}**, profil **{replay['profile']}**. Wybrany jawnie lub jako pierwszy z listy testowej; "
        f"nie wybieramy najlepszego testu do animacji. Czas: {replay['elapsed']:.1f} s. "
        f"Baza: **{replay['base_hp']} HP**, przecieki: **{replay['damage']}**, zabicia: **{replay['kills']}**, "
        f"wieże AI: **{replay['tower_count']}**.", ""]
    if frames:
        lines += ["![AI stawia wieże i broni bazy](replay.gif)", "",
            f"Animacja lokalnej symulacji: {len(frames)} klatek, próbki co około 0,5 s, odtwarzanie 3× i pauza na końcu.", ""]
    lines += ["### Faktyczne budowy wież przez AI", ""]
    lines += table(["Czas [s]", "Slot", "Typ", "x", "y", "Koszt"], [
        [f"{r['time']:.1f}", r["slot"], r["type"], r["x"], r["y"], r["cost"]] for r in builds])
    executed = {r["slot"] for r in builds}
    lines += ["Niewykonane sloty: " + (", ".join(str(p["slot"]) for p in plans if p["slot"] not in executed) or "brak") + ". "
        "Mogły oczekiwać na pieniądze, najwcześniejszy czas lub wolne pole do końca epizodu.", "",
        "### Fale przeciwnika: planowane i rzeczywiste czasy", ""]
    lines += table(["Fala", "Plan [s]", "Start [s]", *names, "Koszt energii"], [
        [w["wave"], f"{w['scheduled_time']:.1f}", f"{w['actual_time']:.1f}", *[w[n] for n in names], w["energy_cost"]]
        for w in wave_rows])
    lines += ["### Bilans gołębi według typu", ""]
    spawned = Counter(e["unit_type"] for e in spawns)
    queued = Counter(state["wave"]["queued_units"])
    alive = Counter(u["type"] for u in state["units"])
    lines += table(["Typ", "Wysłane", "Zabite", "Dotarły do bazy", "Na trasie", "W kolejce"], [
        [n, spawned[n], state["metrics"]["kills_by_type"][n], state["metrics"]["leaks_by_type"][n], alive[n], queued[n]] for n in names])
    lines += ["![Budowy AI i wysyłki przeciwnika](timeline.png)", "", "![Walka](combat.png)", "",
        "![Środki obu stron](resources.png)", "", "![Zdrowie chronionej bazy](base_health.png)", "",
        "![Końcowe rozmieszczenie wież](final_state.png)", "", "## Uruchomienie AI przez socket Godota", "",
        "Z katalogu python_ai uruchom serwer, następnie otwórz godot_game/project.godot i uruchom grę (F6/F5 zgodnie z projektem):", "",
        "```powershell", f"python -m src.serwer --strategy {output.as_posix()}/best_strategy.json --host 127.0.0.1 --port 8080", "```", "",
        "Godot jest klientem TCP. Python odbiera init i update, odsyła JSON UTF-8 zakończony znakiem nowej linii. "
        "Przykład akcji:", "", "```json",
        '{"action":"build_tower","command_id":"ga-episode-step-seq-s0","tower_type":"BASIC","x":3,"y":3}', "```", "",
        "Model nie wysyła fal. Kontroluje budżet i wolne pola w aktualnej obserwacji. "
        "Wysyła maksymalnie jedną komendę na 0,5 s i czeka na action_result. "
        "Powtórzone lub starsze update nie generują kolejnych komend; init nowego epizodu resetuje plan. "
        "Po 2 s bez potwierdzenia sprawdza zajętość pola i rozstrzyga, czy ponowić slot. "
        "Sam Godot ostatecznie zatwierdza koszt, typ i położenie wieży.", "",
        "## Pliki, odtwarzalność i ograniczenia", "",
        "- [Chromosom obrony](best_strategy.json)",
        "- [Dane eksperymentu](report.json), [pełne przebiegi, zdarzenia i plan](detailed_report.json)",
        "- [Budowy wszystkich testów](builds.csv), [fale przeciwnika](waves.csv), [pojawienia się gołębi](spawns.csv)",
        ("- [Trening](generations.csv), " if source["history"] else "- ") +
        "[Porównanie](comparison.csv), [przebieg wybranej gry](replay.csv)", "",
        "```powershell", f"python -m src.experiment_report --input {output.as_posix()}/report.json --gif --replay-seed {replay_seed}",
        f"python -m src.pdf_report --input {output.as_posix()}/report.md", "```", "",
        "Wyniki dotyczą jednej mapy, zapisanej konfiguracji i badanych profili gołębi. "
        "Algorytm wybiera najlepszy sprawdzony plan, bez dowodu globalnego optimum. "
        "Limit slotów ogranicza liczbę wież. Wynik lokalnej symulacji nie jest wynikiem meczu w Godocie; "
        "fizyka, dyskretny krok i opóźnienia sieci mogą zmienić rezultat. "
        "Integracja socketu jest testowana protokołem; rzeczywisty mecz wymaga uruchomionego Godota.", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return detail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.json"))
    parser.add_argument("--gif", action="store_true")
    parser.add_argument("--replay-seed", type=int)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    data = source["strategy"]
    strategy = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
    detail = build_report(source, strategy, args.input.parent, make_gif=args.gif, replay_seed=args.replay_seed)
    print(f"Report: {args.input.parent / 'report.md'}; base HP: {detail['replay']['base_hp']}")


if __name__ == "__main__":
    main()
