---
name: "effectcraft-agent"
description: "EffectCraft (After Effects-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Motion Graphics und visuelle Effekte: Kompositionen, Ebenen, Keyframes, Effekte, Render-Warteschlange. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# EffectCraft für Agenten

Nachbau von Adobe After Effects aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/effectcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the EffectCraft contributors). Geprüft am 13.10.2026 (Version 0.9.2, Commit 549e9d8), Status laut Projekt: jung, ändert sich schnell. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Steuerkanal (`--control`) nur auf 127.0.0.1, laut Doku **ohne Token**: Jedes Programm auf dem Rechner kann die laufende App dann steuern. App deshalb nur bei Bedarf mit `--control` starten, sonst headless arbeiten.
- Ordnerbeschränkung für Agenten: Ja: `--automation-read-root` und `--automation-write-root`.

## Starten
```sh
effectcraft-cli mcp --automation-read-root /arbeit/effekte --automation-write-root /arbeit/effekte/ausgabe
# mit laufender App (vorher: effectcraft --control 9877)
effectcraft-cli mcp --bridge 9877 --automation-read-root /arbeit/effekte --automation-write-root /arbeit/effekte/ausgabe
# einzelne Aufrufe ohne MCP
effectcraft-cli render --comp Main --out main.mp4
```

In Claude Code registrieren (erst nach Freigabe): `claude mcp add effectcraft -- /pfad/zu/effectcraft-cli mcp …` mit denselben Optionen wie oben.

## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- Mit Roots werden Skripte (`run_script`, `file.runScript`), „Execute File“ und die UI-Werkzeuge der Bridge abgelehnt. Das ist gewollt, nicht umgehen.
- Datei-Parameter müssen absolute Pfade innerhalb der Roots sein.
- `command_batch` stoppt beim ersten Fehler. Das ältere Werkzeug `batch` fasst alles in einen Undo-Schritt.
- **Modell-Download** (MediaPipe Face Landmarker von storage.googleapis.com, per `curl`) nur nach Freigabe. Gesichtsdaten sind personenbezogen.
- Rendern läuft im Hintergrund: Fortschritt mit `progressToken`.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
