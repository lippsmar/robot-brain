---
name: "adobe-oss-agent-tools"
description: "Prüfverfahren für Open-Source-Nachbauten von Adobe-Apps (z. B. PhotoCraft), bevor ein Agent sie für Bild- oder Dokumentbearbeitung nutzt. Konkrete Befehle erst nach Prüfung der Quelltexte."
---

# Open-Source-Nachbauten von Adobe-Apps für Agenten

> Status: freigegeben von Marvin am 13.10.2026 (aus Notion rekonstruiert, Original nicht gefunden).

## Status
Die Projekte sind Community-Projekte, keine Veröffentlichung von Adobe, sehr neu und laut Roadmap unvollständig.

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
