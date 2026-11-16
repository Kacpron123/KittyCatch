"""Publication-friendly, headless plots of measured genetic telemetry (Pillow)."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = "#19334f"
PALETTE = ("#1565a8", "#009688", "#ed8d32", "#9a57b7", "#d94c66", "#68788c")


def font(size=18, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size)


def canvas(title, subtitle="", height=720):
    image = Image.new("RGB", (1320, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), title, font=font(27, True), fill=INK)
    draw.text((45, 65), subtitle, font=font(16), fill="#53687d")
    return image, draw


def lines(path, title, series, *, subtitle="", y_label="", bands=None, ylim=None):
    image, draw = canvas(title, subtitle)
    points = [p for values in series.values() for p in values]
    if bands:
        points += [(x, lo) for x, lo, hi in bands] + [(x, hi) for x, lo, hi in bands]
    xmin, xmax = min(x for x, y in points), max(x for x, y in points)
    ymin, ymax = ylim or (min(y for x, y in points), max(y for x, y in points))
    if xmax == xmin:
        xmax += 1
    pad = max((ymax-ymin)*0.08, abs(ymax)*0.02, 0.0001)
    if not ylim:
        ymin, ymax = ymin-pad, ymax+pad
    if ymax == ymin:
        ymax += 1
    def xy(x, y):
        return 110 + (x-xmin)/(xmax-xmin)*1130, 575-(y-ymin)/(ymax-ymin)*435
    for i in range(6):
        value = ymin+(ymax-ymin)*i/5
        y = xy(xmin, value)[1]
        draw.line((110, y, 1240, y), fill="#dde6ed")
        draw.text((15, y-10), f"{value:.3g}", font=font(16), fill=INK)
    epochs = sorted(set(int(x) for x, y in points))
    step = max(1, math.ceil(len(epochs)/12))
    for value in epochs[::step]:
        x = xy(value, ymin)[0]
        draw.text((x, 590), str(value), anchor="mt", font=font(16), fill=INK)
    draw.text((110, 105), y_label, font=font(17), fill=INK)
    draw.text((1240, 620), "Epoka oceny", anchor="rt", font=font(17), fill=INK)
    if bands:
        polygon = [xy(x, lo) for x, lo, hi in bands] + [xy(x, hi) for x, lo, hi in reversed(bands)]
        draw.polygon(polygon, fill="#dceaf7")
    xlegend = 110
    for i, (label, values) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        coords = [xy(x, y) for x, y in values]
        if len(coords)>1:
            draw.line(coords, fill=color, width=3)
        for x, y in coords:
            draw.ellipse((x-2.5,y-2.5,x+2.5,y+2.5), fill=color)
        if xlegend > 1000:
            xlegend = 110
        draw.line((xlegend, 665, xlegend+25, 665), fill=color, width=4)
        draw.text((xlegend+35, 653), label, font=font(16), fill=INK)
        xlegend += draw.textlength(label, font=font(16)) + 85
    image.save(path)


def heatmap(path, title, matrix, *, subtitle="", column_labels=None, vmin=0, vmax=1):
    rows, columns = len(matrix), len(matrix[0])
    image, draw = canvas(title, subtitle, height=max(640, 190+rows*22))
    left, top, width = 95, 125, 1150
    cellw, cellh = width/columns, min(24, (image.height-225)/rows)
    for r, row in enumerate(matrix):
        draw.text((75, top+(r+0.5)*cellh), str(r+1), font=font(13), anchor="rm", fill=INK)
        for c, value in enumerate(row):
            t = max(0, min(1, (value-vmin)/max(vmax-vmin, 1e-12)))
            color = (int(242-220*t), int(247-100*t), int(250-45*t))
            draw.rectangle((left+c*cellw, top+r*cellh, left+(c+1)*cellw, top+(r+1)*cellh), fill=color)
        draw.line((left, top+(r+1)*cellh, left+width, top+(r+1)*cellh), fill="white")
    for c in range(columns):
        label = column_labels[c] if column_labels else str(c+1)
        draw.text((left+(c+0.5)*cellw, top+rows*cellh+10), label, font=font(10), anchor="mt", fill=INK)
        if column_labels and c % 4 == 0:
            draw.line((left+c*cellw,top,left+c*cellw,top+rows*cellh), fill="white", width=2)
    draw.text((15, top-25), "Epoka", font=font(16), fill=INK)
    bottom = image.height-55
    for i in range(200):
        t=i/199
        draw.line((left+i*2,bottom,left+i*2,bottom+15),fill=(int(242-220*t),int(247-100*t),int(250-45*t)),width=2)
    draw.text((left,bottom+20),f"{vmin:.3g}",font=font(13),fill=INK)
    draw.text((left+400,bottom+20),f"{vmax:.3g}",anchor="rt",font=font(13),fill=INK)
    image.save(path)


def bars(path, title, values, *, subtitle="", ylabel="", expected=None, errors=None):
    image, draw = canvas(title, subtitle)
    maximum = max([value for value in values.values()] + ([expected] if expected is not None else []))
    if errors:
        maximum = max(maximum, max(values[k] + errors.get(k, 0) for k in values))
    maximum = max(0.001, maximum)*1.15
    count = len(values)
    left, right, top, bottom = 110, 1240, 140, 570
    for j in range(6):
        y=bottom-j*(bottom-top)/5
        draw.line((left,y,right,y),fill="#dde6ed")
        draw.text((15,y-10),f"{maximum*j/5:.3g}",font=font(16),fill=INK)
    draw.text((left,105),ylabel,font=font(17),fill=INK)
    step=(right-left)/count
    for i,(name,value) in enumerate(values.items()):
        x=left+(i+0.15)*step
        y=bottom-value/maximum*(bottom-top)
        draw.rectangle((x,y,x+step*.7,bottom),fill=PALETTE[i%len(PALETTE)])
        if count<=12:
            draw.text((x+step*.35,y-10),f"{value:.3g}",anchor="mb",font=font(15),fill=INK)
        if errors:
            half=errors.get(name,0)/maximum*(bottom-top)
            cx=x+step*.35
            draw.line((cx,y-half,cx,y+half),fill=INK,width=2)
            draw.line((cx-6,y-half,cx+6,y-half),fill=INK,width=2)
            draw.line((cx-6,y+half,cx+6,y+half),fill=INK,width=2)
        draw.text((x+step*.35,bottom+15),name,anchor="mt",font=font(10 if count>15 else 15),fill=INK)
    if expected is not None:
        y=bottom-expected/maximum*(bottom-top)
        for x in range(left,right,15):
            draw.line((x,y,x+8,y),fill="#b32642",width=2)
        draw.text((right,620),f"Wartość oczekiwana: {expected:.3f}",anchor="rt",font=font(16),fill="#b32642")
    image.save(path)


def operator_diagram(path, birth, parents):
    image,draw=canvas("Przykład rzeczywistego krzyżowania i mutacji", "Każdy prostokąt to gen w [0,1]; czerwone obramowanie oznacza próbę mutacji.")
    rows=[("Rodzic A",parents[0]),("Rodzic B",parents[1]),("Po krzyżowaniu",birth["before_mutation"]),("Potomek",birth["genes"])]
    cellw=1100/len(birth["genes"])
    mutated={m["gene"] for m in birth["mutations"]}
    for i,(label,genes) in enumerate(rows):
        y=150+i*110
        draw.text((45,y-25),label,font=font(18,True),fill=INK)
        for j,value in enumerate(genes):
            x=110+j*cellw
            t=max(0,min(1,value))
            color=(int(235-200*t),int(245-90*t),int(250-45*t))
            draw.rectangle((x,y,x+cellw-1,y+48),fill=color,outline="#c8d6e2")
            draw.text((x+cellw/2,y+24),f"{value:.2f}",anchor="mm",font=font(9),fill="white" if t>.65 else INK)
            if i==3 and j in mutated:
                draw.rectangle((x,y,x+cellw-1,y+48),outline="#d33150",width=3)
            if i==2:
                draw.rectangle((x,y+53,x+cellw-1,y+64),fill=PALETTE[birth["source_mask"][j]])
    draw.text((45,625),f"Fitness rodziców: {birth['parent_fitness'][0]:.5f}, {birth['parent_fitness'][1]:.5f}  |  "
        f"Fitness potomka: {birth['fitness']:.5f}  |  Δ względem lepszego rodzica: {birth['fitness_delta_vs_parent']:+.5f}",font=font(17),fill=INK)
    draw.text((45,665),"Pasek pod krzyżowaniem: niebieski = rodzic A, zielony = rodzic B. To przykład, nie dowód przyczynowy poprawy.",font=font(16),fill=INK)
    image.save(path)


def scatter(path, records):
    image,draw=canvas("Odległość genotypu a jakość rozwiązania", "Odległość RMS od najlepszego chromosomu epoki 1; kolor od niebieskiego (początek) do zielonego (koniec).")
    reference=records[0]["best_genes"]
    points=[]
    for epoch,record in enumerate(records):
        for p in record["population"]:
            distance=math.sqrt(sum((a-b)**2 for a,b in zip(reference,p["genes"]))/len(reference))
            points.append((distance,p["fitness"],epoch))
    xmax=max(x for x,y,e in points)*1.05 or 1
    ymin,ymax=min(y for x,y,e in points),max(y for x,y,e in points)
    span=max(1e-6,ymax-ymin)
    ymin-=span*.05
    ymax+=span*.05
    for i in range(6):
        y=570-i*430/5
        draw.line((110,y,1240,y),fill="#dde6ed")
        draw.text((15,y-10),f"{ymin+(ymax-ymin)*i/5:.3g}",font=font(16),fill=INK)
        draw.text((110+i*1130/5,590),f"{xmax*i/5:.2f}",anchor="mt",font=font(16),fill=INK)
    for x,y,e in points:
        t=e/max(1,len(records)-1)
        color=(int(30-15*t),int(90+80*t),int(180-30*t))
        px,py=110+x/xmax*1130,570-(y-ymin)/(ymax-ymin)*430
        draw.ellipse((px-3,py-3,px+3,py+3),fill=color)
    draw.text((110,105),"Fitness",font=font(17),fill=INK)
    draw.text((1240,640),"Odległość RMS genotypów",anchor="rt",font=font(18),fill=INK)
    image.save(path)
