# Projektstart – technische Details

Aus dem Chat „Autonomer Lernroboter“ vom 12./13.10.2026. Vollständiger Verlauf in Notion: „Chat-Protokoll 13.10.2026 – Projektstart KI-Roboter“ (Robot Brain). Diese Datei sammelt die Einzelheiten, die nicht schon in CLAUDE.md, Memory Core oder den Skills stehen.

## Hardware
- **Körper:** Raspberry Pi Zero 2 W. Der alte Pi Zero ist zu schwach.
- **Gehirn:** Raspberry Pi 5 mit 8 GB oder Heimserver. Dort laufen OpenClaw, Vektorspeicher und Embeddings. Der Zero 2 W (512 MB) bleibt Körper.
- **Sensoren:** über I2C und GPIO, z. B. Abstand, Temperatur, Kamera, Mikrofon. Motoren oder Servos optional.
- **Externer Speicher:** USB-Stick per OTG, NAS oder Cloud, jeweils mit Backups.

## Mobilfunk (SIM)
- LTE-Modem-HAT, z. B. **Waveshare SIM7600 oder SIM7670**.
- **Kein SIM800L:** 3G ist in Deutschland abgeschaltet, 2G ist unsicher.
- Stromspitzen des Modems bis etwa **2 A**: stabiles Netzteil oder Pufferkondensator.
- SMS per AT-Befehlen, `gammu` oder `ModemManager`. Die SIM liefert auch mobiles Internet.
- Prepaid-SIM mit Daten und SMS, in Deutschland auf Marvin registriert. Verfall bei Nichtnutzung beachten.
- Sprachanrufe möglich, aber aufwendig. Start mit SMS.
- Alternative für die Nummer: Dienst wie Twilio.

## E-Mail
- Eigene Adresse bei einem Provider, Zugriff per IMAP/SMTP oder API.

## KI und Modelle
- KI läuft per API in der Cloud, der Pi ist nur Client und Steuerung.
- API-Key aus der Anthropic Console, Prepaid-Guthaben, monatliches Ausgabenlimit.
- Modelle laut Stand 13.10.2026: Claude Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5.
- **Aufteilung:** Haiku für Hintergrundrecherche, Sonnet oder Opus für Gespräche mit Marvin.
- Modellname in einer Config-Datei. Beim Start die Models-API abfragen und bei neuen Modellen Marvin melden.
- Selbsterhalt: eigene Kostenzähler pro Aufruf, bei knappem Budget drosseln, Marvin per Mail oder SMS zum Nachladen auffordern.

## Lernen und Gedächtnis
- „Lernen“ heißt Wissen sammeln, nicht Modelltraining.
- Hintergrunddienst recherchiert per Such-API, die KI fasst zusammen, Ergebnisse werden gespeichert und passende Einträge später in den Prompt geholt.
- **Vektorspeicher:** SQLite mit sqlite-vec und FTS5 (Hybridsuche). Alternative: LanceDB.
- **Embeddings:** kleine ONNX-Modelle (bge-small, MiniLM) über fastembed. Anthropic bietet keine Embeddings an.
- **Langzeitgedächtnis in Schichten:** Rohprotokoll, Tageszusammenfassungen, dauerhafte Fakten (siehe L0 bis L5 in `memory/SYSTEM_PROMPT.md`).
- **Persönlichkeit** über den System-Prompt: immer verfügbarer, loyaler Assistent, klug, gewitzt, unkonventionell.

## OpenClaw absichern
Anfang 2026 waren laut einer Quelle über 135.000 OpenClaw-Instanzen offen erreichbar, meist ohne Authentifizierung.
- In Docker betreiben, nur an `localhost` binden.
- Gateway-Token setzen (im Secret-Store, nicht im Repo).
- Zugriff von außen nur über ein privates Netz wie Tailscale.
- Regelmäßig `openclaw security audit` ausführen.
- ClawHub-Skills vor der Nutzung lesen und nach `skills/INDEX.md` prüfen.

## Energie
- Unbegrenzt Strom geht nicht. Ein 10.000-mAh-Akku mit Modem hält grob ein bis zwei Tage.
- Dauerbetrieb mit Netzteil, UPS-HAT mit USB-C-Laden als Puffer.

## Datenschutz und Auftreten im Netz
- Vollständige Anonymität ist nicht möglich: API-Key und SIM laufen auf Marvin, SIM-Registrierung mit Ausweis ist Pflicht.
- Umsetzbar: lokale Datenhaltung, verschlüsselte Laufwerke, keine Telemetrie, VPN, möglichst wenig persönliche Daten an die API.
- Der Roboter gibt sich im Netz als Bot zu erkennen. Keine Umgehung von Bot-Sperren.
- Unauffälliges Gehäuse ist in Ordnung. Kameras und Mikrofone erkennbar, Aufnahmen von Personen nur mit Einwilligung.

## Claude Code vom Handy
- Keine eigene App: Cloud-Sitzungen und Remote Control liegen im Code-Tab der Claude-App (Android und iOS).
- Cloud-Sitzung: im Code-Tab oder über claude.ai/code/new starten.
- Remote Control: am Rechner `claude remote-control` oder in einer Sitzung `/remote-control`, dann QR-Code scannen. Dateien bleiben lokal, der Rechner muss laufen. Für den Roboter (Gehirn-Rechner) passend.
- Quelle: https://code.claude.com/docs/de/mobile

## Superpowers in Claude Code
- Installation durch Marvin: `/plugin install superpowers@claude-plugins-official`, Telemetrie mit `SUPERPOWERS_DISABLE_TELEMETRY=1` abschalten.

## Adobe-Nachbauten (Instagram-Beitrag von evolving.ai)
Von Marvin am 13.10.2026 als Screenshot nachgereicht. Aussagen des Beitrags, nicht überprüft:
- Ein Entwickler bzw. Team (ArtCraft) hat sieben Adobe-Apps neu gebaut, laut Beitrag „mit Hilfe von Claude Opus 5.5“, frei, Open Source, in Rust, ohne Adobe-Code, aus öffentlichen Spezifikationen und durch Beobachten des Verhaltens.
- Die „Crafting Apps“: PhotoCraft (Photoshop), VectorCraft (Illustrator), FilmCraft (Premiere Pro), LightCraft (Lightroom), EffectCraft (After Effects), PdfCraft (Acrobat Pro) und ein InDesign-Nachbau (Name im Screenshot nicht sichtbar).
- KI-Agenten wie Claude sollen jede App steuern können.
- PhotoCraft soll in den ersten zehn Tagen über 25.000 GitHub-Sterne bekommen haben. Andere Quellen nennen abweichende Zahlen.
- Geprüft ist bisher nur PhotoCraft (siehe `skills/INDEX.md`). Die anderen sechs Apps sind ungeprüft und werden vor Nutzung nach `skills/adobe-oss-agent-tools` geprüft.
- Mit welchem Modell der Code geschrieben wurde, lässt sich aus dem Repo nicht belegen.

## Nicht verfügbare Quellen
- Datei `ki-roboter-projekt.md` aus dem Chat: liegt nur im Chat. Gegenstück ist die Notion-Seite „Entscheidungen und Projektlog“.
