"""Lays out the graded Schlaubi photos with captions and a cover page in VectorCraft (headless MCP)."""
import json
import sys

sys.path.insert(0, sys.argv[1])
from mcp_client import Mcp  # noqa: E402

BIN, ROOT = sys.argv[2], sys.argv[3]   # ROOT contains graded/ (read) and out/ (write)
W, H, BAR = 1600, 1100, 160

ITEMS = [
    ("desk", "01", "Hört zu", "Nach „Schlaubi“ leuchtet der ganze Würfel blau durch das matte Acryl."),
    ("cafe", "02", "Unterwegs im Café", "Er spricht über deine Kopfhörer, ohne Kopfhörer kommt die Antwort aufs Handy."),
    ("show", "03", "Dinge zeigen", "Kamera an heißt hell weiß und zwei Klicks. Das Bild geht ohne Metadaten an Claude."),
    ("insight", "04", "Erkenntnis", "Etwas Neues gelernt: goldener Schimmer und ein Dur-Dreiklang."),
    ("cooling", "05", "Umgebung und Kühlung", "Zuluft, Abluft, Licht und Geräusche, jede Minute gemessen und ausgewertet."),
    ("brain", "06", "Das Gehirn zu Hause", "Alter Laptop als Server, Sicherung auf externer Platte. Violett: Schlaubi recherchiert."),
    ("analysis", "07", "Code und Auswertung", "Er schreibt Auswertungen selbst in der Sandbox und berichtet per Telegram."),
]


def text_of(res):
    return " ".join(c.get("text", "") for c in res[0].get("content", []) if c.get("type") == "text")


def place_at(m, path, x, y, width=None):
    res = m.call("run_command", command="file.place", params={"path": path})
    ids = json.loads(text_of(res))["ids"]

    def bounds():
        b = find(json.loads(text_of(m.call("inspect_document", depth=3))), ids[0])["bounds"]
        return b["x"], b["y"], b["width"]

    bx, by, bw = bounds()
    if width and abs(bw - width) > 0.5:
        m.call("transform", ids=ids, scale=width / bw * 100)
        bx, by, bw = bounds()
    m.call("transform", ids=ids, dx=x - bx, dy=y - by)
    return ids


def find(doc, oid):
    stack = list(doc.get("layers", []))
    while stack:
        n = stack.pop()
        if n.get("id") == oid:
            return n
        stack.extend(n.get("children", []))
    raise KeyError(oid)


def caption_page(m, name, num, title, text):
    m.call("run_command", command="file.new", params={"width": W, "height": H + BAR, "units": "Pixels"})
    place_at(m, f"{ROOT}/graded/graded_{name}.png", 0, 0, width=W)
    m.call("draw_shape", shape="rectangle", x=0, y=H, width=W, height=BAR, fill="#181a1e", stroke="none")
    m.call("draw_shape", shape="rectangle", x=48, y=H + 34, width=6, height=92, fill="#4f8fd6", stroke="none")
    m.call("add_text", text=f"{num}  {title}", x=74, y=H + 72, size=44, color="#f0f0f0")
    m.call("add_text", text=text, x=74, y=H + 120, size=28, color="#b9bec6")
    m.call("add_text", text="Schlaubi · Version 1", x=W - 48, y=H + 72, size=26, color="#7a8088", justify="right")
    m.call("export", path=f"{ROOT}/out/schlaubi-{num}-{name}.png", options={"ppi": 72, "background": "white", "antiAlias": "type"})


def cover(m):
    CW, CH = 1600, 1260
    m.call("run_command", command="file.new", params={"width": CW, "height": CH, "units": "Pixels"})
    m.call("draw_shape", shape="rectangle", x=0, y=0, width=CW, height=CH, fill="#15171b", stroke="none")
    place_at(m, f"{ROOT}/graded/graded_insight.png", 0, 0, width=CW)
    m.call("draw_shape", shape="rectangle", x=0, y=1100, width=CW, height=160, fill="#15171b", stroke="none")
    m.call("add_text", text="Schlaubi", x=72, y=1196, size=96, color="#f3e6cf")
    m.call("add_text", text="Ein KI-Würfel mit eigenem Kopf. Bilderreihe, Version 1.", x=560, y=1172, size=30, color="#c9c2b5")
    m.call("add_text", text="Holz, mattes Acryl, Licht in Laune-Farben. Hört zu, merkt sich alles Wichtige, spricht Hessisch.", x=560, y=1214, size=24, color="#8f887d")
    m.call("export", path=f"{ROOT}/out/schlaubi-00-titel.png", options={"ppi": 72, "background": "white", "antiAlias": "type"})


if __name__ == "__main__":
    m = Mcp(BIN, ROOT, ROOT + "/out")
    cover(m)
    for it in ITEMS:
        caption_page(m, *it)
    m.close()
