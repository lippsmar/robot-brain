---
name: "lightcraft-agent"
description: "LightCraft (Lightroom-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Fotoverwaltung und Raw-Entwicklung: Bibliothek, Bewertungen, Entwickeln, Masken, Export. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# LightCraft für Agenten

Nachbau von Adobe Lightroom aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/lightcraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the LightCraft contributors). Geprüft am 13.10.2026 (Version 0.7.1, Commit b3d392b), Status laut Projekt: jung, ändert sich schnell. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie. Steuerkanal (`--control`) nur auf 127.0.0.1, laut Doku **ohne Token**: Jedes Programm auf dem Rechner kann die laufende App dann steuern. App deshalb nur bei Bedarf mit `--control` starten, sonst headless arbeiten.
- Ordnerbeschränkung für Agenten: **Nein.** Server kann alles lesen und schreiben, was der Benutzer darf.

## Starten
```sh
# ohne App, mit Ordner voller Kopien
lightcraft-cli mcp /arbeit/fotos
# mit laufender App (vorher: lightcraft --control 7980)
lightcraft-cli mcp --connect 127.0.0.1:7980
# Befehlskette ohne MCP
lightcraft-cli run --import /arbeit/fotos/bild.dng develop.set control=light.exposure value=0.7 app.export path=/arbeit/ausgabe/bild.jpg longEdge=2048
```

In Claude Code registrieren (erst nach Freigabe): `claude mcp add lightcraft -- /pfad/zu/lightcraft-cli mcp …` mit denselben Optionen wie oben.

## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- **Keine Ordnerbeschränkung** gefunden: nur in Container oder Benutzerkonto mit ausschließlich Kopien.
- **Import nie mit `mode: "move"`:** verschiebt Originale. Nur `copy` oder ohne Modus.
- `--library DIR` legt eine dauerhafte Bibliothek an. Nur einen eigenen Ordner dafür nehmen, nicht Marvins Foto-Bibliothek.
- **Gesichtserkennung** (Modell AuraFace von huggingface.co): verarbeitet personenbezogene Daten. Nur mit Marvins Freigabe und Einwilligung der Personen, Ergebnisse mit `pii: true`.
- `denoise-serve` kann auf allen Netzwerkschnittstellen lauschen, unverschlüsselt. Nur auf 127.0.0.1 starten.
- Werkzeuge zusätzlich: `import`, `query_photos`, `select_photos`, `get_develop`, `set_develop`, `apply_preset`, `crop`, `render_photo`, `export`. `export` ohne Größe rendert 3000 px lange Kante.
- `addToPhotos` (Apple Fotos) nicht verwenden.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
