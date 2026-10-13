---
name: "vectorcraft-agent"
description: "VectorCraft (Illustrator-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Vektorgrafik: Pfade, Formen, Text, Effekte, SVG, Export. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# VectorCraft für Agenten

Nachbau von Adobe Illustrator aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/vectorcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the VectorCraft contributors). Geprüft am 13.10.2026 (Version 0.10.0, Commit 0d0ea35), Status laut Projekt: in aktiver Entwicklung. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Steuerkanal (`--control`) nur auf 127.0.0.1, laut Doku **ohne Token**: Jedes Programm auf dem Rechner kann die laufende App dann steuern. App deshalb nur bei Bedarf mit `--control` starten, sonst headless arbeiten.
- Ordnerbeschränkung für Agenten: Ja: `--automation-read-root` und `--automation-write-root`.

## Starten
```sh
# ohne App, nur Engine
vectorcraft-cli mcp --headless --automation-read-root /arbeit/vektor --automation-write-root /arbeit/vektor/ausgabe
# mit laufender App (vorher: vectorcraft --control 7979)
vectorcraft-cli mcp --connect 127.0.0.1:7979 --automation-read-root /arbeit/vektor --automation-write-root /arbeit/vektor/ausgabe
```
Ohne Flag versucht der Server 127.0.0.1:7979 und fällt sonst auf headless zurück. Lieber den Modus fest angeben.

In Claude Code registrieren (erst nach Freigabe): `claude mcp add vectorcraft -- /pfad/zu/vectorcraft-cli mcp …` mit denselben Optionen wie oben.

## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- Eigene Werkzeuge zusätzlich zu den gemeinsamen: u. a. `draw_shape`, `draw_path`, `add_text`, `set_paint`, `transform`, `pathfinder`, `apply_effect`, `recolor`, `create_graph`, `text_wrap`, `open_file`, `save_file`, `export`, `undo`.
- Nur im Connect-Modus: `inspect_ui`, `type_text`, `open_panel`, `screenshot {window:true}`.
- Roots trennen Lesen und Schreiben. Nur ein Lese-Root heißt: nichts wird auf die Platte geschrieben. Symbolische Links aus dem Root heraus werden abgelehnt.
- `file.list` (über `run_command`) zeigt, welche Dateien im Lese-Root liegen.
- Die Doku `docs/mcp.md` im Repo ist sehr ausführlich (3.400 Zeilen): bei Unklarheiten dort nachlesen.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
