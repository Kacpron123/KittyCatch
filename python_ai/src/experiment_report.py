"""Detailed report for tower-defense AI, including local replay and TCP usage."""
from __future__ import annotations

import argparse
import csv
import json
import hashlib
import math
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
            fields = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(stream, fieldnames=fields)
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


def layout_image(state, path, title):
    """Number actual placements in construction order; retain type colors."""
    image = render_state_image(state)
    draw = ImageDraw.Draw(image)
    tile = max(24, min(int(state["map"]["cell_size_px"]), 96))
    for i, tower in enumerate(state["towers"], 1):
        x, y = (tower["x"] + 0.5) * tile, (tower["y"] + 0.5) * tile
        color = "#2563eb" if tower["type"] == "BASIC" else "#7c3aed"
        draw.ellipse((x-10, y-10, x+10, y+10), fill=color, outline="white", width=1)
        draw.text((x, y), str(i), anchor="mm", fill="white", font_size=13)
    canvas = Image.new("RGB", (image.width, image.height + 60), "#171923")
    canvas.paste(image, (0, 60))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 10), title, fill="white", font_size=21)
    draw.text((18, 36), "Numbers = construction order | Blue = BASIC | Purple = SNIPER", fill="#c5cad6", font_size=15)
    canvas.save(path)


def additional_sections(source, output):
    lines, extra = [], {}
    probe_path = output / "godot_init.json"
    if probe_path.exists():
        init = json.loads(probe_path.read_text(encoding="utf-8"))
        probe = init.get("physics_probe", {})
        lines += ["## Zgodność modelu z fizyką i mapą Godota", "",
            "Wyeksportowano stan początkowy z rzeczywistej sceny level1 w osobnym procesie bez grafiki. "
            "Proces nie sterował meczem gracza. Rozmiar mapy, pola budowy, kierunek trasy i reguły porównano z modelem.", ""]
        lines += table(["Parametr rzeczywistego silnika", "Wartość"], [
            ["Rozmiar mapy", f"{init['map_size']['width']} × {init['map_size']['height']}"],
            ["HP startowe bazy", init["base"]["health"]],
            ["Skala sceny wieży", probe.get("tower_scene_scale", "brak")],
            ["Fizyczny zasięg BASIC [px]", probe.get("basic_range_world_px", "brak")],
            ["Długość trasy [px]", probe.get("route_length_world_px", "brak")]])
        lines += ["Kluczowa korekta: w scenie Tower skala 0,4 obejmowała również strefę ataku, "
            "podczas gdy poprzedni model zakładał pełny zasięg. Teraz efektywny zasięg = "
            "zasięg z balansu × 64 px × 0,4. BASIC ma więc 51,2 px (1,6 komórki), "
            "a SNIPER 115,2 px (3,6 komórki). Uwzględniono dodatkowo promień kolizji gołębia "
            "8 px, rozrzut względem trasy ±8 px i kolejność wejścia jednostek w zasięg wieży. "
            "Zachowano dotychczasowy fizyczny zasięg wież w Godocie — korekta dotyczy odtworzenia go w modelu.", ""]
        extra["godot_geometry"] = init
    current_hash = source.get("config_sha256")
    strategy_hash = hashlib.sha256(json.dumps(source.get("strategy", {}), sort_keys=True).encode()).hexdigest()
    validations = []
    for path in sorted(output.glob("godot_validation*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("config_sha256") == current_hash and data.get("strategy_sha256") == strategy_hash:
            validations.append(data)
    if validations:
        lines += ["## Walidacja obrony w prawdziwym silniku Godota", "",
            "Po treningu uruchomiono niezależne mecze headless. Godot połączył się z prawdziwym "
            "GameServer na prywatnym porcie TCP; model odsyłał build_tower i otrzymywał action_result. "
            "Fale miały ten sam plan i skład co w porównaniu lokalnym. Rzeczywiste momenty wysyłek "
            "i budowy pozostawały zależne od ekonomii i przebiegu walki. Wyniki te nie wybierały chromosomu.", ""]
        rows = []
        for run in validations:
            for case in run["scenarios"]:
                rows.append([f"{run['time_scale']:g}×", case["seed"], case["profile"], case["local_damage"],
                    case["godot_damage"], case["godot_kills"], case["godot_base_hp"], f"{case['accepted']} / {case['rejected']}"])
        lines += table(["Tempo", "Seed", "Profil", "Model: obrażenia", "Godot: obrażenia", "Godot: zabicia", "HP", "Budowy OK / odrz."], rows)
        errors = [abs(case["godot_damage"] - case["local_damage"]) for run in validations for case in run["scenarios"]]
        lines += [f"Średni błąd bezwzględny liczby obrażeń model–silnik: **{sum(errors)/len(errors):.2f} HP** "
            f"na {len(errors)} przebiegach. Zmienność pozostaje możliwa przez rozrzut pozycji, "
            "kolizje, czas pocisków, krok silnika i opóźnienia komunikacji. "
            "Test 4× używał 240 kroków fizyki/s i limitu 240 klatek/s. "
            "Nie jest to gwarancja takiego samego wyniku na dowolnym komputerze i dowolnej fali gracza.", ""]
        first = validations[0]["scenarios"][0]
        layout_image(first["actual"]["final_state"], output / "godot_layout.png", "Actual Godot match: final tower layout")
        lines += ["![Wieże z rzeczywistego meczu Godota](godot_layout.png)", ""]
        for run in validations:
            for case in run["scenarios"]:
                if case.get("animation"):
                    lines += [f"[Animacja obserwacji rzeczywistego meczu Godota, seed {case['seed']}]({case['animation']}). "
                        "Rysunek odtwarza pozycje i statystyki odebrane z silnika, a nie prognozę symulatora; "
                        "odtwarzanie 3×.", ""]
        extra["godot_validation"] = validations
    stress_path = output / "stress_test.json"
    if stress_path.exists():
        stress = json.loads(stress_path.read_text(encoding="utf-8"))
        if stress.get("config_sha256") == current_hash:
            lines += ["## Próby przeciążeniowe: limity energii 100 / 300 / 1000", "",
                "Osobna seria poza treningiem i wyborem modelu. Każdy profil SCOUT/TANK/SPEED/MIXED/BURST "
                "zbadano dla limitów hard=100, medium=300, easy=1000. "
                "W tym teście gracz zaczynał z pełnym zbiornikiem energii, zamiast standardowych 40. "
                "Budżet żądanej fali był równy limitowi; gołębie wysyłano co 0,1 s, "
                "a planowane odstępy między falami skrócono o połowę. To test dużej zgromadzonej fali, "
                "a nie bezpośrednie porównanie normalnego początku gry.", ""]
            groups = {}
            for row in stress["rows"]:
                groups.setdefault((row["strategy"], row["difficulty"], row["capacity"]), []).append(row)
            lines += table(["Układ", "Poziom", "Limit", "Śr. obrażenia", "Min–maks", "Zniszczenia bazy / próby"], [
                [name, difficulty, capacity, f"{sum(r['damage'] for r in rows)/len(rows):.1f}",
                 f"{min(r['damage'] for r in rows)}–{max(r['damage'] for r in rows)}",
                 f"{sum(r['base_hp'] == 0 for r in rows)} / {len(rows)}"]
                for (name, difficulty, capacity), rows in groups.items()])
            lines += ["![Odporność na duże fale](stress_test.png)", "",
                "Większy limit daje graczowi możliwość zgromadzenia silniejszej fali. "
                "Wynik dotyczy automatycznych profili i nie dowodzi, że gracz nie znajdzie skuteczniejszego ataku.", ""]
            extra["stress_test"] = stress
    return lines, extra


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
    layouts = []
    for run in source.get("search_runs", []):
        data = run["strategy"]
        candidate = Strategy(tuple(data["tower_types"]), tuple(data["genes"]), data["duration"])
        episode = rollout(candidate, config, map_data, seeds[0], duration=duration, dt=dt, trace=True)
        filename = f"layout_seed_{run['seed']}.png"
        layout_image(episode["final_state"], output / filename, f"Run {run['seed']} | scenario {seeds[0]} | base {episode['base_hp']} HP")
        builds_for_layout = [e for e in episode["events"] if e["kind"] == "action_result" and e["accepted"]]
        layouts.append({"seed": run["seed"], "image": filename, "training_fitness": run["training_fitness"],
                        "strategy": data, "episode": episode, "builds": builds_for_layout})
    if layouts:
        tiles = []
        for layout in layouts:
            with Image.open(output / layout["image"]) as tile:
                tile = tile.crop((0, 0, state["map"]["width"] * max(24, min(int(state["map"]["cell_size_px"]), 96)), tile.height))
                tile.thumbnail((650, 400), Image.Resampling.LANCZOS)
                tiles.append(tile.copy())
        atlas = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles)), "#171923")
        offset = 0
        for tile in tiles:
            atlas.paste(tile, (offset, 0))
            offset += tile.width
        atlas.save(output / "layouts_overview.png")
        line_chart(output / "search_runs.png", "Independent genetic runs: best fitness", "Generation", "Fitness", {
            f"Seed {run['seed']}": [(r["generation"], r["best"]) for r in run["history"]]
            for run in source["search_runs"]})
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
        "replay": replay, "layouts": layouts, "config_sha256": source.get("config_sha256"),
        "gif": {"file": "replay.gif", "frames": len(frames), "playback_speed": 3} if frames else None}
    (output / "detailed_report.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")

    lines = ["# Sprawozdanie: nowe układy obrony KittyCatch", "", "## Role i cel eksperymentu", "",
        "**AI broni bazy: wybiera typ, miejsce i czas budowy wież. Gołębie wysyła przeciwnik.** "
        "Jedyną akcją modelu jest `build_tower`, zgodna z istniejącym socketem Godota. "
        f"Badanie dotyczy limitu energii {config['economy']['player']['max_energy']}, "
        f"bazy {config.get('base', {}).get('health', 1000)} HP i epizodów długości {duration:g} s.", "",
        "Cel: minimalizacja obrażeń otrzymanych przez bazę. Fitness = −liczba przecieków + "
        "0,1 × zabite / max(faktycznie wysłane gołębie, 1). Wyższy fitness jest lepszy; "
        "na wykresie porównawczym niższe obrażenia są lepsze. Premia za zabicia rozstrzyga remisy. "
        "Podstawowym kryterium selekcji jest średnia fitness po ziarnach treningowych.", "",
    ]
    if source.get("previous_config"):
        old = source["previous_config"]
        lines += ["## Zmiany zasad uwzględnione w eksperymencie", ""]
        changes = [["HP bazy", old.get("base", {}).get("health", 1000), config.get("base", {}).get("health", 1000)],
            ["Zwrot energii za zabicie", f"{old['economy']['player']['kill_energy_refund_fraction'] * 100:g}%",
             f"{config['economy']['player']['kill_energy_refund_fraction'] * 100:g}%"]]
        for name, unit in config["units"].items():
            for key, label in (("hp", "HP"), ("speed", "prędkość"), ("energy_cost", "koszt")):
                changes.append([f"{name}: {label}", old["units"].get(name, {}).get(key, "brak"), unit[key]])
        for name, tower in config["towers"].items():
            for key in ("cost", "range", "damage", "attack_speed", "rotation_speed"):
                if key in tower:
                    changes.append([f"{name}: {key}", old["towers"].get(name, {}).get(key, "brak"), tower[key]])
        lines += table(["Parametr", "Poprzednia konfiguracja", "Aktualna konfiguracja"], changes)
        refunds = ", ".join(f"{name} {math.ceil(unit['energy_cost'] / 2)}" for name, unit in config["units"].items())
        lines += ["Tabela porównuje zapis poprzedniego eksperymentu z konfiguracją używaną w tym treningu. "
            "Wartości niezmienione pozostają widoczne dla pełnego kontekstu.", "",
            f"Dotarcie do celu zwraca ceil(koszt/2): {refunds}. "
            f"Zwrot za zabicie wynosi {config['economy']['player']['kill_energy_refund_fraction'] * 100:g}% kosztu jednostki; "
            "oba zwroty respektują limit energii.", ""]
    lines += ["## Wyniki na oddzielnych scenariuszach testowych", ""]
    lines += table(["Strategia obrony", "Śr. obrażenia ↓", "Odchylenie", "Min–maks", "Śr. zabicia", "Śr. wieże"], [
        [name, f"{stats['mean_damage']:.2f}", f"{stats['std_damage']:.2f}",
         f"{min(e['damage'] for e in stats['episodes'])}–{max(e['damage'] for e in stats['episodes'])}",
         f"{sum(e['kills'] for e in stats['episodes']) / len(stats['episodes']):.1f}",
         f"{sum(e['tower_count'] for e in stats['episodes']) / len(stats['episodes']):.1f}"]
        for name, stats in source["comparison"].items()])
    lines += ["GENETIC: zwycięzca treningu. BASIC / SNIPER / MIXED: heurystyki pokrycia trasy, "
        "odpowiednio jeden typ lub typy naprzemienne; wszystkie mają tyle samo slotów budowy. "
        "NO_DEFENSE: kontrola bez wież. Chromosom nie jest wybierany na podstawie testu.", "",
        "GA_z: zwycięzca niezależnego przebiegu o ziarnie z. PREVIOUS: poprzedni chromosom ponownie "
        "oceniony na aktualnym balansie i tych samych scenariuszach, z zachowaniem jego zapisanych czasów budowy. "
        "Nie mieszamy historycznych wyników uzyskanych przy innych zasadach z aktualnym testem.", "",
        "![Porównanie obrażeń otrzymanych](comparison.png)", ""]
    alternatives = {name: stats["mean_damage"] for name, stats in source["comparison"].items()
                    if name not in ("GENETIC", "NO_DEFENSE")}
    if alternatives and source["comparison"]["GENETIC"]["mean_damage"] > min(alternatives.values()):
        best_alternative = min(alternatives, key=alternatives.get)
        lines += [f"Na tym zbiorze testowym {best_alternative} ma niższą średnią liczbę obrażeń "
            f"({alternatives[best_alternative]:.2f}) niż wybrany GENETIC "
            f"({source['comparison']['GENETIC']['mean_damage']:.2f}). "
            "Nie zmieniamy po teście wyboru modelu. Różnice na skończonej liczbie ziaren "
            "należy odróżniać od gwarantowanej przewagi strategii.", ""]
    if layouts:
        lines += ["## Nowe warianty rozmieszczenia wież", "",
            "Każdy wariant pochodzi z osobnego treningu. Główny zwycięzca został wybrany według fitness treningowego, "
            "przed testem. Przy równych wynikach pomiędzy przebiegami wygrywa pierwszy. "
            "Poniższe mapy pokazują faktycznie zbudowane wieże na tym samym pierwszym scenariuszu testowym; "
            "niewykonane sloty pozostają tylko w chromosomie. Numery oznaczają kolejność budowy.", ""]
        lines += table(["Ziarno treningu", "Fitness treningowy", "Wybrany model", "Plik strategii"], [
            [r["seed"], f"{r['training_fitness']:.6f}", "TAK" if r["seed"] == settings.get("seed") else "—",
             f"strategy_seed_{r['seed']}.json"] for r in layouts])
        for layout in layouts:
            lines += [f"### Układ z przebiegu {layout['seed']}", "", f"![Układ wież {layout['seed']}]({layout['image']})", ""]
            lines += table(["Nr", "Start [s]", "Slot", "Typ", "x", "y"], [
                [i, f"{e['elapsed_seconds']:.1f}", int(e["command_id"].rsplit("-s", 1)[1]),
                 e["tower_type"], e["grid_x"], e["grid_y"]] for i, e in enumerate(layout["builds"], 1)])
        lines += ["![Przebiegi niezależnego treningu](search_runs.png)", ""]
    lines += ["## Parametry treningu", ""]
    lines += table(["Parametr", "Wartość"], [[key, settings.get(key, "brak danych")]
        for key in ("population", "generations", "slots", "duration", "dt", "seed", "search_seeds", "mutation_rate", "train_seeds", "test_seeds")])
    lines += ["Selekcja turniejowa: 3 osobniki. Krzyżowanie: niezależnie każdy gen od jednego z rodziców (50/50). "
        "Mutacja: szum Gaussa σ=0,15 i obcięcie do [0,1]. Elitaryzm: max(1, populacja // 8). "
        "Populacja początkowa zawiera heurystyki pokrycia trasy. Losowe plany zaczynają od czasów w pierwszych 20% epizodu. "
        "Remisy fitness wewnątrz populacji rozstrzyga losowanie kontrolowane ziarnem przebiegu, "
        "co pozwala zachować różne równie skuteczne układy.", "",
        f"Identyfikator konfiguracji SHA-256: {source.get('config_sha256', 'brak')}.", ""]
    if not source["history"]:
        lines += ["Ten raport jest ponowną oceną zapisanej strategii; nie uruchomiono nowego treningu. "
                  "Parametry populacji i pokoleń w argumentach nie opisują pochodzenia zapisanego chromosomu.", ""]
    else:
        lines += [f"Fitness najlepszego osobnika: {source['history'][0]['best']:.4f} → {source['history'][-1]['best']:.4f}.", "",
                  "![Ewolucja](evolution.png)", "", "![Różnorodność](diversity.png)", ""]
        if abs(source["history"][0]["best"] - source["history"][-1]["best"]) < 1e-12:
            lines += ["Najlepszy wynik był osiągalny już w populacji początkowej. "
                "Trening nie poprawił tego kryterium; zbadał alternatywne układy i ich odporność na zmianę scenariusza. "
                "Różne chromosomy z takim samym fitness nie są dowodem przewagi nad heurystyką.", ""]
    genetic_appendix = output / "genetic_analysis" / "analysis_report.md"
    if source.get("genetic_analysis") and genetic_appendix.exists():
        lines += genetic_appendix.read_text(encoding="utf-8").splitlines() + [""]
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
    lines += table(["Wieża", "Koszt", "Zasięg w JSON", "Zasięg fizyczny [kafle]", "Obrażenia", "Ataki/s"], [
        [name, t["cost"], t["range"], f"{t['range'] * config.get('combat', {}).get('tower_range_scale', 1):.2f}",
         t["damage"], t["attack_speed"]] for name, t in config["towers"].items()])
    lines += table(["Gołąb", "HP", "Szybkość [kafle/s]", "Koszt energii", "Nagroda dla AI"], [
        [name, u["hp"], u["speed"], u["energy_cost"], u["ai_reward"]] for name, u in config["units"].items()])
    lines += ["```json", json.dumps({k: config[k] for k in ("economy", "combat", "base", "map") if k in config}, indent=2),
        "```", "", f"Zdrowie startowe bazy: {config.get('base', {}).get('health', 1000)}. "
        "Każdy przeciek zadaje 1 obrażenie. Wieże finansowane są z funduszy AI oraz nagród za zabicia. "
        "Energia służy wyłącznie przeciwnikowi do wysyłania gołębi. Zwrot przy dotarciu do celu: ceil(koszt/2).", "",
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
        "![Końcowe rozmieszczenie wież](final_state.png)", ""]
    extra_lines, extra_data = additional_sections(source, output)
    lines += extra_lines
    detail.update(extra_data)
    (output / "detailed_report.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")
    lines += ["## Uruchomienie AI przez socket Godota", "",
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
