# Was Claude (in dieser Umgebung) nicht kann oder nicht darf

Stand 16.10.2026. Zwei verschiedene Arten von Grenzen, die oft verwechselt werden. Marvins Frage war, ob OpenClaw manches davon „hinbekommt“. Antwort: Liste A ja, Liste B nein.

## Liste A – Grenzen dieser Cloud-Sitzung (ein anderer Host, z. B. OpenClaw auf dem Laptop, kann das legal übernehmen)

Das sind keine Verbote, sondern Grenzen der jetzigen Umgebung. Auf dem Gehirn-Laptop mit OpenClaw (in Docker, an localhost, mit Gateway-Token) wäre vieles davon normal möglich.

- **Marvins Download-Ordner und seine Geräte erreichen.** Aus der Cloud-Sitzung nicht sichtbar. Ein Host auf dem Laptop sieht lokale Dateien.
- **Dauerhaft laufen und zu festen Zeiten aufwachen.** Diese Sitzung ist flüchtig. Ein Heimserver läuft durch (Hintergrundrecherche, Wochenlauf, Mail-Abruf).
- **Eigene Zugänge nutzen** (SIM, Schlaubis Mail, API-Key, Secret-Store). Hier fehlen sie absichtlich. Auf dem Laptop liegen sie im Secret-Store.
- **Geteilte IP umgehen durch eigene Leitung.** Hier bremsen arXiv und OpenAlex, weil sich viele die IP teilen. Über Marvins Anschluss mit eigenem (kostenlosem) Schlüssel fällt das weg.
- **Lokale Modelle, Mikrofon, Kamera, Sensoren, BLE, LTE.** Gibt es in der Cloud nicht, gehört aber zu Schlaubis Hardware.
- **Große, lang laufende Rechenjobs** (Embeddings bauen, Vektorindex, viele PDFs). Auf dem Laptop ohne Sitzungslimit möglich.

Kurz: Liste A ist der eigentliche Grund für den Heimserver. OpenClaw „bekommt das hin“, weil es dort läuft, wo die Daten und Geräte sind.

## Liste B – Harte Grenzen, die kein Werkzeug und keine Freigabe aufhebt

Diese gelten überall: in Claude Code, in OpenClaw, auf jedem Host. Ein anderes Werkzeug ändert daran nichts, weil die Grenze nicht technisch, sondern rechtlich oder ethisch ist. (Gespiegelt im Skill `roboter-projekt`, Abschnitt 2.)

- **Keine Raubkopien.** Keine Schattenbibliotheken (Sci-Hub, LibGen, Z-Library, Anna's Archive, Spiegel), keine Warez-, Torrent- oder IPTV-Quellen für geschützte Werke. Die Privatkopie gilt nicht für offensichtlich rechtswidrige Vorlagen (§ 53 Abs. 1 UrhG). Von Marvin am 16.10.2026 ausdrücklich gewünscht, von Claude abgelehnt.
- **Kein Umgehen von technischem Schutz.** Kein DRM entfernen (§ 95a UrhG), keine Paywall-Tricks, keine fremden oder geteilten Zugänge.
- **Kein Umgehen von Bot-Sperren für Schlaubi.** Schlaubi gibt sich im Netz als Automat zu erkennen und beachtet robots.txt. (Einzige Ausnahme: der eng begrenzte Skill `social-media-ansehen`, nur für Claude Code, nur Links von Marvin, nichts gespeichert.)
- **Kein Eindringen in fremde Systeme.** Keine Passwörter knacken, keine fremden Lücken ausnutzen, keine Schadsoftware. (Ein Sicherheitswerkzeug wie Strix nur gegen die eigene Seite, siehe `skills/INDEX.md`.)
- **Keine heimlichen Aufnahmen von Personen** (§ 201 StGB). Kamera und Mikrofon erkennbar, Gespräche anderer werden nie ausgewertet.
- **Keine Täuschung.** Keine echte Person vortäuschen, keine Fake-Bewertungen, kein Spam. Die KI-Frage wird nie verneint.
- **Nichts, was Menschen schaden kann.**

## Dazwischen – geht nur mit Marvins Ja (Projektregeln, nicht hart verboten)

Käufe, Konten, Anmeldungen, Nachrichten oder Beiträge in Marvins Namen; Löschen von Daten und Festplatten; physische oder nicht umkehrbare Aktionen; neue Pakete und fremde Skills nach Prüfung; eng begrenzte Ausnahmen wie `social-media-ansehen`. Hier bereitet Claude vor, Marvin gibt frei.
