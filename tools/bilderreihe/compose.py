"""Adds caption bars to the final renders and builds an overview sheet."""
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]
FONT_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)

ITEMS = [
    ("desk", "01", "Hört zu", "Nach „Schlaubi“ leuchtet der ganze Würfel blau durch das matte Acryl."),
    ("cafe", "02", "Unterwegs im Café", "Er spricht über deine Kopfhörer, ohne Kopfhörer kommt die Antwort aufs Handy."),
    ("show", "03", "Dinge zeigen", "Kamera an heißt: hell weiß, zwei Klicks. Das Bild geht ohne Metadaten an Claude."),
    ("insight", "04", "Erkenntnis", "Etwas Neues gelernt: goldener Schimmer und ein Dur-Dreiklang."),
    ("cooling", "05", "Umgebung und Kühlung", "Zuluft, Abluft, Licht und Geräusche, jede Minute gemessen und ausgewertet."),
    ("brain", "06", "Das Gehirn zu Hause", "Alter Laptop als Server, Sicherung auf externer Platte, Schlaubi recherchiert (violett)."),
    ("analysis", "07", "Code und Auswertung", "Er schreibt Auswertungen selbst in der Sandbox und berichtet per Telegram."),
]


def caption(name, num, title, text):
    im = Image.open(f"{SRC}/final_{name}.png").convert("RGB")
    w, h = im.size
    bar = 150
    out = Image.new("RGB", (w, h + bar), (24, 26, 30))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    d.text((48, h + 26), f"{num}  {title}", font=FONT_B, fill=(240, 240, 240))
    d.text((48, h + 88), text, font=FONT, fill=(185, 190, 198))
    d.text((w - 48, h + 34), "Schlaubi · Version 1", font=FONT, fill=(120, 126, 134), anchor="ra")
    path = f"{DST}/schlaubi-{num}-{name}.jpg"
    out.save(path, quality=90)
    return out


def sheet(images):
    tw = 800
    thumbs = [im.resize((tw, int(im.height * tw / im.width))) for im in images]
    th = thumbs[0].height
    cols, rows = 2, (len(thumbs) + 1) // 2
    s = Image.new("RGB", (cols * tw, rows * th), (24, 26, 30))
    for i, t in enumerate(thumbs):
        s.paste(t, ((i % cols) * tw, (i // cols) * th))
    s.save(f"{DST}/schlaubi-uebersicht.jpg", quality=88)


if __name__ == "__main__":
    ims = [caption(*it) for it in ITEMS]
    sheet(ims)
