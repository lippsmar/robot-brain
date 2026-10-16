# Skill-Katalog

Spiegel der Notion-Seiten „Skill-Bibliothek“ und „Skill-Prüfstatus“. Stand 16.10.2026.

## Eigene Skills
| Skill | Status | Zweck |
|---|---|---|
| [roboter-projekt](roboter-projekt/SKILL.md) | aktiv | Arbeitsweise, Regeln, Doku, Testphase |
| [roboter-brainstorming-plan](roboter-brainstorming-plan/SKILL.md) | aktiv | Erst klären, dann Design und Plan |
| [roboter-debugging](roboter-debugging/SKILL.md) | aktiv | Ursache finden, Nachweis vor Erfolgsmeldung |
| [roboter-testumgebung](roboter-testumgebung/SKILL.md) | aktiv | Testphase mit separatem Google-Testkonto |
| [adobe-oss-agent-tools](adobe-oss-agent-tools/SKILL.md) | aktiv | Prüfverfahren für Adobe-Nachbauten (die Tools selbst sind noch ungeprüft) |
| [roboter-retro](roboter-retro/SKILL.md) | aktiv in Claude seit 13.10.2026 | Rückblick auf Sitzungen, Verbesserungen an Regeln, Skills und Prüfungen |
| [photocraft-agent](photocraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.9.0), neue Fassung hochzuladen | Photoshop-Nachbau steuern |
| [vectorcraft-agent](vectorcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.11.0), neue Fassung hochzuladen | Illustrator-Nachbau steuern |
| [filmcraft-agent](filmcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.8.0), neue Fassung hochzuladen | Premiere-Pro-Nachbau steuern |
| [lightcraft-agent](lightcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.8.0), neue Fassung hochzuladen | Lightroom-Nachbau steuern |
| [effectcraft-agent](effectcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.10.0), neue Fassung hochzuladen | After-Effects-Nachbau steuern |
| [pdfcraft-agent](pdfcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.8.0), neue Fassung hochzuladen | Acrobat-Pro-Nachbau steuern |
| [designcraft-agent](designcraft-agent/SKILL.md) | aktiv in Claude seit 13.10.2026, einsatzbereit getestet 15.10.2026 (Version 0.8.0), neue Fassung hochzuladen | InDesign-Nachbau steuern |
| [prompt-engineering](prompt-engineering/SKILL.md) | aktiv in Claude seit 15.10.2026 | Prompts, Skills, Werkzeugbeschreibungen schreiben und prüfen, modellagnostisch. Grundlage: Anthropics Prompt-Audit-Leitfaden |

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
| storytold: PhotoCraft 0.9.0 (15.10.2026 nachgeprüft: reqwest/hyper nur als Build-Abhängigkeit des Windows-Drucks über sigstore, unter Linux nicht enthalten) und VectorCraft 0.11.0 (14.10.2026 nachgeprüft: keine HTTP-Client-Bibliothek). Ursprünglich: VectorCraft, FilmCraft, LightCraft, EffectCraft, PdfCraft, DesignCraft (MIT/Apache-2.0) | alle 7 gezielt geprüft 13.10.2026, bedingt geeignet | Übersicht im Skill adobe-oss-agent-tools. Korrektur: PhotoCraft hat doch eine Ordnerbeschränkung (Read-/Write-Root). Ohne Beschränkung: FilmCraft, LightCraft, DesignCraft |
| storytold: PDFCraft 0.8.0, DesignCraft 0.8.0, EffectCraft 0.10.0, LightCraft 0.8.0, FilmCraft 0.8.0 | nachgeprüft und getestet 15.10.2026 in der Cloud-Sandbox | Netzwerk-Bibliotheken nur in Desktop-Apps oder optionalen Download-Teilen; LightCraft-CLI enthält Modell-Download (nur nach Freigabe). DesignCraft, LightCraft, FilmCraft weiter ohne Ordnerbeschränkung: nur über `tools/craft/craft-sandbox.sh` (bubblewrap, kein Netz, nur Arbeitsordner) |
| trailofbits/skills: property-based-testing 1.2.2 (CC BY-SA 4.0, Henrik Brodin) | vollständig gelesen 15.10.2026, unverändert übernommen als Projekt-Skill `.claude/skills/property-based-testing/` | Hilft beim Schreiben und Prüfen von Hypothesis-Tests (Regel-Katalog, Tautologien, leere Tests). Nur Text, keine Skripte, Hooks oder Netz. Setzt `effort: low`, solange er aktiv ist. Herkunft und Lizenz im Ordner |
| trailofbits/skills: modern-python, static-analysis, supply-chain-risk-auditor, second-opinion, fp-check | nicht übernommen 15.10.2026 | modern-python legt per Hook PATH-Sperren an; static-analysis (Semgrep) sendet standardmäßig Metriken; supply-chain-risk-auditor fragt externe Dienste ab; second-opinion schickt Code an Codex und Gemini; fp-check läuft bei jedem Stopp |
| anthropics/claude-plugins-official: security-guidance, claude-security | abgelehnt 15.10.2026 | installiert Pakete beim Start bzw. proprietäre Lizenz, Hooks schicken Diffs oder Nutzungszähler nach außen |
| Claude Code: eingebaute Skills /security-review und /code-review | nutzbar | gehören zu Claude Code, keine fremde Installation |
| openclaw/openclaw 2026.10.2 (MIT, OpenClaw Foundation) | gezielt geprüft 13.10.2026, bedingt geeignet | Gehirn-Software. Pflicht: Ports nur an 127.0.0.1, Telemetrie aus, keine Abo-Session-Keys, Hardened Baseline, kein Docker-Socket. Details: `docs/pruefung-openclaw.md` |
| Everything Claude Code (affaan-m) | nicht komplett installieren | Überschneidet sich mit Memory Core, viele Hooks |
| Awesome Claude Code (hesreallyhim) | Nachschlagequelle | Linkliste, jeden Fund einzeln prüfen |
| pm-skills (Alireza Rezvani) | abgelehnt | Jira/Confluence, Skripte, Netzwerk, Lizenz widersprüchlich |

## Python-Pakete für die Entwicklung (`brain/requirements-dev.txt`)
Geprüft am 15.10.2026 an genau diesen Versionen: Lizenzdatei aus dem Paket gelesen, Quelltext nach Netzwerk-Importen und Telemetrie durchsucht, Binärdateien nach HTTP-Bibliotheken. Regel: feste Version, mindestens 14 Tage alt, Installation nur mit SHA-256-Prüfsummen. Nur für Tests und Code-Prüfung, nicht im laufenden Betrieb.

| Paket | Lizenz | Netz und Telemetrie | Hinweis |
|---|---|---|---|
| pytest 9.1.1 | MIT | keine Telemetrie. Netz nur mit `--pastebin` (lädt Testausgabe hoch) | `pastebin` ist in `pyproject.toml` abgeschaltet |
| hypothesis 6.168.3 | MPL-2.0 | keine Telemetrie. Netz nur mit `GitHubArtifactDatabase`, die wir nicht nutzen | Beispiel-Datenbank lokal in `.hypothesis/` (nicht im Repo) |
| ruff 0.16.10 | MIT | keine HTTP-Bibliothek im Programm. Das Wort „telemetry“ steht nur im Editor-Protokoll (LSP), nicht für Internet | Code-Prüfung und Formatierung |
| coverage 7.16.2 | Apache-2.0 | keine. `socket` nur für den Rechnernamen | Testabdeckung |
| iniconfig 2.3.0, pluggy 1.6.0, packaging 26.3, pygments 2.21.0 | MIT, MIT, Apache-2.0/BSD, BSD-2-Clause | keine Netz-Importe | Abhängigkeiten von pytest. pluggy 1.7.0 und iniconfig 2.3.1 waren jünger als 14 Tage, deshalb ältere Versionen |
| sortedcontainers 2.4.0 | Apache-2.0 | keine | Abhängigkeit von hypothesis |
| mypy 2.4.0 mit ast-serialize 0.11.2, librt 0.16.0, mypy-extensions 1.1.0, pathspec 1.1.1, typing-extensions 4.16.0 | MIT (mypy, ast-serialize, librt, mypy-extensions), MPL-2.0 (pathspec), PSF-2.0 (typing-extensions) | keine Telemetrie, kein Netz. `urllib` nur für Dateipfad-Umwandlung in Berichten, `socket` nur lokal (Unix-Socket des Hintergrunddienstes), „telemetry“ nur lokale Zeitmessung in eine Datei. Netz nur mit `--install-types`, das wir nicht nutzen | Typprüfung. ast-serialize 0.13.0 war erst 3 Tage alt, deshalb 0.11.2 |

Nicht vollständig gelesen (zu groß). Gelesen bzw. durchsucht: Lizenzdateien, alle Python-Dateien per Suche nach `urllib`, `http`, `socket`, `requests`, Telemetrie-Begriffen, die Fundstellen im Detail, Binärdateien per `strings`.

## Python-Pakete für den Betrieb (`brain/requirements.txt`)
Gleiche Regel wie oben: feste Version, mindestens 14 Tage alt, Installation nur mit SHA-256-Prüfsummen aller Dateien von PyPI.

| Paket | Lizenz | Netz und Telemetrie | Hinweis |
|---|---|---|---|
| PyYAML 6.0.3 (25.09.2025) | MIT (Lizenzdatei im Wheel gelesen) | keine. Alle Importe gelesen: nur Standardbibliothek und eigene Module. Die C-Erweiterung `_yaml` hängt nur an libc und pthread, enthält keine URLs | geprüft 16.10.2026. Für das Charakter-Profil (Bauplan Charakter 2.2). Nur `SafeLoader` und `safe_dump`, doppelte Schlüssel und Aliase werden abgewiesen (`brain/character/profile.py`) |

## Prüfcheckliste für fremde Skills
- [ ] Quelle und Autor bekannt
- [ ] Lizenz aus dem Repo selbst gelesen
- [ ] Berechtigungen geprüft: Skripte, Hooks, Netzwerk, Telemetrie, Zugangsdaten
- [ ] Passt zu einem Solo-Hardwareprojekt
- [ ] Skill vollständig gelesen, nicht nur die Beschreibung
- [ ] Modelldateien nur als ONNX, safetensors oder GGUF/GGML. Pickle-Formate (`.pkl`, `.pt`, `.pth`, FAISS-Index mit `allow_dangerous_deserialization`) und Keras-`.h5` mit Lambda-Schichten können beim Laden Code ausführen und werden nie aus fremden Quellen geladen (16.10.2026)

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
