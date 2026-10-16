#!/bin/bash
# Frischer Prüflauf für ein Arbeitspaket: pytest, ruff und mypy gleichzeitig, danach die
# Fehler-Einbau-Prüfung. Gibt am Ende eine Zeile pro Prüfung aus. Exit 1, wenn eine fehlschlägt.
# Aufruf: tools/dev/pruefen.sh [--voll]   (ohne --voll nur geänderte Dateien bei der Fehler-Einbau-Prüfung)
set -uo pipefail
cd "$(dirname "$0")/../.."
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

.venv/bin/python -m pytest -p no:cacheprovider > "$out/pytest" 2>&1 & p1=$!
{ .venv/bin/ruff check brain tools && .venv/bin/ruff format --check brain tools; } > "$out/ruff" 2>&1 & p2=$!
.venv/bin/mypy > "$out/mypy" 2>&1 & p3=$!
wait $p1; s1=$?; wait $p2; s2=$?; wait $p3; s3=$?

if [ "${1:-}" = "--voll" ]; then
  .venv/bin/python tools/dev/mutation_check.py > "$out/mutation" 2>&1; s4=$?
else
  .venv/bin/python tools/dev/mutation_check.py --geaendert > "$out/mutation" 2>&1; s4=$?
fi

fail=0
report() {
  if [ "$2" -eq 0 ]; then echo "OK      $1: $(tail -n 1 "$out/$3")"; else echo "FEHLER  $1:"; tail -n 25 "$out/$3"; fail=1; fi
}
report pytest $s1 pytest
report ruff $s2 ruff
report mypy $s3 mypy
grep -v "^ERKANNT" "$out/mutation" | grep -v "^Schnellmodus" > "$out/mut2" || true
report "Fehler-Einbau" $s4 mutation
[ $s4 -ne 0 ] && cat "$out/mut2"
exit $fail
