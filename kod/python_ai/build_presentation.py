"""Build matching 16:9 PDF and editable PowerPoint slides from measured results."""
import argparse
import html
import json
import shutil
import statistics
from pathlib import Path

from PIL import Image as PILImage
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from src.genetic_ai import Strategy
from src.pdf_report import register_fonts

NAVY="#132b49"
TEAL="#008f85"
BLUE="#2167aa"
ORANGE="#df7c24"
INK="#243b55"
MUTED="#61748a"
PALE="#edf4fa"
WHITE="#ffffff"
SW,SH=13.333333,7.5


class Deck:
    def __init__(self, folder):
        register_fonts()
        self.folder=folder
        self.prs=Presentation()
        self.prs.slide_width=Inches(SW)
        self.prs.slide_height=Inches(SH)
        self.prs.core_properties.title="KittyCatch — algorytm genetyczny w tower defense"
        self.prs.core_properties.author="Aleksander Kopyto, Kacper Mazurek"
        self.prs.core_properties.subject="Projekt 4 — prezentacja na 16 listopada 2026"
        self.pdf=canvas.Canvas(str(folder/"prezentacja.pdf"),pagesize=(SW*72,SH*72))
        self.pdf.setTitle(self.prs.core_properties.title)
        self.pdf.setAuthor(self.prs.core_properties.author)
        self.notes=[]
        self.overflow=[]
        self.number=0

    def new(self, title, section, speaker, note, *, dark=False):
        if self.number:self.pdf.showPage()
        self.number+=1
        self.slide=self.prs.slides.add_slide(self.prs.slide_layouts[6])
        if self.number>=16:
            self.slide._element.set("show","0")
        self.background=NAVY if dark else WHITE
        self.slide.background.fill.solid()
        self.slide.background.fill.fore_color.rgb=RGBColor.from_string(self.background[1:])
        self.pdf.setFillColor(HexColor(self.background))
        self.pdf.rect(0,0,SW*72,SH*72,fill=1,stroke=0)
        self.slide.notes_slide.notes_text_frame.text=f"{speaker}\n\n{note}"
        self.notes.append({"slide":self.number,"title":title,"section":section,"speaker":speaker,"notes":note})
        self.text(section.upper(),.6,.25,11,.25,size=10,color="#91b7d6" if dark else TEAL,bold=True)
        self.text(title,.6,.65,12.1,1.0,size=31,color=WHITE if dark else NAVY,bold=True)
        self.text("KITTYCATCH · PROJEKT 4 · 16.11.2026",.6,7.08,9,.2,size=9,color="#9bb6cf" if dark else MUTED)
        self.text(f"{self.number:02d}",12.1,7.04,.6,.3,size=12,color="#9bb6cf" if dark else MUTED,bold=True)

    def text(self, text, x, y, w, h, *, size=20, color=INK, bold=False):
        shape=self.slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=shape.text_frame
        tf.clear()
        tf.word_wrap=True
        tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
        tf.vertical_anchor=MSO_ANCHOR.TOP
        for i,line in enumerate(text.split("\n")):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
            p.text=line
            p.font.name="Arial"
            p.font.size=Pt(size)
            p.font.bold=bold
            p.font.color.rgb=RGBColor.from_string(color[1:])
            p.space_before=Pt(0)
            p.space_after=Pt(0)
            p.line_spacing=Pt(size*1.15)
        style=ParagraphStyle("slide",fontName="ReportBold" if bold else "Report",fontSize=size,
            leading=size*1.15,textColor=HexColor(color))
        paragraph=Paragraph(html.escape(text).replace("\n","<br/>"),style)
        _,height=paragraph.wrap(w*72,h*72)
        if height>h*72+1:self.overflow.append({"slide":self.number,"text":text,"needed":height,"available":h*72})
        paragraph.drawOn(self.pdf,x*72,(SH-y)*72-height)
        return shape

    def rect(self,x,y,w,h,*,fill=PALE,line=None,radius=True):
        shape=self.slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
            Inches(x),Inches(y),Inches(w),Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb=RGBColor.from_string(fill[1:])
        if line:shape.line.color.rgb=RGBColor.from_string(line[1:])
        else:shape.line.fill.background()
        self.pdf.setFillColor(HexColor(fill))
        if line:self.pdf.setStrokeColor(HexColor(line))
        if radius:self.pdf.roundRect(x*72,(SH-y-h)*72,w*72,h*72,8,stroke=int(bool(line)),fill=1)
        else:self.pdf.rect(x*72,(SH-y-h)*72,w*72,h*72,stroke=int(bool(line)),fill=1)
        return shape

    def picture(self,path,x,y,w,h,*,poster=None):
        with PILImage.open(path) as im:iw,ih=im.size
        scale=min(w/iw,h/ih)
        dw,dh=iw*scale,ih*scale
        dx,dy=x+(w-dw)/2,y+(h-dh)/2
        self.slide.shapes.add_picture(str(path),Inches(dx),Inches(dy),width=Inches(dw),height=Inches(dh))
        self.pdf.drawImage(str(poster or path),dx*72,(SH-dy-dh)*72,dw*72,dh*72,mask="auto")

    def card(self,x,y,w,value,label,*,fill=PALE,color=TEAL):
        self.rect(x,y,w,1.18,fill=fill)
        self.text(value,x+.18,y+.12,w-.36,.55,size=31,color=color,bold=True)
        self.text(label,x+.18,y+.76,w-.36,.3,size=13,color=INK)

    def bullets(self,items,x,y,w,*,size=21,gap=.85,color=INK):
        for i,item in enumerate(items):
            self.rect(x,y+i*gap+.10,.08,.12,fill=TEAL,radius=False)
            self.text(item,x+.23,y+i*gap,w-.23,gap-.08,size=size,color=color)

    def finish(self):
        self.pdf.save()
        self.prs.save(self.folder/"prezentacja.pptx")
        note_lines=["# KittyCatch — notatki do prezentacji", "", "Termin: poniedziałek 16 listopada 2026, godz. 8:00.",
            "Plan: około 10–12 minut z demonstracją; slajdy 16–18 są zapasowe i ukryte w domyślnym pokazie PowerPoint.",
            "Kacper: gra, architektura i demonstracja. Aleksander: genetyka, eksperymenty i wyniki.",
            "Przed wystąpieniem uzupełnić numer zespołu w project_metadata.json, jeśli prowadzący go wymaga.", ""]
        for n in self.notes:
            note_lines += [f"## {n['slide']}. {n['title']}","",f"**Mówi: {n['speaker']}**", "",n["notes"],""]
        (self.folder/"prezentacja_notatki.md").write_text("\n".join(note_lines),encoding="utf-8")
        (self.folder/"presentation_manifest.json").write_text(json.dumps({"date":"2026-11-16",
            "slides":self.notes,"text_overflow":self.overflow},ensure_ascii=False,indent=2),encoding="utf-8")
        if self.overflow:raise ValueError(f"Text overflow: {self.overflow}")


def build(source_path):
    output=source_path.parent
    source=json.loads(source_path.read_text(encoding="utf-8"))
    analysis=json.loads((output/"genetic_analysis/analysis.json").read_text(encoding="utf-8"))
    figures=json.loads((output/"genetic_analysis/figure_summary.json").read_text(encoding="utf-8"))
    details=json.loads((output/"detailed_report.json").read_text(encoding="utf-8"))
    operator=json.loads((output/"genetic_analysis/operator_example.json").read_text(encoding="utf-8"))
    folder=output/"genetic_analysis"
    data=source["strategy"]
    strategy=Strategy(tuple(data["tower_types"]),tuple(data["genes"]),data["duration"])
    plan=strategy.decode(20,15)
    metrics={m["strategy"]:m for m in figures["benchmark"]}
    validations=[case for run in details["godot_validation"] for case in run["scenarios"]]
    gif=next(output/case["animation"] for case in validations if case.get("animation"))
    shutil.copyfile(gif,output/"prezentacja_demo.gif")
    with PILImage.open(gif) as image:
        image.seek(min(90,image.n_frames-1))
        image.convert("RGB").save(output/"prezentacja_demo.png")
    deck=Deck(output)

    deck.new("KittyCatch", "Algorytm genetyczny w tower defense", "Kacper",
        "Około 20 s. Przedstaw projekt 4: AI broni bazy, człowiek wysyła gołębie. "
        "Powiedz, że Aleksander odpowiadał za genetykę i AI, a Kacper za grę. "
        "Zapowiedz pokaz działającej komunikacji z Godotem i porównanie z losową oraz regułową obroną.",dark=True)
    deck.text("Jak algorytm wybiera\ntyp, miejsce i czas\nbudowy wież?",.6,1.85,6.1,2.2,size=33,color=WHITE,bold=True)
    deck.text("Aleksander Kopyto — genetyka i AI\nKacper Mazurek — gra",.6,4.55,6.2,.95,size=20,color="#cfdfef")
    deck.text("16 listopada 2026 · poniedziałek, 8:00",.6,6.13,7,.4,size=17,color="#91b7d6")
    deck.picture(output/f"layout_seed_{source['settings']['seed']}.png",7.0,1.8,5.7,4.55)

    deck.new("Problem: obrona przy ograniczonym budżecie", "01 / Gra", "Kacper",
        "Około 35 s. Wyjaśnij odwrócone role tower defense: gracz komponuje fale, AI kupuje wieże. "
        "Wieże kosztują, zabicia przynoszą środki na kolejne zakupy. Podkreśl, że maksymalnie 10 slotów "
        "nie oznacza 10 wież od początku ani stałego całkowitego wydatku 150.")
    deck.card(.6,1.85,3.8,"200 HP","zdrowie bazy")
    deck.card(4.75,1.85,3.8,"150","początkowe środki AI")
    deck.card(8.9,1.85,3.8,"10 slotów","maksymalny plan budowy")
    deck.bullets(["Gracz wysyła SCOUT, TANK i SPEED.","AI kupuje BASIC lub SNIPER na wolnych polach.",
        "Celem jest ograniczenie przecieków do bazy."],.8,3.55,11.7,size=24,gap=.9)
    deck.text("Nagrody za zabicia są reinwestowane — ekonomia zmienia dalszy przebieg gry.",.8,6.35,11.8,.45,size=18,color=MUTED)

    deck.new("Jedna polityka: w symulatorze i w Godocie", "02 / Architektura", "Kacper",
        "Około 40 s. Pokaż granicę między silnikiem a Pythonem. Godot jest klientem TCP, Python serwerem. "
        "Godot wysyła init/update, AI odsyła build_tower, a silnik odpowiada action_result. "
        "Symulator przyspiesza trening; osobno sprawdziliśmy wybraną politykę w rzeczywistym silniku. "
        "Przekaż głos Aleksandrowi.")
    for x,y,w,h,title,body in [(.7,2.1,4.7,1.65,"GODOT","Gra, ruch, kolizje, pociski"),
        (7.75,2.1,4.7,1.65,"PYTHON / POLITYKA","Stan → decyzja build_tower"),
        (7.75,4.65,4.7,1.35,"TRENING OFFLINE","Populacja → symulacje → fitness")]:
        deck.rect(x,y,w,h)
        deck.text(title,x+.2,y+.22,w-.4,.4,size=23,bold=True)
        deck.text(body,x+.2,y+.85,w-.4,.55,size=18)
    deck.text("→ init / update",5.55,2.25,2.1,.6,size=18,color=TEAL)
    deck.text("← akcja / wynik",5.55,3.05,2.1,.6,size=18,color=TEAL)
    deck.text("↑ zapisany chromosom",8.1,4.03,4,.4,size=18,color=TEAL)
    deck.text("JSON UTF-8 + nowa linia\nTCP 127.0.0.1:8080",.85,4.65,5.6,1,size=22,color=MUTED)

    deck.new("Chromosom to plan 10 zakupów", "03 / Reprezentacja", "Aleksander",
        "Około 40 s. Wyjaśnij 40 genów: dla każdego slotu typ, x, y i najwcześniejszy czas. "
        "Geny mają wartości 0–1, potem są dyskretyzowane. Pole nielegalne lub zajęte naprawiamy do "
        "najbliższego wolnego. Faktyczny zakup czeka na środki i potwierdzenie poprzedniej akcji.")
    fields=[("TYP",data["genes"][0],TEAL),("X",data["genes"][1],BLUE),("Y",data["genes"][2],BLUE),("CZAS",data["genes"][3],ORANGE)]
    for i,(label,value,color) in enumerate(fields):
        x=.75+i*3.12
        deck.rect(x,2.0,2.85,1.5)
        deck.text(label,x+.18,2.18,2.5,.35,size=17,color=color,bold=True)
        deck.text(f"{value:.3f}",x+.18,2.66,2.5,.6,size=32,color=NAVY,bold=True)
    first=next(p for p in plan if p["slot"]==0)
    deck.text(f"Cel slotu 0 → {first['tower_type']}, ({first['x']}, {first['y']}), od {first['earliest']:.1f} s",.8,4.05,11.8,.75,size=26,bold=True)
    deck.bullets(["4 geny × 10 slotów = 40 liczb w [0,1].","Plan jest naprawiany do legalnych pól.",
        "Czas genu jest dolną granicą, a nie gwarancją zakupu."],.8,5.05,11.8,size=20,gap=.55)

    deck.new("Jak oceniamy jakość obrony?", "04 / Funkcja celu", "Aleksander",
        "Około 35 s. L oznacza przecieki, K zabicia, N faktycznie wysłane jednostki. "
        "Ocena jest średnią po pięciu scenariuszach. Premia jest mała: ochrona bazy ma pierwszeństwo. "
        "Wartość 0,1 jest górną granicą tego fitness w danym eksperymencie, nie dowodem globalnego optimum.")
    deck.rect(.75,1.95,11.85,1.7,fill=NAVY)
    deck.text("F = −L + 0,1 × K / max(N, 1)",1.15,2.37,11.0,.85,size=39,color=WHITE,bold=True)
    deck.bullets(["L — jednostki, które dotarły do bazy.","K / N — udział zatrzymanych przeciwników.",
        "Ocena osobnika = średnia z 5 scenariuszy."],.9,4.15,11.5,size=24,gap=.7)
    deck.text("Wyższy fitness jest lepszy. Testy nie wybierają chromosomu ani epoki.",.9,6.48,11.7,.35,size=18,color=TEAL,bold=True)

    deck.new("Cykl algorytmu genetycznego", "05 / Metoda", "Aleksander",
        "Około 45 s. Przejdź przez cykl od lewej. Populacja początkowa zawiera też trzy heurystyki. "
        "Turniej wybiera rodziców, każdy gen pochodzi z A lub B, mutacja dodaje szum Gaussa. "
        "Trzy elity są kopiowane bez zmian. Epoka 1 ocenia inicjalizację, więc 24 epoki oznaczają 23 reprodukcje.")
    stages=[("24","osobniki"),("5","scenariuszy"),("3","w turnieju"),("50:50","krzyżowanie"),("15%","mutacja genu"),("3","elity")]
    for i,(value,label) in enumerate(stages):
        x=.65+i*2.04
        deck.rect(x,2.35,1.76,1.85)
        deck.text(value,x+.14,2.69,1.48,.75,size=31,color=TEAL,bold=True)
        deck.text(label,x+.14,3.55,1.48,.5,size=14,bold=True)
        if i<5:deck.text("→",x+1.78,3.02,.25,.5,size=21,color=MUTED)
    deck.rect(.75,4.85,11.85,1.05,fill=NAVY)
    deck.text("24 epoki oceny · 3 niezależne przebiegi: 42, 137, 2026",1.0,5.12,11.3,.55,size=24,color=WHITE,bold=True)
    deck.text("Mutacja: N(0; 0,15²), obcięcie do [0,1]. Cache oszczędza ponowne oceny tych samych genotypów.",.85,6.3,11.7,.6,size=17,color=MUTED)

    deck.new("Skąd biorą się geny potomka?", "06 / Krzyżowanie i mutacja", "Aleksander",
        "Około 40 s. To wycinek rzeczywistego zapisu: osiem z czterdziestu genów. "
        "Pasek kolorów wskazuje rodzica, a czerwone pole mutację. Nie przypisuj całej poprawy pojedynczej "
        "mutacji — krzyżowanie i mutacja zadziałały razem. O osobnym wpływie operatorów opowiedz przy ablacji.")
    birth=operator["birth"]
    winner=next(r for r in analysis["runs"] if r["seed"]==source["settings"]["seed"])
    records=[json.loads(line) for line in (folder/winner["telemetry"]).read_text(encoding="utf-8").splitlines()]
    parents={p["id"]:p["genes"] for p in records[operator["epoch"]-2]["population"]}
    rows=[("Rodzic A",parents[birth["parent_ids"][0]]),("Rodzic B",parents[birth["parent_ids"][1]]),
        ("Krzyżowanie",birth["before_mutation"]),("Potomek",birth["genes"])]
    mutations={m["gene"] for m in birth["mutations"]}
    for r,(label,genes) in enumerate(rows):
        y=2.0+r*.75
        deck.text(label,.7,y+.12,2.0,.4,size=20,bold=True)
        for j,value in enumerate(genes[:8]):
            x=2.85+j*1.15
            color="#ffe8e9" if r==3 and j in mutations else PALE
            deck.rect(x,y,1.04,.6,fill=color,line="#d44658" if r==3 and j in mutations else None,radius=False)
            deck.text(f"{value:.2f}",x+.10,y+.13,.86,.35,size=19,bold=True)
            if r==2:deck.rect(x,y+.61,1.04,.07,fill=BLUE if birth["source_mask"][j]==0 else TEAL,radius=False)
    deck.text("Fragment 8 z 40 genów · niebieski: rodzic A · zielony: rodzic B",.85,5.5,11.7,.45,size=20,color=MUTED)
    deck.text(f"F rodziców: {birth['parent_fitness'][0]:.3f} / {birth['parent_fitness'][1]:.3f} → F potomka: {birth['fitness']:.3f}",
        .85,6.05,11.7,.45,size=20,color=MUTED)
    deck.text(f"Poprawa względem lepszego rodzica: ΔF = {birth['fitness_delta_vs_parent']:+.3f}",.85,6.53,11.7,.38,size=20,color=TEAL,bold=True)

    deck.new("Jak przeprowadziliśmy eksperyment?", "07 / Protokół", "Aleksander",
        "Około 40 s. Wymień pięć profili: SCOUT, TANK, SPEED, MIXED, BURST. "
        "Trening i test mają rozłączne ziarna. Losowy baseline to 20 planów razy 20 tych samych scenariuszy. "
        "Późniejsze krzywe testowe służą analizie, nie selekcji. Wspólne harmonogramy nie gwarantują "
        "identycznych rzeczywistych fal, bo zabicia zwracają graczowi energię.")
    deck.card(.75,1.95,3.7,"3 × 24 × 24","przebiegi × epoki × populacja")
    deck.card(4.82,1.95,3.7,"5 / 20","scenariusze treningowe / testowe")
    deck.card(8.9,1.95,3.7,"400","prób losowych rozmieszczeń")
    deck.bullets(["Jedna mapa, baza 200 HP, epizod 120 s.","Te same zasady budżetu i reinwestowania nagród.",
        "Porównanie: RANDOM, BASIC, SNIPER, MIXED i poprzedni model.","Testy i ablacje nie zmieniały wybranego modelu."],.9,3.65,11.6,size=21,gap=.65)

    deck.new("Najlepsze plany poprawiają się wcześnie", "08 / Rozwój uczenia", "Aleksander",
        "Około 40 s. Pokaż trzy linie, a nie tylko wynik końcowy. Dla ziaren 42, 137 i 2026 "
        "najlepszy zaobserwowany wynik osiągnięto odpowiednio w epokach 5, 3 i 4. "
        "Populacja dalej eksplorowała neutralne plany. Heurystyki były w inicjalizacji, więc nie mów, "
        "że cały efekt uzyskano od zupełnie losowego startu.")
    deck.picture(folder/"best_runs.png",.5,1.85,9.15,4.95)
    deck.rect(9.85,2.1,2.8,3.95)
    deck.text("Pierwsza epoka\nnajlepszego wyniku",10.05,2.35,2.4,1.05,size=20,bold=True)
    deck.text("42 → 5\n137 → 3\n2026 → 4",10.1,3.5,2.3,1.7,size=28,color=TEAL,bold=True)
    deck.text("To maksimum obserwowane\nw tym eksperymencie.",10.05,5.25,2.35,.8,size=15,color=MUTED)

    deck.new("Plateau fitness nie zatrzymuje ewolucji", "09 / Chromosomy", "Aleksander",
        "Około 35 s. Każdy wiersz to epoka, każda kolumna to gen najlepszego osobnika. "
        "Zmiany po plateau są możliwe, bo różne plany mają tę samą ocenę. Genotyp ciągły nie jest "
        "tym samym co odkodowane zachowanie. Pełne wartości i wszystkie populacje są zapisane w JSONL i CSV.")
    deck.picture(folder/"chromosome_evolution.png",.55,1.75,9.8,5.15)
    deck.text("40 genów\n×\n24 epoki",10.55,2.3,2.2,1.85,size=28,color=TEAL,bold=True)
    deck.text("T: typ wieży\nx, y: pole\nt: czas budowy",10.55,4.65,2.2,1.25,size=20)

    deck.new("GA wygrywa z losowaniem, reguły są mocne", "10 / Wyniki porównawcze", "Aleksander",
        "Około 50 s. To średnie obrażenia na testach — mniej znaczy lepiej. GENETIC: 0,10; "
        "BASIC: 0,05; RANDOM: 31,9575; poprzedni model ponownie oceniony przy aktualnych zasadach: 20,30. "
        "Nie twierdź, że GA przewyższa każdą heurystykę. W kontroli RANDOM odchylenie zawiera zmienność "
        "planów i scenariuszy. Możesz dodać, że GA zatrzymuje średnio 96,6% jednostek.")
    rows=[("BASIC",BLUE),("GENETIC",TEAL),("PREVIOUS",MUTED),("RANDOM",ORANGE),("NO_DEFENSE","#bf4b62")]
    maximum=max(metrics[name]["damage"] for name,color in rows)
    for i,(name,color) in enumerate(rows):
        y=1.95+i*.73
        deck.text(name,.8,y+.08,2.25,.4,size=20,bold=True)
        value=metrics[name]["damage"]
        width=value/maximum*7.65
        deck.rect(3.18,y+.05,max(width,.008),.43,fill=color,radius=False)
        deck.text(f"{value:.2f}",3.3+width,y+.04,1.25,.45,size=20,color=color,bold=True)
    deck.text("Średnie obrażenia bazy ↓ · pozostałe strategie: 20 prób · RANDOM: 20 planów × 20 scenariuszy",.8,5.85,11.9,.6,size=17,color=MUTED)
    deck.rect(.8,6.38,11.7,.44,fill=PALE)
    deck.text("Wniosek: świadome rozmieszczenie jest kluczowe; GA nie gwarantuje przewagi nad dobrą heurystyką.",.95,6.46,11.4,.3,size=16,bold=True)

    deck.new("Ablacje: osobno wyłączamy operatory", "11 / Co wnosi metoda?", "Aleksander",
        "Około 45 s. Każda grupa ma trzy ziarna, populację 12 i 12 epok. FULL jest kontrolą z tym samym "
        "mniejszym budżetem, a nie głównym treningiem 24×24. Mutacja wyłączona dała podobny wynik testowy "
        "w małej próbie; nie jest to dowód jej uniwersalnej zbędności. Bez elitaryzmu najlepszy wynik "
        "ostatniej populacji bywa gorszy od wcześniej osiągniętego.")
    deck.picture(folder/"ablations.png",.55,1.85,8.7,4.95)
    deck.rect(9.5,2.05,3.15,4.25)
    deck.text("Kontrolowane porównanie",9.7,2.3,2.72,.9,size=23,bold=True)
    deck.text("3 ziarna\n12 osobników\n12 epok",9.75,3.35,2.6,1.7,size=25,color=TEAL,bold=True)
    deck.text("Mała próba — bez\nuniwersalnego rankingu\nwariantów GA.",9.7,5.05,2.7,1.05,size=17,color=MUTED)

    deck.new("Sprawdziliśmy obronę w prawdziwym Godocie", "12 / Silnik i fizyka", "Kacper",
        "Około 45 s. Wyjaśnij, dlaczego osobna walidacja ma znaczenie. Scena wieży ma skalę 0,4, "
        "która obejmuje też zasięg — dawny model zawyżał go. Skalibrowano zasięg, promień kolizji, "
        "rozrzut i kolejność wejścia celów. Siedem przebiegów obejmuje pięć profili i dwa testy kontrolne 1×; "
        "nie są to wszystkie możliwe ataki. Wszystkie miały zero przecieków i zero odrzuconych budów.")
    deck.card(.65,1.85,3.8,str(len(validations)),"przebiegów przez prawdziwy socket")
    deck.card(4.77,1.85,3.8,str(sum(c["godot_damage"] for c in validations)),"łączne obrażenia bazy")
    deck.card(8.9,1.85,3.8,str(sum(c["rejected"] for c in validations)),"odrzuconych komend budowy")
    deck.text("Fizyka wpływa na strategię",.85,3.6,11.8,.6,size=28,bold=True)
    deck.bullets(["Zasięg BASIC: 2 × 64 px × 0,4 = 51,2 px.","Promień gołębia 8 px; rozrzut względem trasy ±8 px.",
        "Pociski samosterujące: 400 px/s; atak zależy od czasu lotu."],.85,4.45,11.8,size=22,gap=.68)

    deck.new("Demonstracja: gracz atakuje, AI buduje", "13 / Pokaz działania", "Kacper",
        "Około 90 s. Przed zajęciami przygotuj terminal w python_ai i uruchom: "
        "python -m src.serwer --strategy models/best_strategy.json. W Godocie F5, wybierz mapę i poziom "
        "trudności, wyślij falę mieszaną. Pokaż automatyczne budowanie, spadek środków i nagrody. "
        "Jeśli pokaz na żywo zawiedzie, odtwórz prezentacja_demo.gif. GIF pochodzi z obserwacji realnego "
        "meczu Godota; obraz mapy jest renderowany z odebranych stanów. W PPTX animacja jest osadzona, "
        "a w PDF widoczny jest nieruchomy kadr.")
    deck.picture(output/"prezentacja_demo.gif",.55,1.8,8.4,4.9,poster=output/"prezentacja_demo.png")
    deck.bullets(["1. Uruchamiamy AI.","2. Wysyłamy falę.","3. Obserwujemy wieże\ni ekonomię."],9.2,2.15,3.6,size=21,gap=1.0)
    deck.text("Awaryjnie: prezentacja_demo.gif\nKadr z obserwacji prawdziwego meczu, seed 303.",.75,6.45,11.7,.55,size=15,color=MUTED)

    deck.new("Wnioski i dalszy rozwój", "14 / Podsumowanie", "Aleksander i Kacper",
        "Około 40 s. Aleksander: reprezentacja planu i jakość oceny są równie ważne jak same operatory. "
        "Kacper: integracja działa w rzeczywistym silniku. Uczciwie podaj ograniczenia — jedna mapa, "
        "skończone profile, przybliżona fizyka. Kolejne kroki to więcej map, inteligentniejszy atakujący "
        "i ocena większej liczby przypadków w Godocie. Zakończ prezentację; slajdy 16–18 są do pytań.")
    deck.bullets(["GA znajduje legalne i skuteczne plany obrony.","Silnik ujawnia błędy niewidoczne w samym symulatorze.",
        "Dobra heurystyka pozostaje ważnym punktem odniesienia."],.85,1.95,11.75,size=25,gap=1.0)
    deck.rect(.85,5.3,11.7,1.08,fill=NAVY)
    deck.text("Dalej: więcej map · silniejszy przeciwnik · więcej testów w silniku",1.1,5.63,11.2,.6,size=23,color=WHITE,bold=True)
    deck.text("Aleksander Kopyto — AI i genetyka   |   Kacper Mazurek — gra",.85,6.58,11.8,.35,size=17,color=MUTED)

    deck.new("Zapas: duże fale i limity energii", "Pytania / materiał dodatkowy", "Aleksander",
        "Pokaż tylko w razie pytania o poziomy trudności. Hard/medium/easy to limity 100/300/1000. "
        "W próbach przeciążeniowych energia startowała na maksimum, a nie na normalnych 40; "
        "jednostki wysyłano co 0,1 s, a odstępy żądań fal skrócono o połowę. To model zgromadzonej "
        "dużej fali, a nie zwykłego początku gry. Nie twierdź, że te testy dowodzą idealnego balansu.")
    deck.picture(output/"stress_test.png",.6,1.8,12.1,4.55)
    deck.text("Uwaga metodologiczna: pełny początkowy zapas energii i szybkie fale — osobna próba przeciążeniowa.",.8,6.45,11.8,.55,size=17,color=ORANGE,bold=True)

    deck.new("Zapas: najważniejsze pytania o GA", "Pytania / odpowiedzi", "Aleksander",
        "Możliwe pytania: dlaczego GA, a nie losowanie? Bo zachowuje i rekombinuje ocenione rozwiązania. "
        "Dlaczego BASIC czasem lepszy? Heurystyka jest dostosowana do jednej mapy, różnice na małej próbie "
        "są małe; nie obiecujemy globalnego optimum. Jak legalność? Najbliższe wolne pole i weryfikacja "
        "funduszy w aktualnym stanie. Dlaczego nie wybrano GA_137 po teście? Wybór odbył się na treningu, "
        "a test nie powinien służyć ponownemu strojeniu.")
    deck.bullets(["Dlaczego GA? Selekcja i rekombinacja ocenionych planów.","Czy to optimum globalne? Nie — najlepszy sprawdzony plan.",
        "Dlaczego test nie wybiera modelu? Żeby ograniczyć dopasowanie do testu.",
        "Skąd legalne akcje? Naprawa pól, budżet i potwierdzenia Godota."],.85,2.0,11.75,size=23,gap=1.0)

    deck.new("Zapas: jak odtworzyć rozwiązanie", "Materiały i uruchomienie", "Kacper i Aleksander",
        "Powiedz, że gotowy model pozwala uruchomić przykład bez treningu. W repo jest instrukcja, "
        "konfiguracja, migawki danych i kod. Sprawozdanie ma 9 stron, a analityczny załącznik 32 strony. "
        "Wyniki training_results są ignorowane przez Git, dlatego należy dołączyć je do paczki zaliczeniowej. "
        "Nie wysyłaj samego linku do repo bez wymaganych PDF-ów i modelu.")
    deck.rect(.8,1.95,11.7,1.15,fill=NAVY)
    deck.text("python -m src.serwer --strategy models/best_strategy.json",1.05,2.28,11.2,.55,size=21,color=WHITE,bold=True)
    deck.bullets(["Godot 4.7.2 · Python 3.14 · JSON/TCP.","Gotowy model oraz migawki mapy i balansu w models/.",
        "Sprawozdanie 9 stron + rozszerzony raport analityczny.","Surowe populacje, rodzice, mutacje, wykresy i animacje."],.9,3.65,11.7,size=22,gap=.65)
    deck.text("github.com/Kacpron123/KittyCatch",.9,6.5,11.7,.35,size=19,color=TEAL,bold=True)
    deck.finish()
    print(f"Created {deck.number} slides: {output/'prezentacja.pdf'} and {output/'prezentacja.pptx'}")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("training_results/report.json"))
    args=parser.parse_args()
    build(args.input)


if __name__=="__main__":main()
