# CLAUDE.md – KI-Roboter (robot-brain)

Status: Entwurf v0.1, Stand 13.10.2026. Spiegel der Notion-Seite „CLAUDE.md – Projektbeschreibung“. Bei Widerspruch gilt Notion, und es wird nachgefragt.

## 1. Ziel
Ein kleiner Roboter mit Sensoren und KI-Zugang, der im Hintergrund Wissen sammelt, auf Anweisung Themen vertieft und sein Wissen in einem externen Speicher ablegt und abrufbar hält. Er hat eine eigene SIM-Karte (SMS, Daten) und eine eigene E-Mail-Adresse. Marvin trägt die rechtliche Verantwortung für alle Konten, die SIM und den API-Key.

## 2. Architektur in Kurzform
- **Cognitive Layer (Host):** Claude Code (Planung, Code, Skills), OpenClaw (agentische Ausführung, Tools, Kommunikation) und Memory Core (Gedächtnis L0 bis L5, siehe `memory/SYSTEM_PROMPT.md`).
- **Control Hub:** Zentrale Instanz für Sensorik, LTE/SIM, Mail, BLE, Netzwerk und Not-Aus. Safety-Funktionen laufen lokal und unabhängig von der Cloud.
- **Vorschlag zur Hardware (offen):** Microcontroller für Not-Aus, Watchdog und Sensorik, Raspberry Pi Zero 2 W für LTE-Modem, Mail und Kommunikation. Das Gehirn (OpenClaw, Vektorspeicher, Embeddings) läuft auf Marvins altem Laptop als Heimserver (Entscheidung 13.10.2026, Eignung noch prüfen).
- **Wissensspeicher:** SQLite mit sqlite-vec und FTS5 (Hybridsuche), kleine ONNX-Embeddings über fastembed.
- **Energie:** Akku mit USB-C-Laden über ein UPS-HAT. Dauerbetrieb braucht ein Netzteil.
- **Details** (SIM-Modem, Modelle, Embeddings, OpenClaw-Absicherung, Handy-Zugriff, Adobe-Nachbauten): `docs/projektstart-details.md`. Teileliste: `docs/teileliste.md`. Design des Körpers „Schlaubi“: `docs/design-koerper.md`. OpenClaw-Prüfung: `docs/pruefung-openclaw.md`.

## 3. Arbeitsregeln für Claude Code
- Vor der Arbeit den Skill `skills/roboter-projekt` befolgen.
- Keine physischen oder irreversiblen Aktionen ohne Freigabe.
- Nichts in Marvins Namen ohne Rückfrage: keine Nachrichten, Mails, SMS oder Anrufe als Marvin, keine Käufe, Anmeldungen, Zusagen, Termine oder Beiträge für ihn. Lesen, recherchieren und Entwürfe vorbereiten ist erlaubt.
- Keine Secrets, Zugangsdaten, SIM-PINs oder Tokens in Code, Logs, Notion oder Gedächtnis. Nur Referenzen auf den Secret-Store.
- Fremde Skills, Repos und Pakete vor der Nutzung vollständig lesen und nach der Checkliste in `skills/INDEX.md` bewerten.
- Keine Umgehung von SIM-Registrierung, Identitätsprüfungen oder Bot-Sperren. Der Roboter gibt sich als Automat zu erkennen und beachtet robots.txt.
- Jede Aktion des Agenten wird protokolliert (Event-Log gemäß Schema).
- Nichts erfinden. Fehlendes wird nachgefragt oder als offen markiert.
- OpenClaw nur in Docker, nur an localhost, mit Gateway-Token, Zugriff von außen nur über privates Netz (z. B. Tailscale), regelmäßig `openclaw security audit`.
- Neue Features: `skills/roboter-brainstorming-plan`. Fehler: `skills/roboter-debugging`. Rückblick: `skills/roboter-retro`.
- Bei Konflikt mit allgemeinen Skills (z. B. Superpowers) gelten die roboter-Skills und die Freigabe-Sperre.

## 4. Token und Budget
- Der laufende Roboter nutzt einen API-Key aus der Anthropic Console mit Prepaid-Guthaben und monatlichem Ausgabenlimit.
- Die Abo-Anmeldung (OAuth) von Claude Pro oder Max wird nicht in OpenClaw oder anderen Drittanbieter-Tools verwendet. Das Abo dient der Entwicklung in Claude Code.
- Selbsterhalt: Budget überwachen, bei knappem Stand Sparmodus und Marvin zum Nachladen auffordern. Dazu Sparen (lokales Modell, Cache), Zuarbeit für Einnahmen (Marvin verkauft) und Belohnung durch Marvin. Immer nach deutschem Recht, Einnahmen sind Marvins Einnahmen, Veröffentlichen und Verkaufen nur mit Freigabe (Details: Notion „Design Gehirn“).
- Modellwahl: Haiku für Hintergrundrecherche, Sonnet oder Opus für Gespräche. Modellname steht in der Config, beim Start die Models-API abfragen und neue Modelle melden.

## 5. Testphase
Alle Funktionen werden zuerst mit Marvins privatem Google-Account getestet. Regeln: `skills/roboter-testumgebung`.

## 6. Datenschutz und Kamera
- Lokale Datenhaltung, verschlüsselte Laufwerke, keine Telemetrie, VPN, möglichst wenig persönliche Daten an die API.
- Marvins Stimme bleibt lokal: Audio geht nie an Cloud-Dienste, auch nicht als Rückfall. Nur erkannter Text geht an die Claude-API (Entscheidung 13.10.2026).
- Kameras und Mikrofone erkennbar, keine verdeckten Aufnahmen, Aufnahmen von Personen nur mit Einwilligung. Personenbezogene Daten mit `pii: true`.

## 7. Offene Punkte
- [ ] Microcontroller-Modell und Sensorliste festlegen (Vorschlag im Design: Version 1 ohne Mikrocontroller)
- [ ] Zweistufiger Hub (Microcontroller plus Pi Zero 2 W) oder reiner Microcontroller
- [x] Speicherziel: Gedächtnis auf dem Laptop, Sicherung verschlüsselt auf externer Festplatte zu Hause (13.10.2026)
- [ ] Vektordatenbank: sqlite-vec mit FTS5 plus zusätzlicher Vektorspeicher (Marvin, 13.10.2026), Kandidat LanceDB, Zweck und Auswahl offen
- [x] Retention-Fristen pro Datentyp mit Merk-Schutz (13.10.2026, Notion „Design Gehirn“)
- [ ] Freigabe-Policy für physische Aktionen
- [ ] Privater Google-Account oder separates Testkonto
- [ ] SIM-Anbieter wählen (E-Mail: mail.de FreeMail, Konto legt Marvin an)
- [x] Design Körper Version 1 freigegeben (13.10.2026, `docs/design-koerper.md`)
- [x] Bauplan Körper Version 1 bestätigt (13.10.2026)
- [ ] Phase 1: Teile Stufe 1 bestellen (Marvin, `docs/einkauf-stufe1.md`)
- [ ] Laptop als Gehirn: Modell, RAM, Speicher, Akkuzustand und Betriebssystem erfassen und Eignung prüfen
- [ ] Superpowers in Claude Code installieren und Telemetrie abschalten (macht Marvin, siehe `docs/projektstart-details.md`)
