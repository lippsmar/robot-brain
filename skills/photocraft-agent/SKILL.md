---
name: "photocraft-agent"
description: "PhotoCraft (Photoshop-Nachbau, Open Source) per MCP oder CLI als Agent steuern: Rasterbildbearbeitung: Ebenen, Masken, Einstellungsebenen, Filter, PSD-Dateien. Verwenden, wenn der KI-Roboter oder Claude damit Dateien bearbeiten soll."
---

# PhotoCraft für Agenten

Nachbau von Adobe Photoshop aus der ArtCraft-Reihe, keine Adobe-Software. Quelle: github.com/storytold/photocraft, Lizenz MIT oder Apache-2.0 (Copyright 2026 ArtCraft Team and the PhotoCraft contributors). Geprüft am 13.10.2026 (Version 0.8.2, Commit 6f85054), nachgeprüft und getestet am 15.10.2026 (Version 0.9.0), Status laut Projekt: early alpha. Befehle unten stammen aus der Doku des Repos; bei Abweichungen gilt die aktuelle Doku bzw. `--help`.

## Prüfergebnis
- Quelltext nicht vollständig gelesen (sehr groß), gezielt geprüft: keine Telemetrie, keine HTTP-Client-Bibliothek. Steuerkanal nur auf 127.0.0.1, mit Token und Größen- und Zeitlimits.
- Ordnerbeschränkung für Agenten: Ja: `--automation-read-root` und `--automation-write-root`.

## Einsatzbereit (geprüft und getestet am 15.10.2026)
Version 0.9.0, Commit 7bb10a7, Lizenz weiter MIT oder Apache-2.0. Aus dem Quellcode gebaut in der Cloud-Sandbox, getestet nur an Kopien.
- **Netz:** Netzwerk-Bibliothek nur im Windows-Build, im Linux-`photocraft-cli` keine.
- **Getestet:**
  - `run` mit Kurven, Dynamik, Fotofilter, Vignette, Unscharf maskieren und Filmkorn: Feinschliff der Bilderreihe Schlaubi (15.10.2026), Rezept in `tools/bilderreihe/finalize.sh`
- **Bauen** (auf dem Gehirn-Laptop erst nach Marvins Freigabe):
  ```sh
  git clone --depth 1 https://github.com/storytold/photocraft.git && cd photocraft && cargo build --release -p photocraft-cli   # Ergebnis: target/release/photocraft-cli
  ```
- **Sandbox:** Zusätzlich empfohlen: in der Sandbox starten (`scripts/craft-sandbox.sh`), dann ohne Netz und ohne Zugriff auf das Home-Verzeichnis.
  ```sh
  photocraft-cli mcp --automation-read-root /arbeit/bilder --automation-write-root /arbeit/bilder/ausgabe
  ```
  `craft-sandbox.sh ARBEITSORDNER PROGRAMM [ARGUMENTE]`. Braucht `bubblewrap` (Debian: `apt install bubblewrap`). Pfade sind innen dieselben wie außen. Ergebnisse landen nur im Arbeitsordner.
- **In Claude Code registrieren** (erst nach Freigabe): `claude mcp add photocraft -- /pfad/zu/craft-sandbox.sh /arbeit/… /pfad/zu/photocraft-cli mcp …`

## Starten
Beispiele ohne Sandbox-Präfix. Im Betrieb `craft-sandbox.sh ARBEITSORDNER` davorsetzen (bei Apps ohne Ordnerbeschränkung Pflicht).
```sh
photocraft-cli mcp --automation-read-root /arbeit/bilder --automation-write-root /arbeit/bilder/ausgabe
```
Mit der laufenden App: Bridge-Modus mit `--bridge` und `--control-token-file` (siehe `docs/development.md` im Repo). UI-Werkzeuge (`ui_inspect`, `ui_screenshot`) nur dort.

CLI ohne MCP:
```sh
photocraft-cli run bild.psd --cmd filter.sharpen.smartSharpen --params '{"amount":80}' --out bild-fertig.png
photocraft-cli batch --actions aktionen.json --in ./eingang --out ./ausgabe
photocraft-cli batch --help
```


## Gemeinsame MCP-Werkzeuge
`command_list` (Befehle finden, mit `filter`), `command_run` (`id`, `params`), `command_batch` (`steps`, stoppt beim ersten Fehler, kein Rollback), `doc_inspect` (Dokument ansehen), `render_preview` (PNG-Vorschau zur Kontrolle). Vor jedem Befehl mit `command_list` die genaue ID und die Parameter nachschlagen, nichts raten.

## Besonderheiten
- Vor Experimenten `command_run` mit `image.duplicate` oder `history.newDocument` (leere `params`): neues Dokument, Original bleibt unverändert.
- `command_batch` ist keine Transaktion: Nach einem Fehler bleiben frühere Schritte angewendet. Mit `doc_inspect` prüfen, mit `edit.undo` zurücknehmen.
- Ohne Root-Flags hat der Server keinen Dateizugriff. Immer beide Roots setzen, Schreib-Root getrennt vom Eingang.
- Plug-ins laufen in einer WebAssembly-Sandbox ohne Datei- und Netzzugriff.

## Sicherheitsregeln (immer)
- Gemeinsame Regeln und Prüfergebnisse: Skill `adobe-oss-agent-tools`. Freigabe-Sperre aus `roboter-brainstorming-plan` gilt: Installation, MCP-Registrierung und Modell-Downloads nur nach Marvins Freigabe.
- Nur auf Kopien arbeiten. Originale nie öffnen und speichern, nie verschieben.
- Nur auf dem Gehirn-Laptop, in eigenem Benutzerkonto oder Container, nie auf dem Pi Zero.
- Installation nur aus den GitHub-Releases von storytold mit Prüfung der `SHA256SUMS.txt`, oder aus dem Quelltext mit `cargo build --release`. Keine Skripte aus dem Netz blind ausführen.
- Steuerkanal (`--control`/`--bridge`) nur auf 127.0.0.1. Token- und Control-Dateien nicht in `/tmp` oder geteilten Ordnern.
- Vor Experimenten Dokument duplizieren. Undo macht geschriebene Dateien nicht rückgängig.
- Jede Aktion im Event-Log festhalten (`agent.action`).
