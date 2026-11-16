"""Nine-page course report; the full telemetry stays in the separate analytical appendix."""
import argparse
import html
import importlib.metadata
import json
import statistics
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, Preformatted, Spacer, Table, TableStyle

from src.genetic_ai import Strategy
from src.simulation import Simulation
from src.pdf_report import ReportDocument, register_fonts


def build(source_path, target):
    source=json.loads(source_path.read_text(encoding="utf-8"))
    root=Path(__file__).resolve().parents[2]
    metadata=json.loads((root/"project_metadata.json").read_text(encoding="utf-8"))
    output=source_path.parent
    folder=output/"genetic_analysis"
    analysis=json.loads((folder/"analysis.json").read_text(encoding="utf-8"))
    summary=json.loads((folder/"figure_summary.json").read_text(encoding="utf-8"))
    details=json.loads((output/"detailed_report.json").read_text(encoding="utf-8"))
    settings,config=source["settings"],source["config"]
    geometry=Simulation(config,source["map"])
    winner=next(r for r in analysis["runs"] if r["seed"]==settings["seed"])
    register_fonts()
    width=A4[0]-80
    body=ParagraphStyle("CourseBody",fontName="Report",fontSize=9,leading=12.5,spaceAfter=6,textColor=colors.HexColor("#26364b"))
    heading=ParagraphStyle("Heading1",fontName="ReportBold",fontSize=16,leading=20,spaceAfter=10,textColor=colors.HexColor("#152e4f"),keepWithNext=True)
    small=ParagraphStyle("CourseSmall",parent=body,fontSize=7.5,leading=10,spaceAfter=5)
    cell=ParagraphStyle("CourseCell",parent=small,fontSize=7.2,leading=9.5)
    caption=ParagraphStyle("CourseCaption",parent=small,alignment=1)
    title=ParagraphStyle("CourseTitle",parent=heading,fontSize=22,leading=27,spaceAfter=12)
    story=[]
    def paragraph(text,style=body):
        story.append(Paragraph(text,style))
    def section(text):
        paragraph(text,heading)
    def page(text):
        story.append(PageBreak())
        section(text)
    def table(headers,rows,widths=None):
        content=[[Paragraph(f"<b>{html.escape(str(v))}</b>",cell) for v in headers]]
        content += [[Paragraph(html.escape(str(v)),cell) for v in row] for row in rows]
        result=Table(content,colWidths=[width*w for w in widths] if widths else None,repeatRows=1,hAlign="LEFT")
        result.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dce9f5")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7fa")]),
            ("GRID",(0,0),(-1,-1),.3,colors.HexColor("#cbd5e1")),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        story.extend([result,Spacer(1,7)])
    def figure(path,label,max_height=260):
        with PILImage.open(path) as image:
            buffer=BytesIO()
            image.convert("RGB").save(buffer,format="PNG")
            buffer.seek(0)
            scale=min(width/image.width,max_height/image.height)
            story.append(KeepTogether([Image(buffer,width=image.width*scale,height=image.height*scale),
                Spacer(1,3),Paragraph(label,caption),Spacer(1,5)]))

    paragraph("KITTYCATCH · PROJEKT 4",small)
    paragraph("Tower defense — optymalizacja rozmieszczenia obrony",title)
    paragraph(metadata["course"]+" · "+metadata["schedule"],small)
    team=str(metadata["team_number"]) if metadata.get("team_number") is not None else "do uzupełnienia"
    paragraph(f"<b>Numer zespołu:</b> {team}",small)
    table(["Autor","Potwierdzony podział pracy"],[[a["name"],a["responsibility"]] for a in metadata["authors"]],[.38,.62])
    section("1. Cel, założenia i architektura")
    paragraph("Celem jest automatyczny dobór typu, położenia i czasu budowy wież przy ograniczonym budżecie. "
        "AI broni bazy, a gracz wysyła gołębie. Rozwiązanie oceniono względem losowych planów i prostych reguł "
        "pokrycia trasy. To własna implementacja algorytmu genetycznego, z lokalnym modelem walki i integracją z Godotem.")
    paragraph(f"Założenia eksperymentu: mapa {geometry.width}×{geometry.height}, baza {config['base']['health']} HP, początkowy budżet AI "
        f"{config['economy']['ai']['starting_money']}, do {settings['slots']} wież w planie, epizod {settings['duration']:g} s. "
        "Nagrody za zabicia pozwalają finansować kolejne wieże; limit slotów pozostaje stały.")
    figure(folder/"architecture.png","Architektura: ewolucja offline i ta sama polityka budowania w działającej grze.",220)
    paragraph("Godot wysyła pełne obserwacje init/update przez TCP jako JSON zakończony nową linią. "
        "Python zwraca build_tower z typem i współrzędnymi. Silnik sprawdza koszt i zajętość pola oraz odsyła "
        "action_result. Model czeka na potwierdzenie, odrzuca duplikaty obserwacji i resetuje stan przy nowym epizodzie.")

    page("2. Reprezentacja rozwiązania i funkcja celu")
    paragraph("Chromosom zawiera 40 liczb rzeczywistych w [0,1]: 10 czwórek [typ, x, y, czas]. "
        "Typ jest dyskretyzowany do BASIC lub SNIPER; współrzędne skalujemy do wymiarów mapy, "
        "a czas do długości epizodu. Zajęty lub niebudowalny cel zastępujemy najbliższym wolnym polem. "
        "To naprawa rozwiązania, dzięki której polityka respektuje przestrzeń akcji gry.")
    paragraph("<b>Fitness pojedynczego epizodu:</b> F = −L + 0,1 · K / max(N,1), gdzie L to liczba przecieków, "
        "K — zabite jednostki, N — rzeczywiście wysłane jednostki. Ocena osobnika jest średnią po pięciu falowych "
        "scenariuszach. Chronimy bazę, a udział zabitych rozstrzyga remisy. Górna granica F=0,1 nie oznacza "
        "globalnego optimum wobec dowolnego ataku gracza.")
    data=source["strategy"]
    plan=Strategy(tuple(data["tower_types"]),tuple(data["genes"]),data["duration"]).decode(geometry.width,geometry.height)
    table(["Slot","Typ","x","y","Najwcześniej [s]"],[[p["slot"],p["tower_type"],p["x"],p["y"],f"{p['earliest']:.2f}"] for p in plan],[.12,.28,.12,.12,.36])
    paragraph("Tabela opisuje plan wybranego chromosomu. Slot może pozostać niewykonany, jeśli zabraknie "
        "środków, czasu lub miejsca. Pełne wartości genów zapisano w modele/best_strategy.json oraz "
        "w rozszerzonym raporcie; nie zastępujemy ich samą ilustracją.")
    figure(output/f"layout_seed_{settings['seed']}.png","Przykładowe faktyczne rozmieszczenie; liczby oznaczają kolejność budowy.",235)

    page("3. Algorytm genetyczny i operatory")
    table(["Parametr głównego eksperymentu","Wartość"],[
        ["Populacja / epoki oceny",f"{settings['population']} / {settings['generations']}"],
        ["Ziarna niezależnego wyszukiwania",", ".join(str(r["seed"]) for r in analysis["runs"])],
        ["Selekcja / krzyżowanie","turniej 3 osobników / jednostajne, każdy gen 50:50"],
        ["Mutacja","p=0,15 na gen; szum Gaussa σ=0,15; obcięcie do [0,1]"],
        ["Elitaryzm",f"{max(1,settings['population']//8)} osobniki kopiowane bez zmian"]],[.48,.52])
    paragraph("Populacja początkowa zawiera trzy plany regułowe oraz losowe chromosomy. W każdej epoce "
        "oceniamy populację, kopiujemy elitę i tworzymy potomków z rodziców wybranych turniejowo. "
        "Cache oszczędza ponowną symulację identycznych genotypów. Remisy rozstrzygamy losowo ze stałym ziarnem.")
    paragraph(f"<b>Epoka</b> oznacza ocenę jednej populacji: epoka 1 to inicjalizacja, zatem {settings['generations']} epok obejmuje "
        f"{settings['generations']-1} przejść reprodukcyjnych. Nie jest to trenowanie sieci neuronowej metodą gradientową.")
    figure(folder/"operators_example.png","Rzeczywisty potomek: maska pochodzenia genów i zaznaczone próby mutacji.",260)
    paragraph(f"W wybranym przebiegu zapisano {summary['offspring']} potomków, "
        f"{summary['mutation_attempts']} prób mutacji i {summary['actual_changes']} faktycznych zmian. "
        f"{summary['clipped']} prób przekroczyło granice [0,1]. Przypadek poprawy potomka nie dowodzi, "
        "że odpowiada za nią pojedyncza mutacja — do tego służy osobne badanie ablacyjne.")

    page("4. Rozwój populacji i zbieżność")
    paragraph("Każdy z trzech przebiegów korzysta z tych samych danych treningowych. Różnią się ziarna "
        "losowania inicjalizacji i operatorów. Poprawę jakości oceniamy zarówno przez najlepszy fitness, "
        "jak i zachowanie całej populacji. Elitaryzm chroni najlepsze rozwiązania, ale słabsi potomkowie "
        "mogą nadal powstawać wskutek eksploracji.")
    figure(folder/"fitness_distribution.png","Fitness populacji; niebieskie pasmo przedstawia kwartyle 25–75%.",260)
    figure(folder/"best_runs.png","Najlepszy fitness dla trzech niezależnych przebiegów.",250)
    paragraph("Pierwsze epoki z najlepszym zaobserwowanym wynikiem: "+", ".join(
        f"ziarno {r['seed']} — epoka {r['first_best_epoch']+1}" for r in analysis["runs"])+
        ". Wynik porównujemy z inicjalizacją zawierającą heurystyki; nie przypisujemy całej skuteczności "
        "samemu uczeniu od losowego startu.")

    page("5. Ewolucja chromosomów i różnorodność")
    paragraph("Mapa genów pokazuje wartości 40 pozycji najlepszego osobnika w każdej epoce. "
        "Po osiągnięciu plateau mogą nadal zmieniać się chromosomy o tej samej jakości. "
        "Genotyp jest ciągły, a odkodowane typy, pola i siatka decyzji są dyskretne; dlatego różnorodność "
        "surowych genów nie jest tym samym co różnorodność rzeczywistych planów.")
    figure(folder/"chromosome_evolution.png","Chromosom × epoka: T — typ, x/y — położenie, t — czas; cztery kolumny na slot.",255)
    figure(folder/"diversity_detail.png","Unikalne genotypy, unikalne odkodowane plany i średnie odchylenie wartości genów.",250)
    paragraph("Pełny załącznik obejmuje dodatkowo presję selekcyjną, rozrzut każdego genu, częstość mutacji, "
        "macierz fitness wszystkich osobników, koszt ewaluacji, czas budowy i krzywe trening–test. "
        "Krzywe testowe obliczono po treningu i nie używano ich do wyboru epoki ani chromosomu.")

    page("6. Eksperymenty porównawcze i budżet")
    paragraph(f"Trening używał ziaren {settings['train_seeds']}; test — {len(settings['test_seeds'])} rozłącznych ziaren "
        "i profili SCOUT, TANK, SPEED, MIXED, BURST. Wybrano zwycięzcę według fitness treningowego. "
        f"RANDOM obejmuje {analysis['random']['layout_count']} niezależnych losowych planów, każdy na tych samych "
        f"{len(settings['test_seeds'])} scenariuszach ({len(analysis['random']['episodes'])} prób). "
        "Losujemy różne pola budowy i typy; sloty losowe oraz regułowe są dostępne od t=0. Wszystkie mają ten sam limit wież i ekonomię.")
    included=[r for r in summary["benchmark"] if r["strategy"] in ("GENETIC","BASIC","SNIPER","MIXED","RANDOM","PREVIOUS")]
    table(["Plan","Obrażenia ↓","HP bazy","Zabicia","Zatrzymane [%]","Wydatek","Zab./100 śr."],[
        [r["strategy"],f"{r['damage']:.2f}",f"{r['base_hp']:.2f}",f"{r['kills']:.2f}",
         f"{r['kill_fraction']*100:.1f}",f"{r['money_spent']:.1f}",f"{r['kills_per_100_money']:.2f}"] for r in included],
        [.17,.13,.13,.12,.16,.13,.16])
    figure(folder/"benchmark_damage.png","Średnie obrażenia bazy: GA, heurystyki, poprzedni model i kontrola losowa.",245)
    genetic=next(r for r in included if r["strategy"]=="GENETIC")
    random=next(r for r in included if r["strategy"]=="RANDOM")
    better = [name for name, stats in source['comparison'].items()
              if name != 'GENETIC' and stats['mean_damage'] < genetic['damage']]
    comparison_note = ("Niższą średnią testową uzyskały: " + ", ".join(better) + ". " if better else "")
    paragraph(f"GENETIC uzyskał średnio {genetic['damage']:.2f} obrażeń, RANDOM {random['damage']:.2f}. "
        + comparison_note + "Zwycięzcę wybrano na treningu; test nie służy ponownemu wyborowi modelu. "
        "SD w kontroli losowej zawiera zmienność planów i scenariuszy, nie tylko błąd średniej.")
    paragraph("Wydatki obejmują reinwestowane nagrody i mogą przekroczyć startowe 150. Wskaźnik zabicia/100 "
        "wydanych środków opisuje efektywność, ale nie zastępuje ochrony bazy. Zwroty energii zależą od zabijania "
        "i przecieków, więc rzeczywiste czasy fal mogą różnić się mimo wspólnego harmonogramu żądań.")

    page("7. Ablacje: co wnoszą operatory?")
    groups={name:[r for r in analysis["ablations"] if r["variant"]==name] for name in ("FULL","NO_MUTATION","NO_CROSSOVER","NO_ELITISM")}
    paragraph("Aby zbadać wpływ operatorów, wykonano cztery warianty: pełny GA, bez mutacji, bez krzyżowania "
        "i bez elitaryzmu. Każdy wariant ma trzy powtórzenia o ziarnach 42, 137, 2026, populację 12, "
        "12 epok i te same scenariusze. Jest to mniejszy budżet obliczeniowy niż eksperyment główny; "
        "porównujemy warianty z kontrolą FULL tej samej wielkości.")
    table(["Wariant","Końcowy fitness: średnia ± SD","Śr. obrażenia testowe"],[
        [name,f"{statistics.mean(r['final_fitness'] for r in rows):.5f} ± {statistics.pstdev(r['final_fitness'] for r in rows):.5f}",
         f"{statistics.mean(r['test_damage'] for r in rows):.3f}"] for name,rows in groups.items()],[.31,.40,.29])
    figure(folder/"ablations.png","Zbieżność po wyłączeniu jednego operatora, średnia trzech powtórzeń.",260)
    paragraph("Wyniki dotyczą małej próby i konkretnego problemu. Brak poprawy po usunięciu operatora "
        "lub podobny wynik nie dowodzi jego zbędności w każdym zadaniu. Bez elitaryzmu najlepszy wynik "
        "ostatniej populacji może być gorszy od najlepszego wcześniej zaobserwowanego.")
    paragraph(f"Kontrola FULL: {statistics.mean(r['test_damage'] for r in groups['FULL']):.3f} średnich obrażeń testowych; "
        f"bez mutacji: {statistics.mean(r['test_damage'] for r in groups['NO_MUTATION']):.3f}; "
        f"bez krzyżowania: {statistics.mean(r['test_damage'] for r in groups['NO_CROSSOVER']):.3f}; "
        f"bez elitaryzmu: {statistics.mean(r['test_damage'] for r in groups['NO_ELITISM']):.3f}. "
        "Samo wyłączenie operatora nie zmienia pozostałych parametrów, lecz sekwencje losowych zdarzeń "
        "mogą się różnić. Zgodne ziarna nie oznaczają identycznych populacji po każdej zmianie wariantu.")

    page("8. Silnik, fizyka i próby przeciążeniowe")
    validations=details.get("godot_validation",[])
    cases=[(run,case) for run in validations for case in run["scenarios"]]
    paragraph("Godot realizuje ruch po trasie, strefy kolizji, wybór celu, timery wież oraz pociski "
        "samosterujące o prędkości 400 px/s. Model Python uwzględnia ich czas lotu. Efektywny zasięg "
        "wieży obejmuje skalę sceny 0,4: BASIC 51,2 px, SNIPER 115,2 px; promień gołębia 8 px, "
        "rozrzut trasy ±8 px. Kalibracja usunęła błędne założenie pełnego zasięgu z JSON-a.")
    table(["Tempo","Seed / profil","Model: obraż.","Godot: obraż.","Budowy OK / odrz."],[
        [f"{run['time_scale']:g}×",f"{case['seed']} / {case['profile']}",case["local_damage"],case["godot_damage"],
         f"{case['accepted']} / {case['rejected']}"] for run,case in cases],[.10,.29,.18,.18,.25])
    paragraph("Są to rzeczywiste procesy silnika z prywatnym socketem, nie same odtworzenia symulatora. "
        "Testy 1× kontrolują wpływ przyspieszenia; 4× używa 240 kroków fizyki/s. "
        "Sprawdzone przypadki nie gwarantują identycznego wyniku wobec innych ataków lub na każdym komputerze.")
    figure(output/"stress_test.png","Przeciążenie: średnie obrażenia dla trzech limitów energii i czterech układów.",220)
    paragraph("Próby przeciążeniowe wykonano osobno w Pythonie: początkowa energia równa limitowi 100/300/1000 "
        "zamiast standardowych 40, maksymalna żądana fala, odstęp 0,1 s między jednostkami i dwukrotnie "
        "gęstsze żądania fal. Wraz z limitem rosną możliwości przełamania obrony; nie jest to porównanie "
        "normalnego startu wszystkich poziomów trudności.")

    page("9. Wnioski, ograniczenia i odtwarzalność")
    paragraph("Algorytm skutecznie wyszukuje legalne plany obrony i wyraźnie przewyższa losowe rozmieszczenie "
        "w badanych warunkach. Heurystyki stanowią punkt odniesienia; przewaga w tym eksperymencie nie jest "
        "gwarancją na innych mapach i falach. Telemetria pozwala śledzić jakość, genotypy, presję selekcyjną i mutacje, "
        "zamiast ograniczać analizę do końcowego zwycięzcy.")
    paragraph("<b>Ograniczenia:</b> jedna mapa, pięć automatycznych profili fal, skończona liczba ziaren i limit "
        "10 slotów. Geny czasów są powiązane z horyzontem epizodu. Symulacja przybliża kolejność zdarzeń, "
        "kolizje i opóźnienia sieci. Nie implementowano wyprzedzania celu ani przeszkód blokujących ostrzał; "
        "samosterujące pociski i silnik stanowią zrealizowane rozszerzenia fizyczne i integracyjne.")
    paragraph("<b>Dalszy rozwój:</b> więcej map i przeciwników adaptacyjnych, więcej powtórzeń ablacji, "
        "walidacja w silniku także dużych fal, predykcja punktu przechwycenia, test widoczności oraz "
        "optymalizacja wielokryterialna ochrony bazy i wydatków.")
    paragraph("<b>Środowisko i wykorzystane narzędzia:</b> Python "+sys.version.split()[0]+", Godot 4.7.2; "
        f"Pillow {importlib.metadata.version('Pillow')} do figur i GIF, ReportLab {importlib.metadata.version('reportlab')} "
        "do PDF, biblioteka standardowa do GA, socketów i JSON. PyMuPDF służy kontroli gotowego PDF. "
        "Nie używano gotowej biblioteki optymalizacji ewolucyjnej. Koncepcja GA jest klasyczną metodą; "
        "własny wkład obejmuje reprezentację planu, ocenę w symulatorze, politykę, integrację i eksperymenty.")
    paragraph("<b>Uruchomienie od zera</b> (Python 3.14, początkowo z katalogu głównego paczki; Godot uruchamiany osobno):")
    code="python -m pip install -r uruchomienie/wymagania.txt\n# PowerShell:\nSet-Location kod/python_ai\npython -m src.serwer --strategy ../../modele/best_strategy.json\n# Otworz kod/godot_game/project.godot w Godocie i nacisnij F5.\n# Przyklad lokalny bez treningu:\npython train.py --strategy ../../modele/best_strategy.json --duration 120 --output ../../wyniki/ocena"
    story.append(Preformatted(code,ParagraphStyle("CourseCode",fontName="Report",fontSize=7.5,leading=10,spaceAfter=8),maxLineLength=105))
    paragraph("<b>Materiały:</b> README repozytorium opisuje zależności, konfigurację i komendy odtworzenia. "
        "modele/ zawiera gotowy chromosom i migawki reguł/mapy. wyniki/ zawiera obszerny raport, "
        "surowe populacje JSONL, maski krzyżowania, mutacje, CSV, figury, wyniki silnika i animacje. "
        "Numery losowań i hash konfiguracji umożliwiają identyfikację eksperymentu.")
    paragraph("<b>Repozytorium:</b> "+metadata["repository"]+". "
        "Podział pracy: Aleksander Kopyto — algorytm genetyczny i AI; Kacper Mazurek — gra. "
        "Wykorzystano wymagania z plików kursu: „Instrukcja oddania projektu.pdf” oraz "
        "„01 Sztuczna inteligencja w grach i rozszerzonej rzeczywistości.docx”. "
        "Numer zespołu należy uzupełnić w project_metadata.json przed oddaniem.",small)
    def footer(canvas,doc):
        canvas.setFont("Report",8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(40,25,"KittyCatch · Projekt 4 · Aleksander Kopyto, Kacper Mazurek")
        canvas.drawRightString(A4[0]-40,25,str(doc.page))
    doc=ReportDocument(str(target),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=40,
        title=metadata["title"],author=", ".join(a["name"] for a in metadata["authors"]))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(f"Course report: {target.resolve()}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("training_results/report.json"))
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    build(args.input,args.output or args.input.parent/"sprawozdanie.pdf")


if __name__=="__main__":
    main()
