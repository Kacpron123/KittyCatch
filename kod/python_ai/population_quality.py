"""Export whole-population learning curves for every independent GA run."""
import argparse
import json
from pathlib import Path

from src.genetic_plots import lines
from src.genetic_report import csv_file
from src.pdf_report import export_pdf


def build(source_path):
    source = json.loads(source_path.read_text(encoding="utf-8"))
    output = source_path.parent
    folder = output / "genetic_analysis"
    rows = []
    text = ["# Rozwój jakości całej populacji", "",
        f"Każdy wykres obejmuje wszystkie {source['settings']['population']} osobniki w każdej z "
        f"{source['settings']['generations']} epok. Trzy przebiegi mają różne ziarna inicjalizacji i operatorów, "
        "ale wspólne scenariusze treningowe. Wyższy fitness oznacza lepszą obronę.", "",
        "## Jak czytać wykres", "",
        "Najlepszy osobnik pokazuje jakość elity. Średnia opisuje przeciętną ocenę wszystkich osobników; "
        "słabe mutacje mogą ją obniżyć. Mediana dzieli populację na dwie równe części i jest mniej wrażliwa "
        "na pojedyncze bardzo słabe plany. Najgorszy pokazuje dolny skraj jakości. "
        "Jasne pasmo Q1–Q3 obejmuje środkowe 50% osobników; nie jest przedziałem ufności.", "",
        "Elitaryzm zachowuje najlepsze rozwiązania, lecz nie wymusza wzrostu średniej lub najgorszej oceny. "
        "Mutacja i krzyżowanie tworzą również gorszych potomków. Epoka 1 to populacja początkowa, "
        "zawierająca także trzy heurystyki. Krzywe pochodzą z ocen treningowych, nie z testu.", "",
        "Fitness epizodu: F = −L + 0,1 × K / max(N, 1), gdzie L oznacza przecieki, K zabicia, N wysłane jednostki. "
        "Ocena osobnika jest średnią po pięciu scenariuszach. Wynik −10 jest lepszy od −20.", ""]
    for run in source["search_runs"]:
        history = run["history"]
        seed = run["seed"]
        name = f"fitness_population_seed_{seed}.png"
        lines(folder / name, f"Rozwój jakości całej populacji — ziarno {seed}",
            {label: [(r["generation"] + 1, r[key]) for r in history]
             for label, key in (("Najlepszy", "best"), ("Średnia", "mean"), ("Mediana", "median"), ("Najgorszy", "worst"))},
            bands=[(r["generation"] + 1, r["q25"], r["q75"]) for r in history],
            y_label="Fitness (więcej = lepiej)", subtitle="Wszystkie osobniki; pasmo Q1–Q3 obejmuje środkowe 50% populacji.")
        text += [f"## Cała populacja — przebieg {seed}", "", f"![Jakość całej populacji](genetic_analysis/{name})", "",
            "| Miara | Epoka 1 | Ostatnia epoka |", "|---|---:|---:|"]
        for key, label in (("best", "Najlepszy"), ("mean", "Średnia"), ("median", "Mediana"), ("worst", "Najgorszy")):
            text.append(f"| {label} | {history[0][key]:.4f} | {history[-1][key]:.4f} |")
        text += ["", "Spadki średniej wskazują na gorsze oceny części potomków; nie oznaczają automatycznie "
            "utraty najlepszego planu. Poprawę całej populacji oceniamy łącznie ze zmianą mediany i kwartylów.", ""]
        rows.extend({"run_seed": seed, "epoch": r["generation"] + 1,
                     **{key: r[key] for key in ("best", "mean", "median", "worst", "q25", "q75", "diversity")}}
                    for r in history)
    csv_file(folder / "population_quality.csv", rows)
    text += ["## Dane źródłowe", "", "Surowe oceny wszystkich 2880 osobników (z powtórzeniami) są w "
        "genetic_analysis/populations.csv i population_seed_*.jsonl. Zbiorcze statystyki wszystkich 90 populacji "
        "są w population_quality.csv. Identyczne genotypy mogą być ocenione z cache; liczba osobników "
        "nie jest liczbą unikalnych chromosomów.", "",
        f"Konfiguracja SHA-256: {source['config_sha256']}.", ""]
    path = output / "rozwoj_populacji.md"
    path.write_text("\n".join(text), encoding="utf-8")
    export_pdf(path, path.with_suffix(".pdf"))
    print(path.with_suffix(".pdf").resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    build(parser.parse_args().input)
