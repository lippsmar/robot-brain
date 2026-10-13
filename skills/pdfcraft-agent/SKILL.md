---
name: "pdfcraft-agent"
description: "PdfCraft (Acrobat Pro-Nachbau, Open Source) per MCP oder CLI als Agent steuern: PDF lesen, durchsuchen, Seiten ordnen, kommentieren, schützen. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# PdfCraft für Agenten

Nachbau von Adobe Acrobat Pro aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/pdfcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the PdfCraft contributors). Geprüft am 13.10.2026 (Version 0.7.1, Commit 7437bde), Status laut Projekt: frühe Version. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Einziger Netzzugriff: Update-Prüfung über das Hilfe-Menü. MCP-Server ohne Port (stdin/stdout). App-Steuerung über eine Control-Datei.
- Ordnerbeschränkung für Agenten: Ja: `--root`.

## Starten
```sh
pdfcraft-cli mcp --root /arbeit/pdf --compact
# einzelne Aufrufe und Skripte
pdfcraft-cli tools
pdfcraft-cli run text_find doc=1 query=rechnung
pdfcraft-cli run --script schritte.json --root /arbeit/pdf
```

In Claude Code registrieren (erst nach Freigabe): `claude mcp add pdfcraft -- /pfad/zu/pdfcraft-cli mcp …` mit denselben Optionen wie oben.

## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- Der MCP-Server startet nie von selbst, öffnet keinen Port und endet, wenn der Agent trennt. `--root` beschränkt alle Lese- und Schreibzugriffe.
- `--compact` spart Token: wenige Kernwerkzeuge plus `tool_search` und `tool_call`.
- Änderungen bleiben im Speicher und rückgängig machbar bis `doc_save`. Speichern hängt ein inkrementelles Update an, die ursprünglichen Bytes bleiben erhalten.
- Steuerung der App: `pdfcraft --control ~/.pdfcraft-control.json`, Datei nur in einem Ordner, den nur Marvin beschreiben kann.
- Netzwerk nur bei „Hilfe ▸ Nach Updates suchen“ (fragt die GitHub-API). Sonst offline, ohne Telemetrie.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
