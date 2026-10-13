# Prüfung OpenClaw (13.10.2026)

Geprüft nach der Checkliste in `skills/INDEX.md`. Gegenstand: offizielles Repo github.com/openclaw/openclaw, Version 2026.10.2, Commit a2d5c3c (13.10.2026). **Nur gezielt geprüft:** Das Repo hat über 55.000 Dateien, deshalb wurden die sicherheitsrelevanten Stellen gelesen, nicht alles. Nichts installiert.

## Ergebnis
**Bedingt geeignet.** OpenClaw passt als Gehirn-Software, aber nur mit eigener Konfiguration. Die Standardeinstellungen für Docker reichen nicht.

## Checkliste
- **Quelle:** OpenClaw Foundation (gemeinnützig). Drittanbieter-Images (z. B. andere Docker-Varianten, teils AGPL-3.0) nicht verwenden.
- **Lizenz:** MIT, aus `LICENSE` und `package.json` gelesen.
- **Telemetrie:** täglicher Update-Check an telemetry.openclaw.ai (Version, Betriebssystem, Node, CPU, ungefährer Standort). Anonyme Statistik ist standardmäßig aus. Ganz abschalten mit `update.checkOnStart: false` und `telemetry.enabled: false`. `DO_NOT_TRACK` stoppt den Update-Check nicht.
- **Netzwerk:** Gateway 18789, Bridge 18790, Microsoft Teams 3978. Bonjour schaltet sich im Container selbst ab.
- **Zugangsdaten:** Das Setup-Skript erzeugt einen Gateway-Token (`openssl rand -hex 32`) und schreibt ihn in `.env`. Fehlt der Token, meldet `openclaw security audit` einen kritischen Fehler.
- **Passt zum Projekt:** ja. Telegram-Kanal mit Pairing und Absenderliste. IMAP-Plugin mit Absenderliste und SPF/DKIM-Prüfung, das jede Mail in einer abgeschotteten Lese-Sitzung verarbeitet. Anthropic per API-Key, Kostenanzeige über einen Admin-Key möglich.

## Was wir ändern müssen (Pflicht)
1. **Ports nur an localhost:** In der mitgelieferten `docker-compose.yml` steht `"18789:18789"`. Das öffnet den Port auf allen Netzwerkkarten des Laptops. Ändern auf `"127.0.0.1:18789:18789"` und genauso für 18790. Port 3978 (Teams) ganz entfernen.
2. **Bind-Modus im Container:** `lan` ist im Container nötig, damit die Portfreigabe funktioniert. Er ist sicher, solange Punkt 1 umgesetzt ist.
3. **Keine Abo-Anmeldung:** Die Compose-Datei reicht `CLAUDE_AI_SESSION_KEY`, `CLAUDE_WEB_SESSION_KEY` und `CLAUDE_WEB_COOKIE` durch. Diese drei bleiben leer bzw. werden entfernt. Nur der API-Key wird verwendet (CLAUDE.md, Abschnitt 4).
4. **Telemetrie aus:** `update.checkOnStart: false`, `telemetry.enabled: false`. Updates holen wir von Hand.
5. **Werkzeuge einschränken:** mit der „Hardened baseline“ aus der Doku starten (`tools.profile: "messaging"`, `exec.security: "deny"`, `elevated.enabled: false`). Danach nur einzeln freischalten.
6. **Kanäle:** Telegram mit `dmPolicy: "pairing"` und `allowFrom` nur Marvin. Mails nur von Marvins Absender.
7. **Docker-Socket:** nicht in den Container einhängen. Wer den Socket hat, hat praktisch Root auf dem Laptop. Achtung: Das IMAP-Plugin braucht eine Sandbox. Wie das ohne Socket geht, klären wir vor dem Bau.
8. **Fernzugriff** nur über Tailscale. Die Gateway-Ports nicht im Tailnet freigeben, sondern Tailscale Serve verwenden. Kein Funnel.
9. Nach jeder Änderung `openclaw security audit` ausführen.

## Lücken für unser Projekt
- **E-Mail senden:** Das IMAP-Plugin liest nur. Antworten per SMTP (mail.de) bauen wir selbst, nur an Marvin.
- **SMS:** nur über Twilio. Für die eigene SIM (SIM7600) bräuchten wir einen eigenen Baustein. Das ist für Version 1 nicht nötig.
- **Audio vom Würfel:** Spracherkennung und Sprachausgabe sind nicht Teil dieser Prüfung, sie werden separat geprüft.

## Quellen (im Repo gelesen)
`LICENSE`, `package.json`, `docker-compose.yml`, `scripts/docker/setup.sh`, `SECURITY.md`, `docs/gateway/telemetry.md`, `docs/gateway/security/hardened-baseline.md`, `docs/gateway/security/exposure-runbook.md`, `docs/install/docker/networking-and-storage.md`, `docs/providers/anthropic.md`, `docs/channels/telegram.md`, `docs/channels/sms.md`, `docs/automation/imap.md`
