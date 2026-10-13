---
name: "filmcraft-agent"
description: "FilmCraft (Premiere Pro-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Videoschnitt, Farbe und Ton: Timeline, Clips, Effekte, Untertitel, Export. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# FilmCraft für Agenten

Nachbau von Adobe Premiere Pro aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/filmcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the FilmCraft contributors). Geprüft am 13.10.2026 (Version 0.7.2, Commit cee1feb), Status laut Projekt: jung, ändert sich schnell. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Steuerkanal (`--control`) nur auf 127.0.0.1, laut Doku **ohne Token**: Jedes Programm auf dem Rechner kann die laufende App dann steuern. App deshalb nur bei Bedarf mit `--control` starten, sonst headless arbeiten.
- Ordnerbeschränkung für Agenten: **Nein.** Server kann alles lesen und schreiben, was der Benutzer darf.

## Starten
```sh
# ohne App: leeres Projekt, Demo oder eigenes Projekt
filmcraft-cli mcp --project /arbeit/film/projekt.fcproj
# mit laufender App (vorher: filmcraft --control 9876)
filmcraft-cli mcp --bridge 127.0.0.1:9876
# alle Befehle auflisten
filmcraft-cli commands
```

In Claude Code registrieren (erst nach Freigabe): `claude mcp add filmcraft -- /pfad/zu/filmcraft-cli mcp …` mit denselben Optionen wie oben.

## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- **Keine Ordnerbeschränkung:** Laut eigener Doku kann der Server überall lesen und schreiben, wo der Benutzer darf. Deshalb nur in einem Container oder Benutzerkonto starten, das ausschließlich Kopien sieht.
- `media_import` nimmt absolute Pfade. Nur Pfade aus dem Arbeitsordner verwenden.
- **Modell-Downloads:** Spracherkennung (Whisper von OpenAI) und Sprachausgabe (Kokoro-82M) werden bei Bedarf von huggingface.co geladen, mit fester Revision und SHA-256-Prüfung. Nur nach Marvins Freigabe.
- Zusatz-Werkzeuge: `project_inspect`, `sequence_inspect`, `render_frame`. Im Bridge-Modus auch `ui_click`, `ui_drag`, `ui_key`, `ui_type`, `ui_screenshot`, `ui_control`.
- Zeiten in Ticks: aus `sequence_inspect` übernehmen, nicht selbst umrechnen.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
