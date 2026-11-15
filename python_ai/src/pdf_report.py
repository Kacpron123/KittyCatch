"""Export the generated Markdown experiment report to a printable PDF."""
import argparse
import html
import re
import json
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


class ReportDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("Heading1", "Heading2"):
            level = 0 if flowable.style.name == "Heading1" else 1
            if level and not getattr(self, "_outline_started", False):
                return
            self._outline_started = True
            name = f"section-{self.page}-{getattr(self, '_section_count', 0)}"
            self._section_count = getattr(self, "_section_count", 0) + 1
            self.canv.bookmarkPage(name)
            self.canv.addOutlineEntry(flowable.getPlainText(), name, level=level, closed=False)
            if level == 0:
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page, name))

    def beforeDocument(self):
        self._outline_started = False
        self._section_count = 0


def register_fonts() -> None:
    # Embedded TrueType fonts preserve Polish characters in every PDF viewer.
    font_dir = Path("C:/Windows/Fonts")
    if not (font_dir / "arial.ttf").exists():
        font_dir = Path("/usr/share/fonts/truetype/dejavu")
    regular = "arial.ttf" if (font_dir / "arial.ttf").exists() else "DejaVuSans.ttf"
    bold = "arialbd.ttf" if regular == "arial.ttf" else "DejaVuSans-Bold.ttf"
    pdfmetrics.registerFont(TTFont("Report", str(font_dir / regular)))
    pdfmetrics.registerFont(TTFont("ReportBold", str(font_dir / bold)))
    pdfmetrics.registerFontFamily("Report", normal="Report", bold="ReportBold", italic="Report", boldItalic="ReportBold")


def export_pdf(source: Path, target: Path) -> None:
    register_fonts()
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "Report"
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    styles["BodyText"].spaceAfter = 7
    for name, size in (("Title", 21), ("Heading1", 15), ("Heading2", 11)):
        styles[name].fontName = "ReportBold"
        styles[name].fontSize = size
        styles[name].leading = size + 5
        styles[name].textColor = colors.HexColor("#152e4f")
    styles["Heading1"].spaceBefore = 16
    styles["Heading1"].spaceAfter = 9
    styles["Heading1"].keepWithNext = True
    styles["BodyText"].textColor = colors.HexColor("#26364b")
    cell_style = ParagraphStyle("Cell", fontName="Report", fontSize=7, leading=10, wordWrap="CJK")
    caption_style = ParagraphStyle("Caption", parent=styles["BodyText"], fontSize=8, alignment=TA_CENTER)
    code_style = ParagraphStyle("CodeBlock", fontName="Report", fontSize=7, leading=9, leftIndent=8, spaceAfter=10)
    width = A4[0] - 80
    story = []

    def inline(text):
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`([^`]+)`", r"<font color='#34445c'>\1</font>", text)
        return re.sub(r"\[([^]]+)\]\(([^)]+)\)", lambda m:
            f'<link href="{m[2]}" color="#235cb0">{m[1]}</link>' if m[2].startswith("https://")
            else f"{m[1]} ({m[2]})", text)

    def add_image(image, caption, max_height=325):
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)
        scale = min(width / image.width, max_height / image.height)
        story.append(KeepTogether([Image(buffer, width=image.width * scale, height=image.height * scale),
            Spacer(1, 5), Paragraph(inline(caption), caption_style), Spacer(1, 9)]))

    lines = source.read_text(encoding="utf-8").splitlines()
    data_file = source.with_suffix(".json")
    experiment = json.loads(data_file.read_text(encoding="utf-8")) if data_file.exists() else None
    has_cover = bool(experiment and experiment.get("search_runs"))
    if has_cover:
        cover_title = ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=30, leading=35,
                                    alignment=0, spaceAfter=20)
        kicker = ParagraphStyle("Kicker", parent=styles["BodyText"], fontSize=11, leading=16,
                                textColor=colors.HexColor("#2978aa"), spaceAfter=18)
        story += [Spacer(1, 20), Paragraph("KITTYCATCH / ANALIZA STRATEGII", kicker),
            Paragraph("Algorytm genetyczny<br/>rozwój populacji i obrony" if experiment.get("genetic_analysis")
                      else "Nowe układy obrony<br/>po zmianie balansu", cover_title),
            Paragraph("Rozszerzony raport analityczny — materiał uzupełniający" if experiment.get("genetic_analysis")
                      else "Sprawozdanie z ponownego treningu algorytmu genetycznego", styles["Heading2"]),
            Spacer(1, 14)]
        metadata_path = Path(__file__).resolve().parents[2] / "project_metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            story.append(Paragraph(" · ".join(html.escape(a["name"])+" — "+html.escape(a["responsibility"])
                for a in metadata["authors"]), styles["BodyText"]))
        settings, config = experiment["settings"], experiment["config"]
        winner = experiment["comparison"]["GENETIC"]
        profile_count = len(settings["test_seeds"])
        metric_style = ParagraphStyle("Metric", parent=styles["BodyText"], fontName="ReportBold",
            fontSize=21, leading=27, textColor=colors.white)
        label_style = ParagraphStyle("MetricLabel", parent=styles["BodyText"], fontSize=8, leading=12,
            textColor=colors.HexColor("#d9e8fa"))
        metrics = [[Paragraph(str(config.get("base", {}).get("health", 1000)), metric_style),
                    Paragraph(str(len(experiment["search_runs"])), metric_style),
                    Paragraph(str(profile_count), metric_style)],
                   [Paragraph("HP BRONIONEJ BAZY", label_style), Paragraph("NIEZALEŻNE TRENINGI", label_style),
                    Paragraph("SCENARIUSZE TESTOWE", label_style)]]
        if experiment.get("genetic_analysis"):
            metrics = [[Paragraph(str(len(experiment["strategy"]["genes"])), metric_style),
                        Paragraph(str(settings["generations"]), metric_style),
                        Paragraph(str(len(experiment["search_runs"])), metric_style)],
                       [Paragraph("GENÓW W CHROMOSOMIE", label_style), Paragraph("EPOK OCENY", label_style),
                        Paragraph("NIEZALEŻNE TRENINGI", label_style)]]
        cards = Table(metrics, colWidths=[width/3]*3)
        cards.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#152e4f")),
            ("LEFTPADDING",(0,0),(-1,-1),15), ("TOPPADDING",(0,0),(-1,0),14),
            ("BOTTOMPADDING",(0,1),(-1,1),14)]))
        story += [cards, Spacer(1, 20), Paragraph(
            f"<b>Wynik lokalnego modelu wybranej obrony:</b> {winner['mean_damage']:.2f} średnich obrażeń otrzymanych "
            f"przez bazę w {profile_count} scenariuszach. Wybór chromosomu odbył się według wyników "
            "treningowych, przed oceną na zbiorze testowym.", styles["BodyText"]),
            Paragraph(f"Populacja: {settings['population']} · pokolenia: {settings['generations']} na przebieg · "
                f"czas epizodu: {settings['duration']:g} s · krok: {settings['dt']:g} s · "
                f"limit energii gracza: {config['economy']['player']['max_energy']}.", styles["BodyText"])]
        detail_path = source.parent / "detailed_report.json"
        if detail_path.exists():
            details = json.loads(detail_path.read_text(encoding="utf-8"))
            runs = details.get("godot_validation", []) if details.get("config_sha256") == experiment.get("config_sha256") else []
            cases = [case for run in runs for case in run["scenarios"]]
            if cases:
                story.append(Paragraph(f"<b>Sprawdzenie w silniku Godota:</b> {len(cases)} przebiegów przez socket, "
                    f"{sum(c['godot_damage'] for c in cases)/len(cases):.2f} średnich obrażeń bazy. "
                    "Pomiary silnika oraz próby przeciążeniowe opisano osobno.", styles["BodyText"]))
        if (source.parent / "layouts_overview.png").exists():
            with PILImage.open(source.parent / "layouts_overview.png") as preview:
                add_image(preview.copy(), "Trzy warianty obrony; szczegółowe mapy i kolejność budowy w dalszej części.", max_height=160)
        story += [Paragraph("Dokument obejmuje aktualny balans, porównanie modeli, nowe mapy wież, "
            "chromosom zwycięzcy oraz przebieg jednej rozgrywki. Wyniki pochodzą z lokalnego symulatora.",
            caption_style), PageBreak()]
        toc = TableOfContents()
        toc.levelStyles = [ParagraphStyle("ContentsItem", fontName="Report", fontSize=10,
                                          leading=15, spaceBefore=7, leftIndent=0)]
        story += [Paragraph("Spis treści", ParagraphStyle("ContentsTitle", parent=styles["Title"], alignment=0)),
                  Spacer(1, 15), toc, PageBreak()]
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line.startswith("```"):
            code = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1
            if code and code[0].lstrip().startswith("{"):
                try:
                    payload = json.loads("\n".join(code))
                    if "genes" in payload:
                        genes = payload.pop("genes")
                        prefix = json.dumps(payload, indent=2, ensure_ascii=False).rstrip().rstrip("}").rstrip()
                        groups = ["    " + ", ".join(json.dumps(v) for v in genes[i:i+4]) for i in range(0, len(genes), 4)]
                        code = (prefix + ',\n  "genes": [\n' + ",\n".join(groups) + "\n  ]\n}").splitlines()
                except (ValueError, TypeError):
                    pass
            # Wrapping also keeps long replay commands inside printable margins.
            story.append(Preformatted("\n".join(code), code_style, maxLineLength=100))
        elif line.startswith("|"):
            rows = [line]
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(lines[index].strip())
                index += 1
            cells = [[c.strip() for c in row.strip("|").split("|")] for row in rows]
            cells = [row for row in cells if not all(re.fullmatch(r":?-+:?", c) for c in row)]
            columns = len(cells[0])
            weights = [min(32, max(8, max(len(row[i]) for row in cells))) for i in range(columns)]
            widths = [width * w / sum(weights) for w in weights]
            content = [[Paragraph(f"<b>{inline(c)}</b>" if i == 0 else inline(c), cell_style) for c in row]
                       for i, row in enumerate(cells)]
            table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT", splitInRow=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd3df")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 10)])
        elif match := re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line):
            path = source.parent / match[2]
            with PILImage.open(path) as image:
                if path.suffix.lower() == ".gif":
                    story.append(Paragraph("Wybrane klatki animacji", styles["Heading2"]))
                    story.append(Paragraph("PDF zawiera nieruchome kadry. Pełna animacja jest w pliku replay.gif obok raportu.", styles["BodyText"]))
                    for frame_index, label in ((0, "Początek"), (image.n_frames // 2, "Środek rozgrywki"), (image.n_frames - 1, "Koniec")):
                        image.seek(frame_index)
                        add_image(image.copy(), label)
                else:
                    add_image(image.copy(), match[1])
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if has_cover and level == 1:
                continue
            style = "Title" if level == 1 else "Heading1" if level == 2 else "Heading2"
            story.append(Paragraph(inline(line.lstrip("# ")), styles[style]))
        else:
            prefix = "• " if line.startswith("- ") else ""
            story.append(Paragraph(prefix + inline(line[2:] if prefix else line), styles["BodyText"]))

    def footer(canvas, document):
        canvas.setFont("Report", 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(40, 25, "KittyCatch • Raport eksperymentu genetycznego")
        canvas.drawRightString(A4[0] - 40, 25, f"Strona {document.page}")
        if document.page > 1:
            canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
            canvas.line(40, A4[1] - 22, A4[0] - 40, A4[1] - 22)
            canvas.setFont("Report", 7)
            canvas.drawString(40, A4[1] - 17, "KITTYCATCH / NOWY BALANS / OBRONA BAZY")

    target.parent.mkdir(parents=True, exist_ok=True)
    document = ReportDocument(str(target), pagesize=A4, rightMargin=40, leftMargin=40,
        topMargin=38, bottomMargin=42, title=lines[0].lstrip("# ") if lines else "KittyCatch",
        author="Aleksander Kopyto, Kacper Mazurek")
    document.multiBuild(story, onFirstPage=footer, onLaterPages=footer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("training_results/report.md"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".pdf")
    export_pdf(args.input, output)
    print(output.resolve())


if __name__ == "__main__":
    main()
