---
name: "adobe-oss-agent-tools"
description: "Prüfverfahren für Open-Source-Nachbauten von Adobe-Apps (z. B. PhotoCraft), bevor ein Agent sie für Bild- oder Dokumentbearbeitung nutzt. Konkrete Befehle erst nach Prüfung der Quelltexte."
---

# Open-Source-Nachbauten von Adobe-Apps für Agenten

> Status: freigegeben von Marvin am 13.10.2026 (aus Notion rekonstruiert, Original nicht gefunden).

## Status
Die Projekte sind Community-Projekte, keine Veröffentlichung von Adobe, sehr neu und laut Roadmap unvollständig.

## Geprüfte Apps (13.10.2026)
Versionen Stand 15.10.2026 (alle sieben gebaut und getestet). Alle von ArtCraft (github.com/storytold), Rust, Lizenz MIT oder Apache-2.0, keine Telemetrie gefunden. Je App gibt es einen eigenen Skill mit Startbefehlen.

| Adobe | Nachbau | Skill | Ordnerbeschränkung | Steuerkanal | Netz / Downloads |
|---|---|---|---|---|---|
| Photoshop | PhotoCraft 0.9.0 | `photocraft-agent` | ja (Read-/Write-Root) | localhost mit Token | keine |
| Illustrator | VectorCraft 0.11.0 | `vectorcraft-agent` | ja (Read-/Write-Root) | localhost ohne Token | keine |
| Premiere Pro | FilmCraft 0.8.0 | `filmcraft-agent` | **nein**, Sandbox | localhost ohne Token | Whisper- und Kokoro-Modelle von huggingface.co |
| Lightroom | LightCraft 0.8.0 | `lightcraft-agent` | **nein**, Sandbox | localhost ohne Token; `denoise-serve` auch auf allen Schnittstellen möglich | Gesichtserkennungs-Modell von huggingface.co |
| After Effects | EffectCraft 0.10.0 | `effectcraft-agent` | ja (Read-/Write-Root) | localhost ohne Token | Face-Landmarker-Modell von Google |
| Acrobat Pro | PdfCraft 0.8.0 | `pdfcraft-agent` | ja (`--root`) | Control-Datei, MCP ohne Port | Update-Prüfung nur über Hilfe-Menü |
| InDesign | DesignCraft 0.8.0 | `designcraft-agent` | **nein**, Sandbox | localhost ohne Token | keine |

Prüftiefe: Die Repos haben je 140.000 bis 525.000 Zeilen Rust und wurden nicht vollständig gelesen. Gezielt geprüft: Lizenz, Netzwerk-Bibliotheken, Sockets, Telemetrie, Downloads, Prozessaufrufe, Agenten-Schnittstelle und Doku. Dass die Apps mit Claude Opus 5.5 gebaut wurden (Instagram-Beitrag von evolving.ai), lässt sich aus den Repos nicht belegen.

## Gemeinsame Regeln für alle Craft-Apps
- Apps ohne Ordnerbeschränkung (DesignCraft, LightCraft, FilmCraft) nur in der Sandbox `craft-sandbox.sh` (bubblewrap: kein Netz, nur der Arbeitsordner mit Kopien; liegt in jedem App-Skill unter `scripts/`), alternativ Container oder eigenes Benutzerkonto. Getestet am 15.10.2026.
- Apps mit Ordnerbeschränkung immer mit Roots starten, Schreib-Root getrennt vom Eingang.
- Steuerkanal ohne Token: App nur bei Bedarf mit `--control` starten.
- Modell-Downloads, Installation und MCP-Registrierung nur nach Marvins Freigabe.
- Gesichtserkennung verarbeitet personenbezogene Daten: nur mit Einwilligung, `pii: true`.
- Vor jeder neuen Version kurz neu prüfen (Changelog, neue Netzwerkzugriffe) und Datum hier eintragen.

## Prüfverfahren vor jeder Nutzung
1. Genauen Namen, Repo, Autor und Aktivität feststellen.
2. Lizenz aus dem Repo selbst lesen. Marken- und Namensfragen (Adobe) beachten.
3. Quelltext vollständig lesen: Installationsskripte, Netzwerkaufrufe, Telemetrie, Zugriff auf Dateien und Zugangsdaten.
4. In einer Sandbox klonen und starten, nie blind installieren.
5. Prüfen, ob es eine Schnittstelle für Agenten gibt (CLI, API, MCP) und was sie darf.
6. Ergebnis mit Datum in skills/INDEX.md und auf der Notion-Seite Skill-Prüfstatus eintragen.

## Erst danach
- Konkrete Befehle und Beispiele für den Agenten ergänzen.
- Nur auf Kopien von Dateien arbeiten, Originale nicht verändern.
