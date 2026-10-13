---
name: "designcraft-agent"
description: "DesignCraft (InDesign-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Seiten- und Layoutgestaltung: Dokumente, Rahmen, Text, Stile, Bilder, PNG-Export. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# DesignCraft für Agenten

Nachbau von Adobe InDesign aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/designcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the DesignCraft contributors). Geprüft am 13.10.2026 (Version 0.7.1, Commit e862e0a), Status laut Projekt: frühe Version. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Steuerkanal (`--control`) nur auf 127.0.0.1, laut Doku **ohne Token**: Jedes Programm auf dem Rechner kann die laufende App dann steuern. App deshalb nur bei Bedarf mit `--control` starten, sonst headless arbeiten.
- Ordnerbeschränkung für Agenten: **Nein.** Server kann alles lesen und schreiben, was der Benutzer darf.

## Starten
```sh
# ohne App
designcraft-cli mcp
# mit laufender App (vorher: designcraft --control 7979)
designcraft-cli mcp --connect 7979
```

In Claude Code registrieren (erst nach Freigabe): `claude mcp add designcraft -- /pfad/zu/designcraft-cli mcp …` mit denselben Optionen wie oben.

## Besonderheiten
- **Keine Ordnerbeschränkung** gefunden: nur in Container oder Benutzerkonto mit ausschließlich Kopien. `place_image` und `open_document` lesen jeden angegebenen Pfad.
- Werkzeuge: `list_commands`, `execute`, `batch`, `inspect_document`, `get_story`, `set_story_text`, `new_document`, `open_document`, `save_document`, `place_image`, `render_page`, `export_png`. Im Connect-Modus zusätzlich `screenshot`, `click`, `drag`, `menu_list`, `ui_inspect`, `ui_set`, `dialog_*`.
- Koordinaten in Punkt (1/72 Zoll), y nach unten, im Druckbogen-Raum. Seiten ab 0 gezählt.
- Textpositionen sind UTF-8-Byte-Offsets, nicht Zeichen (Umlaute zählen 2 Byte).
- Ein fehlgeschlagener Aufruf im Connect-Modus wird nicht wiederholt: erst Dokument prüfen, dann erneut versuchen.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
