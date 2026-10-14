"""Draws the Schlaubi cube illustration with VectorCraft (headless MCP)."""
import math
import sys

sys.path.insert(0, sys.argv[1])  # scripts dir
from mcp_client import Mcp  # noqa: E402

BIN, ROOT = sys.argv[2], sys.argv[3]
OUT = ROOT + "/out"

W, H = 1200, 1000
O = (560.0, 520.0)   # cube centre on screen
S = 300.0            # edge length on screen
FRAME = 0.075        # wood frame width in cube units

C30, S30 = math.cos(math.radians(30)), 0.5


def iso(x, y, z):
    """Cube coords 0..1 to screen; x runs right-down, y left-down, z up."""
    x, y, z = x - 0.5, y - 0.5, z - 0.5
    return (O[0] + S * (x * C30 - y * C30), O[1] + S * (x * S30 + y * S30 - z))


# A face is given by an origin and two axis vectors in cube space.
FACES = {
    "top":   ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "right": ((1, 0, 1), (0, 1, 0), (0, 0, -1)),   # x = 1, side
    "front": ((0, 1, 1), (1, 0, 0), (0, 0, -1)),   # y = 1, front with camera
}


def face_pt(face, u, v):
    o, a, b = FACES[face]
    return iso(*(o[i] + u * a[i] + v * b[i] for i in range(3)))


def quad(face, u0, v0, u1, v1):
    return [face_pt(face, u0, v0), face_pt(face, u1, v0),
            face_pt(face, u1, v1), face_pt(face, u0, v1)]


def blob(face, cu, cv, ru, rv, n=48):
    return [face_pt(face, cu + ru * math.cos(2 * math.pi * i / n),
                    cv + rv * math.sin(2 * math.pi * i / n)) for i in range(n)]


def r(pts):
    return [[round(x, 2), round(y, 2)] for x, y in pts]


def main():
    m = Mcp(BIN, ROOT, ROOT + "/out")
    m.call("run_command", command="file.new", params={"width": W, "height": H})

    def path(pts, fill, stroke="none", sw=0, closed=True):
        args = {"points": r(pts), "closed": closed, "fill": fill, "stroke": stroke}
        if sw:
            args["strokeWidth"] = sw
        return m.call("draw_path", **args)

    def line(a, b, color, sw):
        return m.call("draw_path", points=r([a, b]), closed=False, fill="none",
                      stroke=color, strokeWidth=sw)

    def text(t, x, y, size, color="#2b2b2b", justify="left", font=None):
        args = {"text": t, "x": x, "y": y, "size": size, "color": color, "justify": justify}
        if font:
            args["font"] = font
        return m.call("add_text", **args)

    # Background
    m.call("draw_shape", shape="rectangle", x=0, y=0, width=W, height=H, fill="#f6f2ea", stroke="none")

    # Desk shadow and soft blue glow on the desk
    for i, (col, k) in enumerate([("#ebf0f4", 1.25), ("#dfe9f3", 1.12), ("#d2e2f1", 1.02)]):
        cx, cy = O[0], O[1] + S * 0.98
        m.call("draw_shape", shape="ellipse", x=cx - S * 0.95 * k, y=cy - S * 0.32 * k,
               width=S * 1.9 * k, height=S * 0.64 * k, fill=col, stroke="none")
    cx, cy = O[0], O[1] + S * 1.0
    m.call("draw_shape", shape="ellipse", x=cx - S * 0.8, y=cy - S * 0.2,
           width=S * 1.6, height=S * 0.4, fill="#b9c3cc", stroke="none")

    wood = {"top": "#c8935a", "right": "#9c6a37", "front": "#b57d45"}
    panel = {"top": "#bfe0ff", "right": "#8cc4f2", "front": "#a6d3fa"}
    glow1 = {"top": "#dbeeff", "right": "#b3dafa", "front": "#c7e5fd"}
    glow2 = {"top": "#f2f9ff", "right": "#d6ecfd", "front": "#e6f4ff"}

    for f in ("right", "front", "top"):
        path(quad(f, 0, 0, 1, 1), wood[f])                       # wooden frame
        path(quad(f, FRAME, FRAME, 1 - FRAME, 1 - FRAME), panel[f])  # acrylic panel
        path(blob(f, 0.5, 0.5, 0.34, 0.34), glow1[f])            # light from inside
        path(blob(f, 0.5, 0.5, 0.2, 0.2), glow2[f])

    # Edge highlights and dark outlines for crisp edges
    for f in ("right", "front", "top"):
        path(quad(f, 0, 0, 1, 1), "none", "#5a3a1c", 2.2)
        path(quad(f, FRAME, FRAME, 1 - FRAME, 1 - FRAME), "none", "#6f4a26", 1.2)

    # Wood grain hints on the frame
    for f in ("front", "right"):
        for v in (0.25, 0.55, 0.8):
            line(face_pt(f, FRAME * 0.3, v), face_pt(f, FRAME * 0.3, v + 0.12), "#8a5a2c", 1)
            line(face_pt(f, 1 - FRAME * 0.4, v - 0.1), face_pt(f, 1 - FRAME * 0.4, v + 0.02), "#8a5a2c", 1)

    # Front: camera window, lens and mic holes
    path(blob("front", 0.5, 0.27, 0.11, 0.11), "#2d3440", "#1b1f26", 1.5)
    path(blob("front", 0.5, 0.27, 0.07, 0.07), "#11151b")
    path(blob("front", 0.5, 0.27, 0.035, 0.035), "#3c5f8a")
    path(blob("front", 0.475, 0.245, 0.015, 0.015), "#e9f3ff")
    for du in (-0.06, 0.0, 0.06):
        path(blob("front", 0.5 + du, 0.78, 0.012, 0.012, 16), "#4b5866")

    # Side: ventilation slits and USB-C port
    for k in range(5):
        u = 0.32 + k * 0.09
        path(quad("right", u, 0.12, u + 0.035, 0.36), "#5d7d99")
    path(quad("right", 0.4, 0.84, 0.6, 0.89), "#2b2f36", "#1b1f26", 1)

    # Top: power button
    path(blob("top", 0.78, 0.22, 0.06, 0.06), "#7d522a", "#5a3a1c", 1.2)
    path(blob("top", 0.78, 0.22, 0.04, 0.04), "#d9c4a8")

    # Title
    text("Schlaubi", 60, 110, 64, "#2b2b2b")
    text("Der Würfel – Version 1 (Illustration)", 62, 150, 22, "#6b6257")

    # Callouts: (anchor point, label position, lines of text, justify)
    accent = "#2f6fae"
    callouts = [
        (face_pt("front", 0.5, 0.27), (40, 330), ["Kamera", "nur an, wenn du etwas zeigst"], "left"),
        (face_pt("front", 0.5, 0.78), (40, 790), ["Mikrofon", "hört lokal auf „Schlaubi“"], "left"),
        (face_pt("front", 0.04, 0.55), (40, 560), ["Holzrahmen", "aus deinem Bestand"], "left"),
        (face_pt("top", 0.5, 0.45), (900, 120), ["Acrylglas opal, mattweiß", "leuchtet in der Zustandsfarbe", "(blau = hört zu)"], "left"),
        (face_pt("top", 0.78, 0.22), (900, 300), ["Taster", "sauber herunterfahren"], "left"),
        (face_pt("right", 0.45, 0.24), (930, 470), ["Lüftung"], "left"),
        (face_pt("right", 0.5, 0.865), (930, 740), ["USB-C", "zum Laden"], "left"),
    ]
    for anchor, (lx, ly), lines, just in callouts:
        end_x = lx - 12 if lx > anchor[0] else lx + 235
        line(anchor, (end_x, ly - 6), accent, 1.4)
        path(blob_screen(anchor, 4.5), accent)
        for i, t in enumerate(lines):
            text(t, lx, ly + i * 24, 20 if i == 0 else 16,
                 "#1f2a36" if i == 0 else "#5d6670")

    # Size marker along the bottom-right edge of the front face
    a, b = face_pt("front", 0, 1), face_pt("front", 1, 1)
    off = (-14, 26)
    a2, b2 = (a[0] + off[0], a[1] + off[1]), (b[0] + off[0], b[1] + off[1])
    line(a2, b2, "#6b6257", 1.2)
    line((a2[0], a2[1] - 7), (a2[0], a2[1] + 7), "#6b6257", 1.2)
    line((b2[0], b2[1] - 7), (b2[0], b2[1] + 7), "#6b6257", 1.2)
    text("10 cm", (a2[0] + b2[0]) / 2 - 40, (a2[1] + b2[1]) / 2 + 36, 18, "#6b6257")

    # Footer
    text("Antwortet über Bluetooth-Kopfhörer oder -Box, sonst per Telegram.  Gezeichnet mit VectorCraft.",
         60, 960, 15, "#8a8076")

    m.call("save_file", path=OUT + "/schlaubi-wuerfel.vectorcraft")
    m.call("export", path=OUT + "/schlaubi-wuerfel.svg", outlineText=True)
    m.call("export", path=OUT + "/schlaubi-wuerfel.png",
           options={"ppi": 144, "background": "white", "antiAlias": "art"})
    m.close()


def blob_screen(c, rad, n=24):
    return [(c[0] + rad * math.cos(2 * math.pi * i / n), c[1] + rad * math.sin(2 * math.pi * i / n))
            for i in range(n)]


if __name__ == "__main__":
    main()
