"""Claude-Code-Hook (PreToolUse): Änderungen am festen Kern nur nach Rückfrage bei Marvin.

brain/character/kern.md ist Schlaubis fester Kern (Rangfolge, Grenzen). Er wird nur in der Datei
geändert, nie im Gespräch. Will Claude ihn bearbeiten (Edit, Write oder ein Bash-Befehl, der die
Datei nennt), fragt Claude Code Marvin vorher. Nur Standardbibliothek.
"""

import json
import os
import sys
from pathlib import Path

KERN = Path("brain") / "character" / "kern.md"
GRUND = "Das ist Schlaubis fester Kern (brain/character/kern.md). Nur mit Marvins Ja ändern."


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    tool = event.get("tool_name") or ""
    data = event.get("tool_input") or {}
    if tool == "Bash":
        hit = "kern.md" in (data.get("command") or "")
    else:
        path = data.get("file_path") or data.get("notebook_path") or ""
        # a relative path counts from the session's folder (cwd), or from the project if none is given
        base = Path(event.get("cwd") or root)
        target = Path(path) if Path(path).is_absolute() else base / path
        hit = bool(path) and target.resolve() == (root / KERN).resolve()
    if not hit:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": GRUND,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
