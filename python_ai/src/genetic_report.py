"""Turn recorded populations and genetic operations into figures and an appendix."""
import argparse
import json
import statistics
import hashlib
import importlib.metadata
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw

from src.experiment_report import csv_file, layout_image, table
from src.genetic_ai import Strategy, rollout
from src.simulation import Simulation
from src.genetic_plots import bars, canvas, font, heatmap, lines, operator_diagram, scatter


def benchmark_metrics(comparisons):
    rows = []
    for name, stats in comparisons.items():
        episodes = stats["episodes"]
        rows.append({"strategy": name, "episodes": len(episodes), "damage": stats["mean_damage"],
            "damage_std": stats["std_damage"], "base_hp": statistics.mean(e["base_hp"] for e in episodes),
            "kills": statistics.mean(e["kills"] for e in episodes),
            "kill_fraction": statistics.mean(e["kills"] / max(e["spawned"],1) for e in episodes),
            "money_spent": statistics.mean(e["money_spent"] for e in episodes),
            "kills_per_100_money": statistics.mean(100*e["kills"]/max(e["money_spent"],1) for e in episodes)})
    return rows


def architecture(path):
    image,draw=canvas("Architektura rozwiązania", "Rozdzielono trening offline, ewaluację i politykę wykonywaną w grze.",height=590)
    boxes=[(55,145,405,285,"GODOT","Mapa, wieże, gołębie, kolizje"),
        (505,145,855,285,"PYTHON / POLITYKA","Genotyp → plan → build_tower"),
        (505,365,855,505,"ALGORYTM GENETYCZNY","Selekcja, krzyżowanie, mutacja"),
        (955,365,1290,505,"SYMULATOR","5 scenariuszy → fitness")]
    for x0,y0,x1,y1,title,detail in boxes:
        draw.rounded_rectangle((x0,y0,x1,y1),radius=14,fill="#e6eff8",outline="#286a9d",width=2)
        draw.text(((x0+x1)/2,y0+40),title,anchor="mm",font=font(19,True),fill="#19334f")
        draw.text(((x0+x1)/2,y0+87),detail,anchor="mm",font=font(15),fill="#294b69")
    for start,end in [((410,180),(495,180)),((495,245),(410,245)),((680,355),(680,295)),((865,420),(945,420)),((945,465),(865,465))]:
        draw.line((*start,*end),fill="#1565a8",width=3)
        dx,dy=end[0]-start[0],end[1]-start[1]
        length=(dx*dx+dy*dy)**.5
        ux,uy=dx/length,dy/length
        draw.polygon([end,(end[0]-12*ux+6*uy,end[1]-12*uy-6*ux),(end[0]-12*ux-6*uy,end[1]-12*uy+6*ux)],fill="#1565a8")
    draw.text((450,110),"TCP / JSON",anchor="mm",font=font(16,True),fill="#19334f")
    draw.text((450,315),"init/update ↔ akcja",anchor="mm",font=font(14),fill="#53687d")
    image.save(path)


def render(source_path):
    source=json.loads(source_path.read_text(encoding="utf-8"))
    output=source_path.parent
    folder=output/"genetic_analysis"
    analysis=json.loads((folder/"analysis.json").read_text(encoding="utf-8"))
    if analysis["config_sha256"] != source["config_sha256"]:
        raise ValueError("Genetic telemetry belongs to a different balance")
    if analysis.get("random"):
        source["comparison"]["RANDOM"]={key:analysis["random"][key] for key in ("mean_damage","std_damage","episodes")}
    runs=analysis["runs"]
    winner=next(r for r in runs if r["seed"]==source["settings"]["seed"])
    all_records={run["seed"]:[json.loads(line) for line in (folder/run["telemetry"]).read_text(encoding="utf-8").splitlines()] for run in runs}
    records=all_records[winner["seed"]]
    settings=source["settings"]
    implementation = b"".join((Path(__file__).parent/name).read_bytes() for name in ("genetic_ai.py","simulation.py","data.py"))
    analysis["implementation_sha256"] = hashlib.sha256(implementation).hexdigest()
    analysis["environment"] = {"python": sys.version.split()[0], "Pillow": importlib.metadata.version("Pillow"),
                               "ReportLab": importlib.metadata.version("reportlab")}
    epochs=lambda values,key:[(r["generation"]+1,r[key]) for r in values]
    history=winner["history"]
    figures=[]
    def register(name, title, caption):
        figures.append({"file":name,"title":title,"caption":caption})

    lines(folder/"fitness_distribution.png","Rozwój jakości całej populacji",{
        "Najlepszy":epochs(history,"best"),"Średnia":epochs(history,"mean"),
        "Mediana":epochs(history,"median"),"Najgorszy":epochs(history,"worst")},
        subtitle="Pasmo: kwartyle 25–75%; epoka 1 jest populacją początkową.", y_label="Fitness (więcej = lepiej)",
        bands=[(r["generation"]+1,r["q25"],r["q75"]) for r in history])
    register("fitness_distribution.png","Fitness, mediana i kwartyle", "Pasma i statystyki dotyczą wszystkich ocenionych osobników, a nie wyłącznie elity.")
    lines(folder/"best_runs.png","Najlepszy fitness w niezależnych treningach",{
        f"Ziarno {run['seed']}":epochs(run["history"],"best") for run in runs}, y_label="Fitness",
        subtitle="Wspólne scenariusze treningowe i parametry; różne ziarna wyszukiwania.")
    register("best_runs.png","Powtarzalność zbieżności", "Porównujemy ziarna losowania operatorów, nie różne zbiory treningowe.")
    lines(folder/"diversity_detail.png","Różnorodność populacji i fenotypów",{
        "Unikalne genotypy":epochs(history,"diversity"),
        "Unikalne plany":epochs(history,"phenotype_diversity"),
        "Śr. odchylenie genów":epochs(history,"mean_gene_std")}, y_label="Ułamek / odchylenie",
        subtitle="Fenotyp: odkodowany plan; czasy zaokrąglone do siatki decyzji 0,5 s.")
    register("diversity_detail.png","Różnorodność genotypu i fenotypu", "Genotypy mogą być różne mimo takiego samego typu wieży, pola i przedziału czasowego po dekodowaniu.")
    labels=[f"{i//4}{('T','x','y','t')[i%4]}" for i in range(len(records[0]["best_genes"]))]
    heatmap(folder/"chromosome_evolution.png","Chromosom najlepszego osobnika w kolejnych epokach",
        [r["best_genes"] for r in records],column_labels=labels,
        subtitle="T = typ, x/y = współrzędne, t = najwcześniejszy czas; cztery kolumny na slot.")
    register("chromosome_evolution.png","Ewolucja 40 genów zwycięzcy epoki", "Kolor to surowa wartość genu [0,1]. Zmiana koloru nie musi zmieniać odkodowanego rozwiązania ani fitness.")
    std_matrix=[r["gene_std"] for r in records]
    heatmap(folder/"gene_diversity.png","Odchylenie standardowe każdego genu w populacji",std_matrix,
        column_labels=labels,vmax=max(v for row in std_matrix for v in row),
        subtitle="Kolumna = konkretny gen; wiersz = epoka. To miara rozrzutu, nie ważności genu.")
    register("gene_diversity.png","Rozrzut genów w populacji", "Niska wariancja wskazuje koncentrację wartości, ale sama nie dowodzi znaczenia przyczynowego danego genu.")
    matrix=[sorted((p["fitness"] for p in r["population"]),reverse=True) for r in records]
    heatmap(folder/"population_fitness.png","Cała populacja: rozkład fitness w każdej epoce",matrix,
        vmin=min(v for row in matrix for v in row),vmax=max(v for row in matrix for v in row),
        subtitle="Kolumny posortowane od najlepszego do najgorszego; pozycja nie identyfikuje potomka.")
    register("population_fitness.png","Macierz jakości populacji", "Wszystkie osobniki pozostają widoczne, w tym słabi potomkowie powstający wskutek eksploracji.")
    curve=winner["test_curve"]
    lines(folder/"generalization.png","Uczenie i późniejsza ocena na zbiorze testowym",{
        "Trening":epochs(curve,"training_fitness"),"Test post hoc":epochs(curve,"test_fitness")}, y_label="Fitness",
        subtitle="Test policzono po zakończeniu treningu; nie sterował selekcją ani wyborem epoki.")
    register("generalization.png","Generalizacja najlepszego osobnika epoki", "Krzywa testowa to dodatkowa analiza po treningu. Nie stosowano early stopping na podstawie tych danych.")
    scatter(folder/"genotype_fitness.png",records)
    register("genotype_fitness.png","Odległość chromosomów a fitness", "Odległość RMS liczona jest w przestrzeni surowych genów i nie jest odległością między zachowaniami w grze.")
    lines(folder/"evaluation_cost.png","Koszt ewaluacji i wykorzystanie pamięci wyników",{
        "Wykonane symulacje":epochs(history,"cumulative_rollouts"),
        "Bez cache":[(r["generation"]+1,(r["generation"]+1)*settings["population"]*len(settings["train_seeds"])) for r in history]},
        y_label="Liczba symulacji",subtitle="Każdy nowy genotyp jest oceniany na wszystkich scenariuszach treningowych.")
    register("evaluation_cost.png","Rzeczywisty koszt treningu", "Cache działa po całym genotypie. Wykres nie obejmuje późniejszych testów, baseline'ów i ablacji.")

    offspring=[(record,birth) for record in records for birth in record["births"]]
    n_genes=len(labels)
    mutation_counts=Counter(m["gene"] for record,b in offspring for m in b["mutations"])
    rates={str(i):mutation_counts[i]/max(len(offspring),1) for i in range(n_genes)}
    bars(folder/"mutation_by_gene.png","Zarejestrowana częstość mutacji każdego genu",rates,
        subtitle="Próba mutacji obejmuje również zmiany obcięte do granicy [0,1].",ylabel="Ułamek potomków",expected=settings["mutation_rate"])
    register("mutation_by_gene.png","Częstość mutacji w 40 pozycjach", "Przerywana linia to zadane prawdopodobieństwo 0,15, a nie dopasowanie do zmierzonych słupków.")
    operator_rows=[]
    for record in records[1:]:
        births=record["births"]
        mutations=[m for b in births for m in b["mutations"]]
        denominator=max(1,len(births)*n_genes)
        operator_rows.append({"generation":record["generation"],
            "attempt_rate":len(mutations)/denominator,"change_rate":sum(m["changed"] for m in mutations)/denominator,
            "clip_rate":sum(m["clipped"] for m in mutations)/max(1,len(mutations)),
            "parent_fitness":statistics.mean(f for b in births for f in b["parent_fitness"]),
            "previous_population_mean":records[record["generation"]-1]["summary"]["mean"],
            "improved_fraction":sum(b["fitness_delta_vs_parent"]>1e-12 for b in births)/max(1,len(births))})
    lines(folder/"operator_rates.png","Próby mutacji, faktyczne zmiany i obcinanie",{
        "Próba na gen":epochs(operator_rows,"attempt_rate"),"Zmiana na gen":epochs(operator_rows,"change_rate"),
        "Obcięte / próby":epochs(operator_rows,"clip_rate")},y_label="Ułamek",subtitle="Pierwsza reprodukcja tworzy populację epoki 2.")
    register("operator_rates.png","Co faktycznie robiła mutacja", "Szum może zostać obcięty na 0 lub 1; dlatego próba mutacji nie zawsze zmienia gen.")
    lines(folder/"selection_pressure.png","Efekt selekcji turniejowej",{
        "Średnia wybranych rodziców":epochs(operator_rows,"parent_fitness"),
        "Średnia poprzedniej populacji":epochs(operator_rows,"previous_population_mean")},y_label="Fitness",
        subtitle="Porównanie rodziców z populacją, z której ich wylosowano; turniej ma 3 uczestników.")
    register("selection_pressure.png","Presja selekcyjna", "Rodzice zwykle mają wyższy fitness od przeciętnego osobnika, ale selekcja nadal dopuszcza eksplorację.")
    candidates=[(r,b) for r,b in offspring if b["mutations"] and b["parent_ids"][0]!=b["parent_ids"][1]]
    if candidates:
        record,birth=max(candidates,key=lambda pair:pair[1]["fitness_delta_vs_parent"])
        parents={p["id"]:p["genes"] for p in records[record["generation"]-1]["population"]}
        operator_diagram(folder/"operators_example.png",birth,[parents[i] for i in birth["parent_ids"]])
        (folder/"operator_example.json").write_text(json.dumps({"epoch":record["generation"]+1,"birth":birth},indent=2),encoding="utf-8")
        register("operators_example.png","Pochodzenie genów rzeczywistego potomka", "Przedstawiono zmierzony przykład. Zestawienie nie rozdziela przyczynowo efektu krzyżowania od efektu mutacji.")
    policy_types=[]
    build_times=[]
    geometry=Simulation(source["config"],source["map"])
    geometry_width, geometry_height=geometry.width, geometry.height
    for record in records:
        plan=Strategy(tuple(source["strategy"]["tower_types"]),tuple(record["best_genes"]),settings["duration"]).decode(geometry_width,geometry_height)
        counts=Counter(p["tower_type"] for p in plan)
        policy_types.append({"generation":record["generation"],**counts})
        build_times.append({"generation":record["generation"],"mean":statistics.mean(p["earliest"] for p in plan),
            "min":min(p["earliest"] for p in plan),"max":max(p["earliest"] for p in plan)})
    lines(folder/"tower_types.png","Typy wież w najlepszym odkodowanym planie",{
        name:epochs([{**r,name:r.get(name,0)} for r in policy_types],name) for name in source["strategy"]["tower_types"]},y_label="Liczba slotów",
        subtitle="To plan, a nie gwarancja faktycznego zakupu wszystkich wież.")
    register("tower_types.png","Zmiany typów wież", "Rozkład obejmuje wszystkie sloty chromosomu, także niewykonane z braku środków.")
    lines(folder/"build_times.png","Ewolucja najwcześniejszych czasów budowy",{
        label:epochs(build_times,key) for label,key in (("Najwcześniejszy","min"),("Średni","mean"),("Najpóźniejszy","max"))},
        y_label="Sekundy",subtitle="Rzeczywisty start może być późniejszy ze względu na środki i poprzednią komendę.")
    register("build_times.png","Uczenie momentu budowy", "Gen czasu ustala dolną granicę, a nie bezwarunkową komendę zakupu.")
    selected_epochs=sorted(set([0,1,3,7,len(records)-1]))
    tiles=[]
    animation=[]
    for epoch in range(len(records)):
        record=records[epoch]
        policy=Strategy(tuple(source["strategy"]["tower_types"]),tuple(record["best_genes"]),settings["duration"])
        episode=rollout(policy,source["config"],source["map"],settings["train_seeds"][3%len(settings["train_seeds"])],
            duration=settings["duration"],dt=settings["dt"],trace=True)
        path=folder/f"layout_epoch_{epoch+1}.png"
        layout_image(episode["final_state"],path,f"Epoch {epoch+1} | training fitness {record['summary']['best']:.4f}")
        with Image.open(path) as image:
            frame=Image.new("RGB",(image.width,image.height+50),"white")
            frame.paste(image,(0,0))
            draw=ImageDraw.Draw(frame)
            for gene,value in enumerate(record["best_genes"]):
                x=gene*image.width/n_genes
                color=(int(242-220*value),int(247-100*value),int(250-45*value))
                draw.rectangle((x,image.height,x+image.width/n_genes,image.height+22),fill=color)
            draw.text((12,image.height+28),"Geny: [typ, x, y, czas] × 10 | Epoki, nie sekundy rozgrywki",font=font(13),fill="#19334f")
            animation.append(frame.convert("P",palette=Image.Palette.ADAPTIVE,colors=128))
            if epoch in selected_epochs:
                image.thumbnail((620,380),Image.Resampling.LANCZOS)
                tiles.append(image.copy())
    animation[0].save(folder/"genetic_evolution.gif",save_all=True,append_images=animation[1:],
        duration=[800]*(len(animation)-1)+[2000],loop=0,disposal=2,optimize=False)
    atlas=Image.new("RGB",(1240,math_ceil_half(len(tiles))*400),"white")
    for i,tile in enumerate(tiles):atlas.paste(tile,((i%2)*620,(i//2)*400))
    atlas.save(folder/"layout_evolution.png")
    register("layout_evolution.png","Jak zmieniało się rozmieszczenie", "Każdą epokę odtworzono na tym samym scenariuszu treningowym. To nie są wybrane najlepsze scenariusze testowe.")
    benchmark=benchmark_metrics(source["comparison"])
    for name,key,title,unit in (("benchmark_damage.png","damage","Porównanie z regułami i układami losowymi","Średnie obrażenia bazy"),
        ("benchmark_efficiency.png","kills_per_100_money","Skuteczność wykorzystania środków AI","Zabicia na 100 wydanych środków"),
        ("benchmark_kill_rate.png","kill_fraction","Udział zatrzymanych przeciwników","Ułamek wysłanych jednostek")):
        bars(folder/name,title,{r["strategy"]:r[key] for r in benchmark},ylabel=unit)
        register(name,title,"Przeciwnik otrzymuje zwroty energii, a AI reinwestuje nagrody. Wydatki całkowite mogą przekroczyć budżet startowy 150.")
    ablations=analysis.get("ablations",[])
    groups={name:[r for r in ablations if r["variant"]==name] for name in sorted({r["variant"] for r in ablations})}
    if groups:
        lines(folder/"ablations.png","Kontrolowane wyłączanie operatorów",{
            name:[(epoch+1,statistics.mean(r["history"][epoch]["best"] for r in cases)) for epoch in range(len(cases[0]["history"]))]
            for name,cases in groups.items()},y_label="Śr. najlepszy fitness",subtitle="Każdy wariant: 3 ziarna, populacja 12, 12 epok, te same fale treningowe.")
        register("ablations.png","Badanie ablacyjne operatorów","FULL jest kontrolą przy mniejszym budżecie obliczeń niż główny eksperyment. Krzyżowanie, mutacja i elitaryzm są wyłączane pojedynczo.")
        bars(folder/"ablation_test.png","Ablacje: późniejsze wyniki testowe",{
            name:statistics.mean(r["test_damage"] for r in cases) for name,cases in groups.items()},ylabel="Śr. obrażenia bazy",
            errors={name:statistics.pstdev(r["test_damage"] for r in cases) for name,cases in groups.items()},
            subtitle="Wąsy: odchylenie standardowe pomiędzy trzema ziarnami wyszukiwania.")
        register("ablation_test.png","Operator a generalizacja","Trzy powtórzenia to mała próba. Wynik nie uprawnia do uniwersalnego rankingu wariantów GA.")
    architecture(folder/"architecture.png")
    export_rows=[]
    birth_rows=[]
    for seed,run_records in all_records.items():
        for record in run_records:
            for p in record["population"]:
                export_rows.append({"run_seed":seed,"epoch":record["generation"]+1,
                    **{k:p[k] for k in ("index","id","fitness","damage","kills","money_spent")},
                    **{f"gene_{i:02d}":g for i,g in enumerate(p["genes"])}})
            for birth in record["births"]:
                birth_rows.append({"run_seed":seed,"epoch":record["generation"]+1,"child_id":birth["child_id"],
                    "parent_a":birth["parent_ids"][0],"parent_b":birth["parent_ids"][1],"fitness":birth["fitness"],
                    "delta_vs_best_parent":birth["fitness_delta_vs_parent"],"mutation_attempts":len(birth["mutations"]),
                    "actual_changes":sum(m["changed"] for m in birth["mutations"]),
                    "clipped":sum(m["clipped"] for m in birth["mutations"])})
    csv_file(folder/"populations.csv",export_rows)
    csv_file(folder/"offspring.csv",birth_rows)
    csv_file(folder/"operators.csv",operator_rows)
    csv_file(folder/"benchmark_metrics.csv",benchmark)
    summary={"offspring":len(offspring),"mutation_attempts":sum(mutation_counts.values()),
        "actual_changes":sum(m["changed"] for r,b in offspring for m in b["mutations"]),
        "clipped":sum(m["clipped"] for r,b in offspring for m in b["mutations"]),
        "improved":sum(b["fitness_delta_vs_parent"]>1e-12 for r,b in offspring),
        "tied":sum(abs(b["fitness_delta_vs_parent"])<=1e-12 for r,b in offspring),
        "worse":sum(b["fitness_delta_vs_parent"] < -1e-12 for r,b in offspring),
        "figures":figures,"benchmark":benchmark}
    (folder/"figure_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (folder/"analysis.json").write_text(json.dumps(analysis,indent=2),encoding="utf-8")
    text=["## Szczegółowa analiza algorytmu genetycznego", "",
        "Epoka oznacza ocenę jednej populacji. Epoka 1 zawiera populację początkową, "
        f"więc {settings['generations']} epoki oceny oznaczają {settings['generations']-1} przejść reprodukcyjnych. "
        "GA jest algorytmem ewolucyjnym; nie stosuje gradientów ani epok uczenia sieci neuronowej.","",
        "Telemetria opisuje przebiegi treningowe zapisane w tym eksperymencie. Zgodność końcowych "
        "chromosomów jest sprawdzana podczas analizy. Krzywe testowe obliczono po treningu; "
        "nie służyły do selekcji ani wyboru zwycięskiego modelu.",""]
    text += ["[Animacja zmian chromosomu i układu obrony epoka po epoce](genetic_analysis/genetic_evolution.gif). "
        "Każdy plan odtworzono na tym samym scenariuszu treningowym; pasek pod mapą przedstawia wartości 40 genów.",""]
    text+=table(["Ziarno","Epoki","Pierwsza epoka najlepszego zaobserwowanego fitness","Wykonane symulacje treningowe"],
        [[r["seed"],len(r["history"]),r["first_best_epoch"]+1,r["history"][-1]["cumulative_rollouts"]] for r in runs])
    text += ["### Operatory w liczbach dla wybranego przebiegu", ""]
    text+=table(["Pomiar","Wartość"],[["Potomkowie (bez elity)",summary["offspring"]],
        ["Próby mutacji",summary["mutation_attempts"]],["Rzeczywiste zmiany genu",summary["actual_changes"]],
        ["Mutacje obcięte do granic",summary["clipped"]],["Potomkowie lepsi od lepszego rodzica",summary["improved"]],
        ["Remisy względem lepszego rodzica",summary["tied"]],["Potomkowie gorsi",summary["worse"]]])
    text += ["Identyfikator rodowodu jest hashem genotypu. Duplikaty genotypów mają ten sam identyfikator; "
        "indeks w populacji rozróżnia osobniki. Statystyki potomstwa opisują zaobserwowane operacje; "
        "same nie dowodzą przyczynowego wpływu pojedynczej mutacji lub krzyżowania.", ""]
    for figure in figures:
        text += [f"### {figure['title']}","",f"![{figure['title']}](genetic_analysis/{figure['file']})","",figure["caption"],""]
    if groups:
        text += table(["Wariant","Powtórzenia","Śr. końcowy fitness treningowy","Śr. obrażenia testowe"],[
            [name,len(cases),f"{statistics.mean(r['final_fitness'] for r in cases):.5f}",
             f"{statistics.mean(r['test_damage'] for r in cases):.3f}"] for name,cases in groups.items()])
    text += ["### Porównanie z rozmieszczeniem losowym i regułami", "",
        f"RANDOM obejmuje {analysis['random']['layout_count']} niezależnych losowych planów, każdy oceniony na "
        f"{len(settings['test_seeds'])} tych samych scenariuszach: razem {len(analysis['random']['episodes'])} prób. "
        "Losujemy typy i różne pola budowy, a wszystkie sloty są dostępne od t=0. Późniejsze zakupy "
        "nadal wymagają funduszy. Pozostałe strategie mają po jednym planie i po jednej próbie na scenariusz. "
        "Odchylenie RANDOM obejmuje zmienność układów i scenariuszy; nie jest błędem standardowym średniej.",""]
    text += table(["Strategia","Śr. obrażenia","Śr. HP bazy","Śr. zabicia","Zatrzymane [%]","Śr. wydatek","Zabicia / 100 środków"],[
        [r["strategy"],f"{r['damage']:.3f}",f"{r['base_hp']:.2f}",f"{r['kills']:.2f}",
         f"{100*r['kill_fraction']:.2f}",f"{r['money_spent']:.2f}",f"{r['kills_per_100_money']:.2f}"] for r in benchmark])
    text += ["Pełne źródła: genetic_analysis/population_seed_*.jsonl, populations.csv, offspring.csv, "
        "operators.csv i random_benchmark.json. " + ("Dostępne są też osobne ablation_*.json. " if groups else "") + "Pliki zawierają surowe pomiary, "
        "maski pochodzenia wszystkich genów i zmiany przed/po każdej próbie mutacji.",""]
    (folder/"analysis_report.md").write_text("\n".join(text),encoding="utf-8")
    print(f"Generated {len(figures)} genetic figures and full data appendix in {folder}")
    return summary


def math_ceil_half(value):
    return (value+1)//2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("training_results/report.json"))
    args=parser.parse_args()
    render(args.input)


if __name__=="__main__":
    main()
