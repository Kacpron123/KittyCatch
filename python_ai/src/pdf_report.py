"""Export the generated Markdown experiment report to a printable PDF."""
import argparse
import html
import re
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
    Image, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle,
)


def export_pdf(source: Path, target: Path) -> None:
    # Embedded TrueType fonts preserve Polish characters in every PDF viewer.
    font_dir = Path("C:/Windows/Fonts")
    if not (font_dir / "arial.ttf").exists():
        font_dir = Path("/usr/share/fonts/truetype/dejavu")
    regular = "arial.ttf" if (font_dir / "arial.ttf").exists() else "DejaVuSans.ttf"
    bold = "arialbd.ttf" if regular == "arial.ttf" else "DejaVuSans-Bold.ttf"
    pdfmetrics.registerFont(TTFont("Report", str(font_dir / regular)))
    pdfmetrics.registerFont(TTFont("ReportBold", str(font_dir / bold)))
    pdfmetrics.registerFontFamily("Report", normal="Report", bold="ReportBold", italic="Report", boldItalic="ReportBold")
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

    def add_image(image, caption):
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)
        scale = min(width / image.width, 325 / image.height)
        story.append(KeepTogether([Image(buffer, width=image.width * scale, height=image.height * scale),
            Spacer(1, 5), Paragraph(inline(caption), caption_style), Spacer(1, 9)]))

    lines = source.read_text(encoding="utf-8").splitlines()
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
            content = [[Paragraph(inline(c), cell_style) for c in row] for row in cells]
            table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT", splitInRow=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2eaf6")),
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

    target.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=40, leftMargin=40,
        topMargin=38, bottomMargin=42, title=lines[0].lstrip("# ") if lines else "KittyCatch", author="KittyCatch")
    document.build(story, onFirstPage=footer, onLaterPages=footer)


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
