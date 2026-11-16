"""Plain-language companion to the actual presentation, with worked examples."""
import argparse
import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from src.genetic_ai import GeneticAgent, Strategy, init_message
from src.pdf_report import ReportDocument, register_fonts
from src.simulation import Simulation


class Guide:
    def __init__(self):
        register_fonts()
        self.story=[]
        self.markdown=[]
        self.width=A4[0]-84
        self.body=ParagraphStyle("GuideBody",fontName="Report",fontSize=10.7,leading=15,spaceAfter=7,textColor=colors.HexColor("#243b55"))
        self.h1=ParagraphStyle("Heading1",fontName="ReportBold",fontSize=18,leading=23,spaceAfter=12,
            textColor=colors.HexColor("#132b49"),keepWithNext=True)
        self.h2=ParagraphStyle("Heading2",parent=self.h1,fontSize=12.5,leading=17,spaceBefore=8,spaceAfter=6)
        self.cell=ParagraphStyle("GuideCell",parent=self.body,fontSize=9.5,leading=13,spaceAfter=0)

    def p(self,text):
        self.story.append(Paragraph(text,self.body))
        self.markdown.extend([re.sub(r"</?b>","**",text),""])

    def heading(self,text):
        self.story.append(Paragraph(html.escape(text),self.h2))
        self.markdown.extend(["## "+text,""])

    def page(self,title):
        if self.story:self.story.append(PageBreak())
        self.story.append(Paragraph(html.escape(title),self.h1))
        self.markdown.extend(["# "+title,""])

    def say(self,text,label="Możesz powiedzieć"):
        paragraph=Paragraph(f"<b>{html.escape(label)}:</b> {text}",self.body)
        box=Table([[paragraph]],colWidths=[self.width])
        box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#e9f5f3")),
            ("LINEBEFORE",(0,0),(0,-1),3,colors.HexColor("#008f85")),
            ("LEFTPADDING",(0,0),(-1,-1),11),("RIGHTPADDING",(0,0),(-1,-1),11),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
        self.story.extend([box,Spacer(1,8)])
        self.markdown.extend([f"> **{label}:** "+re.sub(r"</?b>","**",text),""])

    def table(self,headers,rows,widths):
        values=[[Paragraph(f"<b>{html.escape(str(v))}</b>",self.cell) for v in headers]]
        values += [[Paragraph(html.escape(str(v)),self.cell) for v in row] for row in rows]
        result=Table(values,colWidths=[self.width*w for w in widths],repeatRows=1,hAlign="LEFT")
        result.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dce9f5")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7fa")]),
            ("GRID",(0,0),(-1,-1),.3,colors.HexColor("#ccd8e4")),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        self.story.extend([result,Spacer(1,9)])
        self.markdown += ["| "+" | ".join(headers)+" |","| "+" | ".join("---" for _ in headers)+" |"]
        self.markdown += ["| "+" | ".join(str(v) for v in row)+" |" for row in rows]
        self.markdown.append("")

    def card(self,number,title,meaning,numbers,speech):
        self.heading(f"Slajd {number}. {title}")
        self.p("<b>O co chodzi?</b> "+meaning)
        self.p("<b>Jak wyjaśnić liczby i rysunek?</b> "+numbers)
        self.say(speech)

    def save(self,path):
        def footer(canvas,doc):
            canvas.setFont("Report",8)
            canvas.setFillColor(colors.HexColor("#62758a"))
            canvas.drawString(42,25,"KittyCatch · pomoc do prezentacji · pojęcia i liczby prostym językiem")
            canvas.drawRightString(A4[0]-42,25,str(doc.page))
        doc=ReportDocument(str(path),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=40,
            title="KittyCatch — jak wyjaśnić prezentację",author="Materiały pomocnicze do projektu KittyCatch")
        doc.build(self.story,onFirstPage=footer,onLaterPages=footer)
        path.with_suffix(".md").write_text("\n".join(self.markdown),encoding="utf-8")


def build(source_path):
    folder=source_path.parent
    source=json.loads(source_path.read_text(encoding="utf-8"))
    manifest=json.loads((folder/"presentation_manifest.json").read_text(encoding="utf-8"))
    analysis=json.loads((folder/"genetic_analysis/analysis.json").read_text(encoding="utf-8"))
    example=json.loads((folder/"genetic_analysis/operator_example.json").read_text(encoding="utf-8"))
    summary=json.loads((folder/"genetic_analysis/figure_summary.json").read_text(encoding="utf-8"))
    data=source["strategy"]
    strategy=Strategy(tuple(data["tower_types"]),tuple(data["genes"]),data["duration"])
    sim=Simulation(source["config"],source["map"])
    agent=GeneticAgent(strategy)
    agent(init_message(sim))
    first_action=agent(sim.to_dict())
    first_plan=next(p for p in strategy.decode(sim.width,sim.height) if p["slot"]==0)
    winner=next(r for r in analysis["runs"] if r["seed"]==source["settings"]["seed"])
    records=[json.loads(line) for line in (folder/"genetic_analysis"/winner["telemetry"]).read_text(encoding="utf-8").splitlines()]
    birth=example["birth"]
    parents={p["id"]:p["genes"] for p in records[example["epoch"]-2]["population"]}
    mutation=next(m for m in birth["mutations"] if m["gene"]==5)
    g=Guide()

    g.page("Ściąga: o co chodzi w naszym projekcie?")
    g.p("Ten PDF służy do zrozumienia prezentacji, a nie do zapamiętywania wszystkich cyfr. "
        "Najpierw przeczytaj tę stronę oraz wyjaśnienie krzyżowania, mutacji i fitness. "
        "Dalej znajdziesz krótkie odpowiedzi dopasowane do wszystkich 18 slajdów.")
    g.say("Porównujemy wiele planów obrony. Sprawdzamy je w grze, wybieramy lepsze, mieszamy ich "
        "instrukcje i wprowadzamy niewielkie losowe zmiany. Tak tworzymy kolejne propozycje ustawienia wież.","Cały algorytm w jednym zdaniu")
    g.table(["Słowo","Znaczenie w naszym projekcie"],[
        ["Osobnik","Jeden kompletny plan obrony, nie jeden gołąb i nie jedna wieża."],
        ["Chromosom","Zapis tego planu: 40 liczb."],
        ["Gen","Jedna liczba, np. współrzędna x jednej planowanej wieży."],
        ["Fitness","Ocena jakości planu po rozegraniu scenariuszy. Wyższa jest lepsza."],
        ["Krzyżowanie","Złożenie nowego planu z genów dwóch wybranych planów."],
        ["Mutacja","Losowa zmiana niektórych liczb w nowym planie."],
        ["Epoka / pokolenie","Jedna ocena całej populacji planów."],
        ["Elita","Najlepsze plany przeniesione dalej bez zmian."]],[.26,.74])
    g.heading("Trzy rzeczy, które musisz pamiętać")
    g.p("<b>1.</b> AI stawia wieże, a gracz wysyła gołębie. <b>2.</b> Nie używamy sieci neuronowej: "
        "szukamy dobrego planu metodą ewolucyjną. <b>3.</b> Nie twierdzimy, że znaleźliśmy najlepszą "
        "możliwą strategię. Znaleźliśmy skuteczne rozwiązanie w sprawdzonych warunkach.")
    g.p("W razie pośpiechu naucz się powiedzieć własnymi słowami: czym jest jeden osobnik, "
        "jak działa krzyżowanie, czym różni się od mutacji i dlaczego mniejsze obrażenia bazy są lepsze.")

    g.page("Słownik: nie myl tych pojęć")
    g.table(["Pojęcie","Proste wyjaśnienie"],[
        ["Populacja","Cała grupa rozpatrywanych planów. U nas 24 osobniki naraz."],
        ["Rodzic / potomek","Rodzic to wybrany istniejący plan. Potomek to nowy plan utworzony z rodziców."],
        ["Genotyp","Surowe liczby chromosomu, np. 0,406 jako gen x."],
        ["Fenotyp / plan po dekodowaniu","Znaczenie tych liczb: np. BASIC na polu (8,7), dostępny od 0 s."],
        ["Dekodowanie","Przeliczenie liczb [0,1] na typ, pole mapy i sekundy."],
        ["Naprawa rozwiązania","Jeżeli cel jest zajęty lub niedozwolony, wybieramy najbliższe legalne wolne pole."],
        ["Scenariusz","Cały epizod 120 s z wieloma falami. To nie jest pojedynczy gołąb ani jedna fala."],
        ["Przebieg treningu","Całe wyszukiwanie przez 24 epoki. Wykonaliśmy 3 przebiegi."],
        ["Ziarno losowania (seed)","Numer ustawiający generator losowy. Przy tej samej konfiguracji pozwala odtworzyć losowania; nie jest oceną jakości."],
        ["Heurystyka / strategia regułowa","Ręczna reguła, np. ustawiaj wieże tam, gdzie dobrze pokrywają trasę."],
        ["Baseline","Punkt odniesienia: losowanie albo prosta reguła, z którą porównujemy GA."],
        ["Generalizacja","Działanie na scenariuszach, które nie wybierały rozwiązań podczas treningu."]],[.30,.70])
    g.say("Osobnik nie oznacza jednostki w grze. Osobnikiem algorytmu jest cały plan ustawienia obrony. "
        "Wieże i gołębie to elementy symulacji, na której ten plan oceniamy.")

    g.page("Krzyżowanie: mieszamy instrukcje rodziców")
    g.p("Wyobraź sobie dwie instrukcje ustawienia obrony. Jedna dobrze rozmieściła pierwsze wieże, "
        "a druga może mieć użyteczne inne położenia lub czasy. Tworzymy nową instrukcję, biorąc "
        "poszczególne liczby z jednej albo z drugiej. Dopiero potem sprawdzamy, czy nowy plan jest dobry.")
    g.p("U nas jest <b>krzyżowanie jednostajne</b>: dla każdego genu losujemy, czy przepisujemy go "
        "od rodzica A, czy B. Każdy ma szansę 50%. To nie jest średnia dwóch liczb. "
        "Jeżeli rodzice mają 0,2 i 0,8, krzyżowanie wybierze 0,2 albo 0,8; samo nie wyliczy 0,5.")
    rows=[]
    for label,values in [("Rodzic A",parents[birth["parent_ids"][0]]),("Rodzic B",parents[birth["parent_ids"][1]]),
                         ("Po krzyżowaniu",birth["before_mutation"]),("Po mutacji",birth["genes"])]:
        rows.append([label]+[f"{v:.2f}" for v in values[:8]])
    g.table(["Wiersz"]+[str(i) for i in range(8)],rows,[.24]+[.095]*8)
    g.p("To dokładnie wycinek ze slajdu 7. Kolumny 0–3 opisują jeden slot, 4–7 następny. "
        "W pierwszych trzech kolumnach wybór padł na A, w kolumnach 3–6 na B, a w kolumnie 7 na A. "
        "Kolumna 5 zmieniła się dodatkowo przez mutację: około 0,42 → 0,25.")
    g.p("<b>Dlaczego to może pomóc?</b> Łączymy elementy już ocenionych rozwiązań, zamiast za każdym "
        "razem losować wszystko od zera. Nie ma gwarancji poprawy: niepasujące elementy mogą stworzyć "
        "gorszy plan. Dlatego każdy potomek znowu trafia do symulacji.")
    g.say("Dla każdego genu rzucamy umowną monetą: bierzemy wartość z rodzica A albo B. "
        "Nowy plan może więc połączyć różne elementy obrony. Dopiero symulacja mówi nam, czy to połączenie zadziałało.")

    g.page("Mutacja: małe losowe poprawki, nie mieszanie")
    g.p("<b>Krzyżowanie</b> przepisuje istniejące liczby rodziców. <b>Mutacja</b> zmienia wybraną liczbę. "
        "Dzięki temu algorytm może sprawdzić wartość, której nie miał żaden z rodziców, np. przesunąć "
        "cel wieży albo zmienić najwcześniejszy moment zakupu.")
    g.table(["Zapis na slajdzie","Co to oznacza"],[
        ["p = 15% = 0,15","Każdy gen potomka ma 15% szansy na próbę mutacji. Nie chodzi o 15% wież ani o szansę wygranej."],
        ["40 × 0,15 = 6","Średnio 6 prób mutacji na potomka. W konkretnym potomku może ich być mniej lub więcej."],
        ["σ = 0,15","Skala dodawanego szumu. To inny parametr niż prawdopodobieństwo mutacji, choć ma tę samą wartość liczbową."],
        ["N(0; 0,15²)","Losowa poprawka ma średnią 0 i odchylenie standardowe 0,15. Częstsze są małe poprawki; duże też są możliwe."],
        ["Obcięcie do [0,1]","Wynik poniżej 0 zamieniamy na 0, a powyżej 1 na 1."]],[.28,.72])
    g.p(f"<b>Rzeczywisty przykład ze slajdu 7:</b> gen 5 miał {mutation['before']:.5f}. "
        f"Dodano {mutation['noise']:+.5f}, więc otrzymano {mutation['after']:.5f}. "
        "Po zaokrągleniu na slajdzie widać po prostu 0,42 → 0,25. To gen x drugiego slotu, "
        "więc zmienił się cel położenia tej wieży.")
    g.p("Jeśli gen miał 0, a losowa poprawka wyniosła −0,1, po obcięciu nadal ma 0. "
        "Dlatego liczba <b>prób mutacji</b> może być większa niż liczba <b>faktycznie zmienionych genów</b>. "
        "Mutacja nie musi poprawiać fitness — umożliwia eksplorację.")
    g.say("Mutacja wprowadza nowe wartości przez niewielkie losowe zmiany. "
        "Prawdopodobieństwo 15% mówi, czy ruszamy gen, a sigma 0,15 mówi, jak duża może być poprawka.")

    g.page("Fitness: jak czytać minusy i ułamki?")
    g.say("F = −L + 0,1 × K / max(N,1)","Wzór z prezentacji")
    g.p("<b>L</b> to liczba gołębi, które dotarły do bazy. <b>K</b> to zabite jednostki. "
        "<b>N</b> to jednostki, które faktycznie pojawiły się na trasie. Nie liczymy tu samych "
        "zamówień czekających w kolejce. max(N,1) zabezpiecza przed dzieleniem przez zero.")
    g.table(["Przykład","Obliczenie","Fitness"],[
        ["0 przecieków, 10 zabitych z 10","0 + 0,1 × 10/10","0,10"],
        ["0 przecieków, 8 zabitych z 10","0 + 0,1 × 8/10","0,08"],
        ["1 przeciek, 9 zabitych z 10","−1 + 0,1 × 9/10","−0,91"],
        ["2 przecieki, 8 zabitych z 10","−2 + 0,1 × 8/10","−1,92"]],[.44,.36,.20])
    g.p("<b>Więcej znaczy lepiej:</b> 0,10 jest lepsze od 0,08, a −0,5 lepsze od −9,5. "
        "Minus nie jest błędem programu — to kara za przecieki. Niewielka premia za zabicia pomaga "
        "rozróżnić obrony o tej samej liczbie przecieków.")
    g.p("Powyższy wzór ocenia <b>jeden scenariusz</b>. W treningu puszczamy plan na pięciu "
        "scenariuszach i bierzemy średnią. Przykładowo wyniki 0,1; 0,1; −0,9; 0,1; 0,1 dają średnio −0,1. "
        "Dobre działanie na czterech przypadkach nie usuwa kary za piąty.")
    g.heading("Dlaczego ΔF może wynosić +9,029, skoro maksimum to 0,1?")
    g.p(f"Δ oznacza <b>zmianę</b>, nie końcowy wynik. Lepszy rodzic miał {birth['parent_best_fitness']:.3f}, "
        f"a potomek {birth['fitness']:.3f}. Różnica to {birth['fitness']:.3f} − "
        f"({birth['parent_best_fitness']:.3f}) = {birth['fitness_delta_vs_parent']:+.3f}. "
        "Potomek bardzo się poprawił, ale nadal miał ujemny wynik. Nie przekroczył maksimum fitness.")
    g.say("Najpierw karzemy za dotarcie gołębi do bazy. Mała premia za zabicia rozstrzyga remisy. "
        "Oceniamy cały plan na kilku scenariuszach, więc nie opieramy się na jednej szczęśliwej rozgrywce.")

    titles={s["slide"]:s["title"] for s in manifest["slides"]}
    cards={
    1:("Przedstawiamy grę oraz sposób automatycznego planowania obrony.",
       "Nie trzeba tu tłumaczyć żadnego wzoru. Najważniejszy jest podział ról: gracz wysyła gołębie, a AI buduje.",
       "Zrobiliśmy grę, w której algorytm genetyczny szuka planu ustawienia wież. Pokażemy, jak taki plan zapisujemy, oceniamy i uruchamiamy w Godocie."),
    2:("Dobry plan musi zmieścić zakupy w aktualnych środkach. Nie może po prostu kupić wszystkich wież od razu.",
       "200 to początkowe HP bazy. 150 to początkowe środki AI. 10 slotów to do 10 zaplanowanych wież. BASIC kosztuje 50, SNIPER 80; zabicia finansują dalsze zakupy.",
       "AI zaczyna ze 150 środkami, a kolejne zdobywa za zabite jednostki. Dlatego optymalizujemy nie tylko miejsca wież, ale też ich typ i czas zakupu."),
    3:("Polityka to reguła podejmowania decyzji. Ta sama polityka używa planu w lokalnym modelu i w prawdziwym silniku.",
       "TCP jest kanałem komunikacji. JSON to tekstowy zapis danych. Godot jest klientem, Python serwerem. init przekazuje reguły, update aktualny stan, build_tower żąda budowy, action_result potwierdza jej wynik.",
       "Godot odpowiada za rozgrywkę i fizykę. Python dostaje stan, wybiera zakup i odsyła komendę. Godot sprawdza, czy jest legalna. Symulator służy do szybszego oceniania kandydatów podczas treningu."),
    4:("Jedna czwórka liczb opisuje jeden slot: typ, x, y i najwcześniejszy czas. Dziesięć czwórek daje 40 genów.",
       f"Pierwsze wartości to {data['genes'][0]:.3f}, {data['genes'][1]:.3f}, {data['genes'][2]:.3f}, 0. Typ poniżej 0,5 oznacza BASIC. x: {data['genes'][1]:.3f} × 19 ≈ {data['genes'][1]*19:.2f} → 8. y: {data['genes'][2]:.3f} × 14 ≈ {data['genes'][2]*14:.2f} → 7. Czas: 0 × 120 = 0 s. To cel przed naprawą; pierwsza legalna akcja trafia na ({first_action['x']},{first_action['y']}).",
       "Zamiast przechowywać osobno wiele instrukcji, zapisujemy plan jako liczby od zera do jednego. Dekodujemy je na wieże i pola. Nielegalne pole naprawiamy, a na zakup czekamy, jeśli brakuje pieniędzy."),
    5:("Fitness jest oceną, która pozwala uporządkować plany od lepszych do gorszych.",
       "Wykresy fitness czytamy: wyżej = lepiej. W tabelach obrażeń czytamy odwrotnie: mniej = lepiej. 0,1 we wzorze to mała waga premii, nie 10% szansy na wygraną.",
       "Najważniejsze jest nie dopuścić gołębi do bazy. Za to dostajemy ocenę bliską zeru, a maksymalnie 0,1, jeśli zatrzymamy wszystkie wysłane jednostki."),
    6:("Po ocenieniu planów tworzymy kolejną populację z lepszych rodziców i nowych propozycji.",
       "24 = liczba planów naraz. 5 = scenariusze do oceny jednego planu. Turniej 3 = losujemy trzy plany i wybieramy najlepszy. Robimy dwa turnieje, by wybrać rodziców. 3 elity kopiujemy, 21 nowych potomków tworzymy. 24 epoki zawierają 23 reprodukcje.",
       "Z populacji wybieramy rodziców przez małe turnieje. Mieszamy geny, mutujemy niektóre wartości i tworzymy nową populację. Najlepsze trzy plany przenosimy bez zmian, żeby ich nie zgubić."),
    7:("Kolorowe paski pokazują pochodzenie wartości genu; czerwone pole oznacza próbę mutacji.",
       "Na slajdzie widać tylko 8 z 40 genów, żeby dało się je przeczytać. Pierwszy fragment wziął część liczb od A, część od B. Gen 5 po skopiowaniu z B zmienił się z około 0,42 na 0,25. ΔF to poprawa względem lepszego rodzica, nie nowa wartość fitness.",
       "W tym przykładzie nowy plan kopiuje różne geny rodziców, a potem zmienia jeden z pokazanych genów przez mutację. Nie zakładamy, że sam fakt mutacji daje poprawę — nowy plan trzeba jeszcze przetestować."),
    8:("Oddzielamy dane, na których wybieramy plany, od danych używanych do późniejszego sprawdzenia jakości.",
       "3 × 24 × 24 = 1728 zapisów osobników: trzy przebiegi, 24 epoki i 24 plany w populacji. To nie 1728 osobnych meczów, bo ocenę planu liczymy po kilku scenariuszach, a część ocen korzysta z cache. 20 losowych planów × 20 scenariuszy = 400 prób kontroli losowej.",
       "Każdy plan oceniamy na pięciu scenariuszach treningowych. Zwycięzcę sprawdzamy na dwudziestu innych. Dodatkowo porównujemy go z losowaniem i prostymi regułami, żeby wiedzieć, czy algorytm wnosi coś więcej."),
    9:("Oś pozioma pokazuje kolejne epoki oceny, pionowa najlepszy fitness w danej populacji.",
       "42, 137 i 2026 to ziarna losowania, a nie liczby epok. Dla tych ziaren najlepszy zaobserwowany wynik pojawił się odpowiednio w epoce 5, 3 i 4. Płaska linia oznacza brak poprawy tej oceny, nie zatrzymanie wykonywania algorytmu.",
       "W tych próbach najlepsze wyniki pojawiły się dość wcześnie. Późniejsze epoki nadal sprawdzały inne plany, ale nie poprawiły najlepszego wyniku. Nie jest to dowód, że pięć epok wystarczy zawsze."),
    10:("Plateau to wypłaszczenie wyniku. Geny mogą się zmieniać, mimo że plan ma tę samą jakość.",
        "Wiersz mapy = epoka, kolumna = pozycja genu. Kolor oznacza liczbę w [0,1], nie stopień uszkodzenia wieży. T, x, y, t to cztery pola slotu. Przykładowo 0,20 i 0,30 nadal mogą oznaczać BASIC, więc zmiana genu nie musi zmienić decyzji.",
        "Widzimy różne chromosomy, które osiągają podobne wyniki. To normalne: więcej niż jeden plan może skutecznie bronić tej samej trasy."),
    11:("Słupki przedstawiają średnie obrażenia bazy po epizodzie. Tutaj krótszy słupek jest lepszy.",
        "GENETIC 0,10 = łącznie 2 przecieki w 20 próbach. BASIC 0,05 = 1 w 20. To średnie, nie ułamki obrażenia zadawanego przez gołębia. RANDOM 31,96 to średnia z 400 prób. PREVIOUS to stary plan oceniony teraz na aktualnych zasadach, a NO_DEFENSE nie buduje wież.",
        "GA jest dużo skuteczniejsze od losowego rozmieszczenia. Jednocześnie prosta heurystyka BASIC miała tu minimalnie mniej przecieków, więc nie twierdzimy, że GA zawsze wygrywa z każdą regułą."),
    12:("Ablacja to doświadczenie: wyłączamy jeden element metody i sprawdzamy, co się zmieni.",
        "FULL = komplet operatorów. NO_MUTATION = bez mutacji. NO_CROSSOVER = bez krzyżowania. NO_ELITISM = bez kopiowania elity. Każdy wariant ma 3 ziarna, populację 12 i 12 epok. To mniejszy eksperyment niż główny 24 × 24; porównujemy warianty między sobą.",
        "Osobno sprawdziliśmy, co się dzieje po wyłączeniu każdego operatora. W tak małym badaniu wyniki są podobne, a bez elitaryzmu najlepszy wynik może się cofać. Nie wyciągamy z tego ogólnej tezy, że jakiś operator jest zawsze niepotrzebny."),
    13:("Test w prawdziwym silniku sprawdza, czy założenia modelu i komunikacja działają w rzeczywistej grze.",
        "7 to liczba przebiegów Godota: 5 profili i 2 dodatkowe kontrole w tempie 1×. To nie siedem różnych map. Zero oznacza brak obrażeń i odrzuceń budowy w tych konkretnych próbach. BASIC: 2 kafle × 64 px × skala 0,4 = 51,2 px. To promień fizycznego zasięgu.",
        "Znaleźliśmy różnicę pomiędzy modelem a silnikiem: skala wieży zmniejszała też jej zasięg. Dopasowaliśmy symulator do rzeczywistej fizyki i powtórzyliśmy trening. Potem sprawdziliśmy nowy plan przez prawdziwy socket."),
    14:("Pokazujemy decyzje gotowego modelu. Podczas tej demonstracji nie wykonujemy od nowa treningu.",
        "Gołębie wysyłamy ręcznie w grze, a AI kupuje wieże zgodnie z zapisanym planem i aktualnymi środkami. GIF jest zapasowym pokazem pozycji odebranych z realnego Godota. Nie jest nagraniem kamerki silnika ani tylko prognozą symulatora.",
        "Teraz wysyłamy falę gracza. AI obserwuje stan i odsyła komendy budowy. Widać, jak wydaje środki i jak zabicia finansują kolejne wieże."),
    15:("Podsumowujemy osiągnięcia, ale również granice eksperymentu.",
        "Sprawdziliśmy jedną mapę i wybrane profile ataku. Dobry wynik w tych testach nie dowodzi odporności na dowolny pomysł człowieka. Mówimy o skutecznym sprawdzonym planie, a nie o gwarantowanym optimum.",
        "Algorytm znalazł skuteczną obronę i działa razem z silnikiem. Dobra reprezentacja i trafna symulacja były równie ważne jak same operatory. Następny krok to więcej map i silniejsi przeciwnicy."),
    16:("To slajd zapasowy o możliwościach przełamania obrony dużą zgromadzoną falą.",
        "100, 300 i 1000 to limity energii dla trudnego, średniego i łatwego. W tej próbie od razu napełniliśmy zapas do limitu zamiast zaczynać od 40. Gołębie wysyłaliśmy co 0,1 s i skróciliśmy odstępy żądań fal. Kolory komórek to średnie obrażenia bazy.",
        "Sprawdziliśmy też przeciążenie obrony dużymi falami. To celowo trudniejsze warunki dla AI, z pełnym początkowym zapasem energii. Nie są one tym samym co zwykły początek każdego poziomu trudności."),
    17:("Ten slajd zawiera odpowiedzi na typowe pytania, nie nowy eksperyment.",
        "GA różni się od czystego losowania tym, że ocena wpływa na wybór rodziców i zachowanie dobrych planów. Naprawa oraz warunki zakupów zapewniają legalne akcje. Test nie powinien wybierać modelu, bo wtedy zaczynamy dostrajać się do pytań egzaminacyjnych.",
        "Naszym argumentem jest porównanie z losowaniem, regułami i próbami wyłączania operatorów. Nie opieramy się wyłącznie na tym, że końcowy plan dobrze wygląda na mapie."),
    18:("Projekt ma dać się uruchomić bez wielominutowego treningu od zera.",
        "models/best_strategy.json to zapisane liczby planu. Serwer odczytuje je i korzysta z nich w grze. Kod, mapa, balans oraz ziarna pozwalają odtworzyć trening i analizę. Pliki PDF oraz wyniki trzeba dołączyć do materiałów zaliczeniowych.",
        "Do demonstracji udostępniamy gotowy model. Do odtworzenia badań są również komendy, konfiguracja i surowe pomiary. Można więc oddzielnie sprawdzić grę i cały proces wyszukiwania.")}
    for left in range(1,19,2):
        g.page(f"Prezentacja: slajdy {left}–{left+1}")
        for number in (left,left+1):
            g.card(number,titles[number],*cards[number])

    g.page("Liczby, które łatwo pomylić")
    g.table(["Liczba","Jak ją powiedzieć"],[
        ["0,1 w fitness","Mała maksymalna premia za udział zabitych; to nie sekundy i nie prawdopodobieństwo."],
        ["0,1 s w stresie","Odstęp pojawiania się gołębi w próbie szybkiej fali; to inna wielkość niż premia fitness."],
        ["0,15 jako p","15% szansy próby mutacji dla każdego genu."],
        ["0,15 jako σ","Odchylenie standardowe dodawanego szumu; skala wielkości zmiany."],
        ["0,4","Skala fizycznego zasięgu wieży względem nominalnego rozmiaru."],
        ["24 epoki","24 oceny populacji; pierwsza ocena jest przed reprodukcją."],
        ["3 w turnieju","Z tylu losowych kandydatów wybieramy jednego rodzica."],
        ["3 elity","Tyle najlepszych planów kopiujemy bez zmiany do następnej populacji."],
        ["42 / 137 / 2026","Ziarna losowania trzech treningów, nie ich czas trwania."],
        ["0,10 obrażeń","Średnia po próbach: w naszym przypadku 2 całkowite obrażenia podzielone przez 20 prób."]],[.25,.75])
    g.heading("Dodatkowe liczby z pełnego raportu")
    g.p(f"W jednym przebiegu powstaje 21 nowych potomków na przejście: 24 osobniki minus 3 elity. "
        f"23 przejścia × 21 = {summary['offspring']} potomków. Trzy przebiegi dają 1449 potomków. "
        f"W wybranym przebiegu zmierzono {summary['mutation_attempts']} prób mutacji i {summary['actual_changes']} "
        "faktycznych zmian. Nie trzeba recytować tych liczb — ważne, żeby umieć wskazać, co liczą.")
    g.p("Bez cache nominalnie byłoby 3 × 24 × 24 × 5 = 8640 symulacji treningowych. "
        f"Wykonano {sum(r['history'][-1]['cumulative_rollouts'] for r in analysis['runs'])}, "
        "bo ponowne wystąpienie tego samego genotypu może wykorzystać zapamiętany wynik. "
        "To nie obejmuje późniejszych testów, losowych baseline'ów i ablacji.")

    g.page("Pytania prowadzącego: gotowe odpowiedzi")
    questions=[
        ("Czy to jest sieć neuronowa albo Q-learning?","Nie. To algorytm ewolucyjny do optymalizacji planów. Nie uczymy wag sieci ani tablicy akcji metodą nagród w Q-learningu."),
        ("Czy model uczy się podczas demonstracji?","Nie. Trening odbywa się wcześniej. W grze model odczytuje stały chromosom, ale wykonanie dopasowuje do pieniędzy, wolnych pól i potwierdzeń."),
        ("Czy zaczynaliśmy wyłącznie od losowych planów?","Nie. Populacja początkowa zawiera trzy plany regułowe i 21 losowych. Dlatego nie przypisujemy całej skuteczności ewolucji od zupełnie losowego startu."),
        ("Dlaczego 24 osobniki, 24 epoki i sigma 0,15?","To przyjęte parametry eksperymentu. Zbadaliśmy działanie operatorów, ale nie udowodniliśmy, że te parametry są najlepsze dla każdej mapy."),
        ("Czy krzyżujemy całe wieże?","Nie atomowo. Losujemy pochodzenie każdego genu osobno, więc typ może być od A, x od B, y od A. Potem dekodujemy i naprawiamy plan."),
        ("Dlaczego BASIC wypadł trochę lepiej niż GA?","Prosta reguła dobrze pasuje do tej mapy. Różnica w teście wyniosła jedno łączne obrażenie. Nie twierdzimy, że GA musi wygrać z dobrą heurystyką."),
        ("Dlaczego nie wybraliście innego GA po teście?","Wyboru dokonaliśmy na treningu. Wybór po obejrzeniu testu sprawiłby, że test stałby się kolejnym narzędziem strojenia."),
        ("Co jeśli prowadzący pyta o coś, czego nie sprawdziliśmy?","Powiedz: tego wariantu nie badaliśmy; nasze wyniki dotyczą opisanych map i scenariuszy. Nie zamieniaj przypuszczenia w wynik eksperymentu.")]
    for q,a in questions:
        g.heading(q)
        g.p(a)

    g.page("Jeszcze kilka prostych wyjaśnień")
    g.heading("Jak czytać słowa statystyczne?")
    g.table(["Słowo","Znaczenie"],[
        ["Średnia","Suma wyników podzielona przez ich liczbę. Średnia 0,1 nie wymaga wyniku 0,1 w żadnej pojedynczej grze."],
        ["Mediana","Środkowy wynik po posortowaniu. Dla 1, 2, 3, 100 średnia to 26,5, a mediana 2,5."],
        ["Kwartyle 25–75%","Granice środkowej połowy wyników. Pasmo pokazuje rozrzut populacji."],
        ["Odchylenie standardowe (SD)","Miara rozrzutu. Małe SD oznacza podobne wyniki, duże większe różnice. SD nie jest gwarantowanym błędem prognozy."],
        ["Post hoc","Analiza wykonana po zakończeniu treningu; nie zmienia wyborów algorytmu."],
        ["Plateau","Najlepszy wynik przestaje się poprawiać, ale inne plany nadal mogą być tworzone."]],[.30,.70])
    g.heading("Skąd biorą się pieniądze i energia?")
    g.p("Pieniądze należą do AI i finansują wieże. Energia należy do gracza i finansuje gołębie. "
        "Zabicie daje AI nagrodę pieniężną i obecnie oddaje graczowi cały koszt energii jednostki. "
        "Dotarcie gołębia do bazy oddaje graczowi połowę kosztu energii zaokrągloną w górę. "
        "Z tego powodu sprawniejsza obrona może pośrednio pozwolić graczowi wysłać następne fale wcześniej.")
    g.say("Gdy widzę liczbę, najpierw mówię, co liczy i w jakich jednostkach. Potem wyjaśniam, "
        "czy większa wartość jest lepsza. Na końcu mówię, jaki wniosek rzeczywiście wynika z porównania.","Zasada na całe wystąpienie")
    g.p("Jeśli się zatniesz, wróć do podstaw: <b>próbujemy wiele planów → oceniamy je w symulacji → "
        "wybieramy lepszych rodziców → mieszamy i lekko zmieniamy geny → sprawdzamy nową populację</b>.")
    target=folder/"prezentacja_pomoc.pdf"
    g.save(target)
    print(target.resolve())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("training_results/report.json"))
    args=parser.parse_args()
    build(args.input)


if __name__=="__main__":main()
