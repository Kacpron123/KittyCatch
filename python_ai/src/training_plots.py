"""Headless PNG charts using the project's existing Pillow dependency."""
from pathlib import Path
from PIL import Image, ImageDraw

COLORS = ("#75baff", "#75ddaa", "#ffb570", "#dc99ff", "#ff7888")


def line_chart(path: Path, title: str, x_label: str, y_label: str,
               series: dict[str, list[tuple[float, float]]]) -> None:
    image = Image.new("RGB", (1100, 650), "#171923")
    draw = ImageDraw.Draw(image)
    points = [point for values in series.values() for point in values]
    if not points:
        raise ValueError("Cannot plot empty series")
    xmax = max(1, max(x for x, _ in points))
    ymax = max(1, max(y for _, y in points)) * 1.08
    draw.text((80, 22), title, fill="white", font_size=24)
    for i in range(6):
        y = 550 - i * 90
        draw.line((80, y, 1040, y), fill="#34394b")
        draw.text((10, y - 8), f"{ymax * i / 5:.1f}", fill="white", font_size=16)
        x = 80 + i * 192
        draw.text((x, 560), f"{xmax * i / 5:.1f}", fill="white", font_size=16)
    draw.text((80, 75), y_label, fill="white", font_size=16)
    draw.text((960, 605), x_label, fill="white", font_size=16)
    for index, (name, values) in enumerate(series.items()):
        color = COLORS[index % len(COLORS)]
        coords = [(80 + 960 * x / xmax, 550 - 450 * y / ymax) for x, y in values]
        if len(coords) > 1:
            draw.line(coords, fill=color, width=3)
        else:
            x, y = coords[0]
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)
        draw.text((330 + index * 140, 75), name, fill=color, font_size=16)
    image.save(path)


def comparison_chart(path: Path, comparisons: dict[str, dict]) -> None:
    image = Image.new("RGB", (1100, 650), "#171923")
    draw = ImageDraw.Draw(image)
    draw.text((60, 25), "Holdout: mean base damage (min-max across seeds)", fill="white", font_size=24)
    maximum = max(1, max(max(r["damage"] for r in v["episodes"]) for v in comparisons.values()))
    for i, (name, stats) in enumerate(comparisons.items()):
        y = 120 + i * min(85, 450 / len(comparisons))
        values = [r["damage"] for r in stats["episodes"]]
        draw.text((30, y), name, fill="white", font_size=18)
        end = 230 + 680 * stats["mean_damage"] / maximum
        draw.rectangle((230, y, max(231, end), y + 30), fill=COLORS[i % len(COLORS)])
        low, high = (230 + 680 * v / maximum for v in (min(values), max(values)))
        draw.line((low, y + 15, high, y + 15), fill="white", width=2)
        for x in (low, high):
            draw.line((x, y + 8, x, y + 22), fill="white", width=2)
        draw.text((930, y), f"{stats['mean_damage']:.2f}", fill="white", font_size=18)
    image.save(path)
