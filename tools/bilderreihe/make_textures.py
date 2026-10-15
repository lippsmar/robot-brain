"""Screen textures for the Schlaubi renders: chat on a phone, charts on a laptop."""
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def wrap(draw, text, font, width):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def phone_chat():
    W, H = 900, 1950
    img = Image.new("RGB", (W, H), (236, 229, 221))
    d = ImageDraw.Draw(img)
    f_head = ImageFont.truetype(FONT_B, 46)
    f_sub = ImageFont.truetype(FONT, 30)
    f_msg = ImageFont.truetype(FONT, 38)
    f_time = ImageFont.truetype(FONT, 24)
    d.rectangle([0, 0, W, 230], fill=(44, 94, 142))
    d.ellipse([40, 90, 140, 190], fill=(120, 190, 255))
    d.text((170, 95), "Schlaubi", font=f_head, fill="white")
    d.text((170, 152), "Bot · denkt nach …", font=f_sub, fill=(205, 225, 245))
    msgs = [
        ("me", "Wie warm war's heute im Würfel?", "17:42"),
        ("bot", "Zuluft 22,4\u00a0°C, Abluft 27,9\u00a0°C, Chip max. 58\u00a0°C. Kühlung reicht, solang de mich net in die Sonne stellst.", "17:42"),
        ("me", "Und was war heute los?", "17:43"),
        ("bot", "Büro bis 15\u00a0Uhr, dann Café. Dreimal Kaffeemaschine, einmal Regen. Ruhigste Stunde: 10 bis 11.", "17:43"),
        ("bot", "Neuer Update-Vorschlag is da. Drei Punkte, alle mit Quellen. Guckste drüber?", "17:44"),
    ]
    y = 280
    for who, text, t in msgs:
        maxw = 600
        lines = wrap(d, text, f_msg, maxw - 60)
        h = 40 + len(lines) * 50 + 40
        wbox = max(d.textlength(l, font=f_msg) for l in lines) + 60
        wbox = max(wbox, 200)
        if who == "me":
            x1 = W - 40 - wbox
            col = (220, 248, 198)
        else:
            x1 = 40
            col = (255, 255, 255)
        d.rounded_rectangle([x1, y, x1 + wbox, y + h], radius=28, fill=col)
        for i, l in enumerate(lines):
            d.text((x1 + 30, y + 30 + i * 50), l, font=f_msg, fill=(30, 30, 30))
        d.text((x1 + wbox - 90, y + h - 36), t, font=f_time, fill=(130, 130, 130))
        y += h + 28
    d.rectangle([0, H - 140, W, H], fill=(250, 250, 250))
    d.rounded_rectangle([30, H - 115, W - 140, H - 30], radius=40, fill=(240, 240, 240))
    d.text((70, H - 92), "Nachricht", font=f_sub, fill=(150, 150, 150))
    d.ellipse([W - 115, H - 115, W - 30, H - 30], fill=(44, 94, 142))
    img.save(f"{OUT}/phone_chat.png")


def laptop_chart():
    hours = [h / 4 for h in range(0, 24 * 4)]
    zuluft = [21.5 + 1.5 * math.sin((h - 9) / 24 * 2 * math.pi) for h in hours]
    last = [1.0 if 9 <= h <= 18 else 0.3 for h in hours]
    abluft = [z + 2.5 + 3.5 * l + 0.4 * math.sin(h * 3) for z, l, h in zip(zuluft, last, hours)]
    chip = [z + 18 + 22 * l + 2 * math.sin(h * 2.3) for z, l, h in zip(zuluft, last, hours)]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=110, gridspec_kw={"width_ratios": [2, 1]})
    fig.patch.set_facecolor("#1d2229")
    ax = axes[0]
    ax.set_facecolor("#1d2229")
    ax.plot(hours, chip, color="#ff8a5c", lw=2.2, label="Chip")
    ax.plot(hours, abluft, color="#ffd166", lw=2.2, label="Abluft")
    ax.plot(hours, zuluft, color="#7cc4ff", lw=2.2, label="Zuluft")
    ax.axhline(70, color="#ff5c5c", lw=1, ls="--")
    ax.text(0.3, 71, "Warngrenze 70 °C", color="#ff8a8a", fontsize=11)
    ax.set_xlim(0, 24)
    ax.set_ylim(15, 80)
    ax.set_xlabel("Uhrzeit", color="#c9d1d9")
    ax.set_ylabel("°C", color="#c9d1d9")
    ax.set_title("Kühlung heute", color="white", loc="left", fontsize=17)
    ax.tick_params(colors="#9aa4ad")
    for s in ax.spines.values():
        s.set_color("#3a424c")
    ax.legend(facecolor="#1d2229", edgecolor="#3a424c", labelcolor="#c9d1d9", loc="upper left")
    ax2 = axes[1]
    ax2.set_facecolor("#1d2229")
    classes = ["Stille", "Sprache", "Kaffeemaschine", "Musik", "Verkehr", "Regen"]
    vals = [41, 23, 9, 12, 10, 5]
    cols = ["#7cc4ff", "#9b8cff", "#ffd166", "#5ce1a6", "#ff8a5c", "#9aa4ad"]
    ax2.barh(classes[::-1], vals[::-1], color=cols[::-1])
    ax2.set_title("Geräusche (%)", color="white", loc="left", fontsize=17)
    ax2.tick_params(colors="#9aa4ad")
    for s in ax2.spines.values():
        s.set_color("#3a424c")
    fig.tight_layout(pad=2)
    fig.savefig(f"{OUT}/laptop_chart.png", facecolor=fig.get_facecolor())


if __name__ == "__main__":
    phone_chat()
    laptop_chart()
