"""Claude-Code-Hook (PostToolUse): nach jeder Änderung an einer Python-Datei ruff format und ruff check.

Formatiert die Datei und meldet Lint-Fehler sofort an Claude (Exit-Code 2, Text auf stderr), statt
erst am Paketende. Dateien, die ruff laut pyproject.toml nicht prüft, bleiben unberührt
(--force-exclude). Ohne .venv macht der Hook nichts. Nur Standardbibliothek.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(".py"):
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    ruff = root / ".venv" / "bin" / "ruff"
    target = Path(path).resolve()
    if not ruff.exists() or not target.exists() or not target.is_relative_to(root):
        return 0
    base = [str(ruff)]
    try:
        subprocess.run(  # noqa: S603  fixed arguments, no shell
            [*base, "format", "--force-exclude", "-q", str(target)], cwd=root, timeout=30, check=False
        )
        result = subprocess.run(  # noqa: S603  fixed arguments, no shell
            [*base, "check", "--force-exclude", "-q", str(target)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 0
    if result.returncode != 0:
        print(f"ruff check meldet Fehler in {target.relative_to(root)}:\n{result.stdout.strip()}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
