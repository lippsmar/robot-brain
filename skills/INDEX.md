# Skill-Katalog

Spiegel der Notion-Seiten „Skill-Bibliothek“ und „Skill-Prüfstatus“. Stand 13.10.2026.

## Eigene Skills
| Skill | Status | Zweck |
|---|---|---|
| [roboter-projekt](roboter-projekt/SKILL.md) | aktiv | Arbeitsweise, Regeln, Doku, Testphase |
| [roboter-brainstorming-plan](roboter-brainstorming-plan/SKILL.md) | aktiv | Erst klären, dann Design und Plan |
| [roboter-debugging](roboter-debugging/SKILL.md) | aktiv | Ursache finden, Nachweis vor Erfolgsmeldung |
| [roboter-testumgebung](roboter-testumgebung/SKILL.md) | aktiv | Testphase mit privatem Google-Account |
| [adobe-oss-agent-tools](adobe-oss-agent-tools/SKILL.md) | aktiv | Prüfverfahren für Adobe-Nachbauten (die Tools selbst sind noch ungeprüft) |
| [roboter-retro](roboter-retro/SKILL.md) | aktiv in Claude seit 13.10.2026 | Rückblick auf Sitzungen, Verbesserungen an Regeln, Skills und Prüfungen |
| [photocraft-agent](photocraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | Photoshop-Nachbau steuern |
| [vectorcraft-agent](vectorcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | Illustrator-Nachbau steuern |
| [filmcraft-agent](filmcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | Premiere-Pro-Nachbau steuern |
| [lightcraft-agent](lightcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | Lightroom-Nachbau steuern |
| [effectcraft-agent](effectcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | After-Effects-Nachbau steuern |
| [pdfcraft-agent](pdfcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | Acrobat-Pro-Nachbau steuern |
| [designcraft-agent](designcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026 | InDesign-Nachbau steuern |

## Geplante Roboter-Skills (noch nicht geschrieben)
| Skill | Kategorie | Zweck | Schnittstelle |
|---|---|---|---|
| memory-recall | Gedächtnis | Kontext für Tasks abrufen | Bus |
| memory-consolidate | Gedächtnis | Journale und Fakten verdichten | intern |
| ble-scan-and-pair | Geräte | BLE-Geräte finden, registrieren, koppeln | BLE |
| ble-control | Geräte | GATT-Lesen/Schreiben, Notify loggen | BLE |
| net-discovery | Netzwerk | mDNS/ARP/SNMP-Scan, Inventar | LAN/WLAN |
| net-device-control | Netzwerk | HTTP/MQTT/Modbus-Befehle | LAN/WLAN |
| sensor-logging | Daten | Sensorwerte erfassen, validieren, speichern | I2C/SPI/UART |
| camera-capture | CV | Bilder/Video mit Sidecar-Metadaten | Kamera |
| dataset-export | ML | Datensätze mit Manifest und Splits | Datei |
| sms-gateway | Kommunikation | SMS senden/empfangen über SIM | LTE |
| mail-handler | Kommunikation | Mails lesen, klassifizieren, antworten | IMAP/SMTP |
| health-monitor | System | Watchdog, Akku, Temperatur, Konnektivität | Hub |
| safety-stop | Safety | Not-Aus auslösen und protokollieren | GPIO |

## Fremde Skills
| Quelle | Status | Anmerkung |
|---|---|---|
| obra/superpowers (MIT, Jesse Vincent) | alle 15 gelesen 13.10.2026, empfohlen für Claude Code | test-driven-development, systematic-debugging, verification-before-completion aktiv in Claude. Telemetrie mit `SUPERPOWERS_DISABLE_TELEMETRY` abschalten. executing-plans/subagent-driven-development entscheiden ohne Rückfrage: Freigabe-Sperre hat Vorrang. using-git-worktrees installiert Pakete automatisch |
| mattpocock/skills: grilling, grill-me (MIT) | geprüft 13.10.2026, nicht zusätzlich installieren | Ideen-Verfeinerung per Entscheidungsbaum. Fragt mehrere Fragen pro Runde. Entscheidungsbaum und Faktensuche in roboter-brainstorming-plan übernommen |
| mattpocock/skills: retro (MIT) | geprüft 13.10.2026, als roboter-retro angepasst | Rückblick auf Coding-Sitzungen, braucht writing-for-agents |
| corca-ai/claude-plugins: cwf:retro (MIT) | abgelehnt 13.10.2026 | Braucht ganzes CWF-Framework mit Hooks bei jeder Eingabe, 37 Skripte, optional Slack-Webhook |
| storytold: PhotoCraft, VectorCraft, FilmCraft, LightCraft, EffectCraft, PdfCraft, DesignCraft (MIT/Apache-2.0) | alle 7 gezielt geprüft 13.10.2026, bedingt geeignet | Übersicht im Skill adobe-oss-agent-tools. Korrektur: PhotoCraft hat doch eine Ordnerbeschränkung (Read-/Write-Root). Ohne Beschränkung: FilmCraft, LightCraft, DesignCraft |
| Everything Claude Code (affaan-m) | nicht komplett installieren | Überschneidet sich mit Memory Core, viele Hooks |
| Awesome Claude Code (hesreallyhim) | Nachschlagequelle | Linkliste, jeden Fund einzeln prüfen |
| pm-skills (Alireza Rezvani) | abgelehnt | Jira/Confluence, Skripte, Netzwerk, Lizenz widersprüchlich |

## Prüfcheckliste für fremde Skills
- [ ] Quelle und Autor bekannt
- [ ] Lizenz aus dem Repo selbst gelesen
- [ ] Berechtigungen geprüft: Skripte, Hooks, Netzwerk, Telemetrie, Zugangsdaten
- [ ] Passt zu einem Solo-Hardwareprojekt
- [ ] Skill vollständig gelesen, nicht nur die Beschreibung

## Vorlage für neue Skills
```markdown
---
name: ble-control
version: 0.1.0
category: devices
description: Liest und schreibt GATT-Characteristics registrierter BLE-Geräte und loggt alle Werte.
interfaces: [ble]
requires_approval: false   # true bei physischen/irreversiblen Aktionen
risk: low                  # low | medium | high
---

## Wann verwenden
## Eingaben
## Ablauf
## Fehlerbehandlung
## Beispiele
```
