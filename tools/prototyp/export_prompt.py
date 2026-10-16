"""Export Schlaubi's prompt parts and test questions for the chat prototype (Wegwerf-Prototyp A).

Reads the real fixed core, profile, prompt builder and test questions from brain/, so the
prototype speaks with exactly the character in the code. Writes JSON to stdout; the page
`tools/prototyp/schlaubi-chat.html` embeds it. Rebuild after profile or core changes.

Usage: .venv/bin/python tools/prototyp/export_prompt.py [--html OUT.html]
Without --html the data goes to stdout as JSON; with --html the page is written from
schlaubi-chat.template.html (outside the repo, e.g. into the scratchpad, for publishing).
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from brain.character.core import CORE_FILE  # noqa: E402
from brain.character.exam import AI_STOCK_PHRASES, load_questions, max_sentences  # noqa: E402
from brain.character.mood import Mood  # noqa: E402
from brain.character.profile import load_profile  # noqa: E402
from brain.character.prompt import _length_line, _mood_line, build_system_prompt  # noqa: E402

LAUNEN = {
    "ruhig": Mood(0.0, 0.0, 0.0, "nichts Besonderes"),
    "gut": Mood(0.6, 0.5, -0.3, "die Kühlung läuft ruhig und Marvin war gestern lange da"),
    "grantig": Mood(-0.7, -0.4, 0.65, "schon die dritte Smalltalk-Frage heute und Akku bei 12 %", (("smalltalk", 0.75),)),
    "muede": Mood(-0.1, -0.7, 0.1, "spät am Abend, Akku bei 20 %"),
    "ernst": Mood(0.0, 0.0, 0.0, "ernstes Thema", damped=True),
}


def main():
    core = CORE_FILE.read_text(encoding="utf-8")
    profile = load_profile()
    stable = build_system_prompt(core, profile, LAUNEN["ruhig"], now=datetime.now(UTC)).stable
    daten = {
        "stable": stable,
        "launen": {name: _mood_line(mood) for name, mood in LAUNEN.items()},
        "laenge": {"normal": _length_line(profile, False), "mehr": _length_line(profile, True)},
        "max_saetze": max_sentences(profile),
        "floskeln": list(AI_STOCK_PHRASES),
        "pruefragen": load_questions(),
    }
    text = json.dumps(daten, ensure_ascii=False)
    if len(sys.argv) == 3 and sys.argv[1] == "--html":
        template = Path(__file__).with_name("schlaubi-chat.template.html").read_text(encoding="utf-8")
        safe = text.replace("</", "<\\/")  # no "</script>" inside the embedded JSON
        Path(sys.argv[2]).write_text(template.replace("/*DATEN*/", safe), encoding="utf-8")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
