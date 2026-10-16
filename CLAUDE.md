# CLAUDE.md – KI-Roboter (robot-brain)

Status: Stand 16.10.2026, abgeglichen mit der Notion-Seite „CLAUDE.md – Projektbeschreibung“ (Spiegel). Bei Widerspruch gilt Notion, und es wird nachgefragt.

## 1. Ziel
Ein kleiner Roboter mit Sensoren und KI-Zugang, der im Hintergrund Wissen sammelt, auf Anweisung Themen vertieft und sein Wissen in einem externen Speicher ablegt und abrufbar hält. Er hat eine eigene SIM-Karte (SMS, Daten) und eine eigene E-Mail-Adresse. Marvin trägt die rechtliche Verantwortung für alle Konten, die SIM und den API-Key.

## 2. Architektur in Kurzform
- **Cognitive Layer (Host):** Claude Code (Planung, Code, Skills), OpenClaw (agentische Ausführung, Tools, Kommunikation) und Memory Core (Gedächtnis L0 bis L5, siehe `memory/SYSTEM_PROMPT.md`).
- **Control Hub:** Zentrale Instanz für Sensorik, LTE/SIM, Mail, BLE, Netzwerk und Not-Aus. Safety-Funktionen laufen lokal und unabhängig von der Cloud.
- **Vorschlag zur Hardware (offen):** Microcontroller für Not-Aus, Watchdog und Sensorik, Raspberry Pi Zero 2 W für LTE-Modem, Mail und Kommunikation. Das Gehirn (OpenClaw, Vektorspeicher, Embeddings) läuft auf Marvins altem Laptop als Heimserver (Entscheidung 13.10.2026, Eignung noch prüfen).
- **Wissensspeicher:** SQLite mit sqlite-vec und FTS5 (Hybridsuche), dazu LanceDB als Vergleich und Ersatz. Kleine ONNX-Embeddings über fastembed.
- **Energie:** Akku mit USB-C-Laden über ein UPS-HAT. Dauerbetrieb braucht ein Netzteil.
- **Details** (SIM-Modem, Modelle, Embeddings, OpenClaw-Absicherung, Handy-Zugriff, Adobe-Nachbauten): `docs/projektstart-details.md`. Teileliste: `docs/teileliste.md`. Design des Körpers „Schlaubi“: `docs/design-koerper.md`. Design des Gehirns: `docs/design-gehirn.md`. Design des Charakters: `docs/design-charakter.md`. Design Datensammlung: `docs/design-daten.md`. Design Code-Skills: `docs/design-code-umgebung.md`. Design Data Lakehouse: `docs/design-lakehouse.md`. Design Wissensarchitektur (Entwurf): `docs/design-wissen.md`. OpenClaw-Prüfung: `docs/pruefung-openclaw.md`. Sicherheit und Recht: `docs/sicherheit-und-recht.md`. Grenzen von Claude (Umgebung vs. harte Grenzen): `docs/claude-grenzen.md`. Mögliche Features für später: `docs/zukunft-features.md`. Lessons Learned und Mechanismen für Claude: `docs/claude-optimierung.md` (Spiegel des Notion-Projekts „Claude – Selbstoptimierung“). Bilder: `docs/bilder/` (Notion „Bilder: Schlaubi“).

## 3. Arbeitsregeln für Claude Code
- Vor der Arbeit den Skill `skills/roboter-projekt` befolgen und die Checklisten in `docs/claude-optimierung.md` nutzen.
- Keine physischen oder irreversiblen Aktionen ohne Freigabe.
- Nichts in Marvins Namen ohne Rückfrage: keine Nachrichten, Mails, SMS oder Anrufe als Marvin, keine Käufe, Anmeldungen, Zusagen, Termine oder Beiträge für ihn. Lesen, recherchieren und Entwürfe vorbereiten ist erlaubt.
- Keine Secrets, Zugangsdaten, SIM-PINs oder Tokens in Code, Logs, Notion oder Gedächtnis. Nur Referenzen auf den Secret-Store.
- Fremde Skills, Repos und Pakete vor der Nutzung vollständig lesen und nach der Checkliste in `skills/INDEX.md` bewerten.
- Keine Umgehung von SIM-Registrierung, Identitätsprüfungen oder Bot-Sperren. Der Roboter gibt sich als Automat zu erkennen und beachtet robots.txt. Ausnahme nur für Claude Code (Marvin, 16.10.2026): Beiträge auf Social Media, deren Link Marvin selbst schickt, darf Claude mit Browser-Kennung ansehen, privat und ohne etwas zu speichern (Skill `skills/social-media-ansehen`).
- Jede Aktion des Agenten wird protokolliert (Event-Log gemäß Schema).
- Nichts erfinden. Fehlendes wird nachgefragt oder als offen markiert.
- OpenClaw nur in Docker, nur an localhost, mit Gateway-Token, Zugriff von außen nur über privates Netz (z. B. Tailscale), regelmäßig `openclaw security audit`.
- Neue Features: `skills/roboter-brainstorming-plan`. Fehler: `skills/roboter-debugging`. Rückblick: `skills/roboter-retro`.
- Bei Konflikt mit allgemeinen Skills (z. B. Superpowers) gelten die roboter-Skills und die Freigabe-Sperre.
- **Code (ab 15.10.2026):** unter `brain/`, Python 3.13, erst Test, dann Code. Fertig erst mit frischem Testlauf (`pytest`, `ruff check brain`, `mypy`; alles gleichzeitig mit `tools/dev/pruefen.sh`, Abschluss mit Skill `paket-abschluss`), Fehler-Einbau-Prüfung (`tools/dev/mutation_check.py`, parallel; während der Arbeit `--geaendert`) und Code-Prüfung (`/code-review`), beides einmal pro Arbeitspaket. Ein Commit und ein Notion-Eintrag pro Paket (16.10.2026). Befunde von Prüfern gegen die Primärquelle prüfen, nicht blind übernehmen. Werkzeuge nur aus `brain/requirements-dev.txt` (für den Skill `social-media-ansehen` zusätzlich `tools/social/requirements.txt`, eigene venv): feste Versionen, mindestens 14 Tage alt, mit Prüfsummen. Laufzeitdaten nie im Repo. Details: `brain/README.md`.

## 4. Token und Budget
- **Anbieterunabhängig (Entscheidung 15.10.2026):** Schlaubi läuft mit jedem Modell, das man hat. Bevorzugt europäische Infrastruktur (z. B. IONOS, STACKIT, Mistral, Langdock), möglich sind auch API-Keys großer US-Anbieter und freie Modelle lokal. Für den laufenden Betrieb immer ein API-Key oder lokales Modell mit Prepaid bzw. Ausgabenlimit. Ein Modell muss vorher die Prüffragen bestehen.
- Abo-Anmeldungen (OAuth) von Claude Pro/Max oder anderen Anbietern werden nicht in OpenClaw oder anderen Drittanbieter-Tools verwendet. Abos nutzt man nur über die offiziellen Apps des Anbieters (z. B. später als Host über MCP). Das Claude-Abo dient der Entwicklung in Claude Code.
- **Betrieb (Entscheidung 15.10.2026, Weg C):** Version 1 läuft mit einem kleinen Prepaid-API-Key aus der Anthropic Console mit monatlichem Ausgabenlimit. Limit höchstens 20 € im Monat (Entscheidung 15.10.2026, ersetzt 10 €; die Console rechnet in US-Dollar, Limit so setzen, dass es unter 20 € bleibt; Vorschlag 22 $, am 15.10.2026 laut EZB-Kurs 1,1208 etwa 19,63 €; der Budget-Wächter stoppt vor diesem Limit und hält Gesprächen 10 € frei, die Recherche bekommt dann höchstens etwa 9,63 €). Aufteilung (bestätigt 15.10.2026): Recherche höchstens 10 € (davon Selbstoptimierung 40 %, also 4 €), Gespräche mit Marvin mindestens 10 €. Warnung 80 %, Sparmodus 90 %, Stopp 100 %. Marvins Claude Pro dient nur der Entwicklung und seiner eigenen Nutzung.
- Selbsterhalt: Budget überwachen, bei knappem Stand Sparmodus und Marvin zum Nachladen auffordern. Dazu Sparen (lokales Modell, Cache), Zuarbeit für Einnahmen (Marvin verkauft) und Belohnung durch Marvin. Immer nach deutschem Recht, Einnahmen sind Marvins Einnahmen, Veröffentlichen und Verkaufen nur mit Freigabe (Details: Notion „Design Gehirn“).
- Modellwahl über Rollen statt Namen: günstiges Modell für Hintergrundrecherche, starkes Modell für Gespräche, Spitzenmodell für schwierige Fragen. Die Zuordnung zu Anbieter und Modell steht in der Config (Start: Haiku, Sonnet, Opus). Beim Start die verfügbaren Modelle abfragen und neue melden.

## 5. Testphase
Google-Funktionen werden mit einem separaten Google-Testkonto getestet, das Marvin anlegt (Entscheidung 13.10.2026). Kein Zugriff auf Marvins privates Google-Konto. Regeln: `skills/roboter-testumgebung`.

## 6. Datenschutz und Kamera
- Lokale Datenhaltung, verschlüsselte Laufwerke, keine Telemetrie, VPN, möglichst wenig persönliche Daten an die API.
- Marvins Stimme bleibt lokal: Audio geht nie an Cloud-Dienste, auch nicht als Rückfall. Nur erkannter Text geht an die Claude-API (Entscheidung 13.10.2026).
- Kamerabilder dürfen zur Auswertung an die Claude-API, nur wenn Marvin etwas zeigt, ohne Metadaten (Entscheidung 13.10.2026). Seit 15.10.2026 keine Kamera im Würfel: Die Augen sind das Handy als Livebild über eine Seite des Gehirns (nur Tailscale), an Claude nur Einzelbilder auf Frage.
- Kameras und Mikrofone erkennbar, keine verdeckten Aufnahmen, Aufnahmen von Personen nur mit Einwilligung. Personenbezogene Daten mit `pii: true`.

## 7. Offene Punkte
- [ ] Microcontroller-Modell und Sensorliste festlegen (Vorschlag im Design: Version 1 ohne Mikrocontroller)
- [ ] Zweistufiger Hub (Microcontroller plus Pi Zero 2 W) oder reiner Microcontroller
- [x] Speicherziel: Gedächtnis auf dem Laptop, Sicherung verschlüsselt auf externer Festplatte zu Hause (13.10.2026)
- [x] Vektordatenbank: sqlite-vec mit FTS5, dazu LanceDB als Vergleich und Ersatz (13.10.2026). LanceDB vor Nutzung nach Checkliste prüfen
- [x] Retention-Fristen pro Datentyp mit Merk-Schutz (13.10.2026, Notion „Design Gehirn“)
- [ ] Freigabe-Policy für physische Aktionen
- [x] Separates Google-Testkonto statt privatem Account (13.10.2026). Anlegen: Marvin
- [x] Monatsbudget API-Key: höchstens 20 € (15.10.2026). Aufteilung bestätigt
- [ ] SIM-Anbieter wählen: höchstens 10 € im Monat, 3–5 GB, beim Kauf aktuell vergleichen (E-Mail: mail.de FreeMail, Konto legt Marvin an)
- [x] Design Körper Version 1 freigegeben (13.10.2026, `docs/design-koerper.md`)
- [x] Bauplan Körper Version 1 bestätigt (13.10.2026)
- [x] Änderung Körper: Abstand statt Kamera, Livebild übers Handy, freigegeben (15.10.2026)
- [x] Design Gehirn Version 1 freigegeben (13.10.2026, `docs/design-gehirn.md`)
- [x] Bauplan Gehirn Version 1 bestätigt (13.10.2026, `docs/bauplan-gehirn-v1.md`)
- [x] Design Charakter Version 1 freigegeben (14.10.2026, `docs/design-charakter.md`)
- [x] Bauplan Charakter Version 1 bestätigt (14.10.2026, `docs/bauplan-charakter-v1.md`)
- [x] Design Umgebungsbewusstsein und Datensammlung freigegeben (14.10.2026, `docs/design-daten.md`)
- [x] Bauplan Datensammlung Version 1 bestätigt (14.10.2026, `docs/bauplan-daten-v1.md`)
- [x] Design Code-Skills und Umgebungsauswertung freigegeben (15.10.2026, `docs/design-code-umgebung.md`)
- [x] Bauplan Code-Skills Version 1 bestätigt (15.10.2026, `docs/bauplan-code-umgebung-v1.md`)
- [ ] Gehirn Phase 0: Bestandsaufnahme und Inhalte sichern (Marvin, `docs/checkliste-phase0-gehirn.md`). Löschen noch nicht freigegeben
- [x] Testweg und angepasste Baupläne bestätigt (15.10.2026): Gehirn zuerst, dann Handy als Test-Würfel (Bauplan Gehirn 11.5–11.8), erst danach Stufe 2 kaufen
- [ ] Testweg durchführen (nach Gehirn Phase 1–11)
- [ ] Phase 1: Teile Stufe 1 bestellen (Marvin, `docs/einkauf-stufe1.md`)
- [ ] Laptop als Gehirn: Modell, RAM, Speicher, Akkuzustand und Betriebssystem erfassen und Eignung prüfen (dabei AVX2 prüfen, für LanceDB)
- [ ] Superpowers in Claude Code installieren und Telemetrie abschalten (macht Marvin, siehe `docs/projektstart-details.md`)
- [x] Design Data Lakehouse freigegeben (16.10.2026, `docs/design-lakehouse.md`)
- [x] Bauplan Data Lakehouse bestätigt (16.10.2026, `docs/bauplan-lakehouse-v1.md`), Phase 1 gebaut
- [ ] Such-API für Schlaubis Recherche wählen (Bauplan Gehirn 13.1, Vergleich `docs/vergleich-such-apis.md`). Staan-Konto angelegt (16.10.2026), wartet auf Freischaltung, danach Nutzungsbedingungen prüfen
- [ ] Design Wissensarchitektur freigeben (Entwurf 16.10.2026, `docs/design-wissen.md`). Wie Modul-Wissen behandelt wird (gesichert oder zu prüfen), entscheidet der Live-Test. Bis zur Such-API: kostenlose Quellen (Wikipedia, Wikidata, Marginalia, Fachliteratur) und eigene Vektor-Suche (Marvin, 16.10.2026)
- [ ] Prototyp A (Chat mit echtem Kern und Profil, claude.ai-Seite, `tools/prototyp/`) testen: Marvin
- [ ] Sperre für Secret-Dateien als Hook (`.env`, `*.key`, `secrets/`, `credentials*.json`, `token*.json`), erst wenn das Projekt fertig ist (Marvin, 16.10.2026)
