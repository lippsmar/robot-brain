#!/bin/bash
# SessionStart-Hook (nur Cloud-Sitzungen): richtet die Testumgebungen ein, damit pytest, ruff und mypy
# und der Skill social-media-ansehen sofort laufen. Pakete nur mit Prüfsummen (--require-hashes),
# wie in brain/README.md. Idempotent: Ist eine Umgebung zu den aktuellen Requirements schon
# eingerichtet, wird nichts neu installiert.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# richtet venv $1 aus den Requirements-Dateien $2... ein, nur wenn sich diese geändert haben
setup_venv() {
  local venv="$1"; shift
  local stamp="$venv/.requirements.sha256"
  local want
  want=$(cat "$@" | sha256sum | cut -d' ' -f1)
  if [ -x "$venv/bin/python" ] && [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$want" ]; then
    echo "$venv ist aktuell."
    return
  fi
  python3 -m venv "$venv"
  local args=()
  for file in "$@"; do args+=(-r "$file"); done
  "$venv/bin/pip" install -q --disable-pip-version-check --require-hashes "${args[@]}" "${EXTRA_PIP_ARGS[@]}"
  echo "$want" > "$stamp"
  echo "$venv eingerichtet."
}

EXTRA_PIP_ARGS=()
setup_venv .venv brain/requirements.txt brain/requirements-dev.txt
EXTRA_PIP_ARGS=(--no-deps --only-binary=:all:)
setup_venv .venv-social tools/social/requirements.txt
