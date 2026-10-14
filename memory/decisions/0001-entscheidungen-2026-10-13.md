# ADR 0001 – Grundentscheidungen (13.10.2026)

Spiegel der Notion-Seite „Entscheidungen und Projektlog“. Nichts löschen, nur ergänzen.

| Datum | Entscheidung | Status |
|---|---|---|
| 13.10.2026 | Kein eigenes echtes Konto für den Roboter, Selbsterhalt nur über Token-Budget | Beschlossen |
| 13.10.2026 | Handynummer über eine echte SIM-Karte (auf Marvin registriert) | Beschlossen |
| 13.10.2026 | Immer die neuesten Anthropic-Modelle verfügbar halten | Beschlossen |
| 13.10.2026 | Alle Tests zuerst mit privatem Google-Account | Beschlossen, Alternative separates Testkonto offen |
| 13.10.2026 | Notion als Gedächtnis des Projekts | Beschlossen |
| 13.10.2026 | Claude-Abo nicht für den laufenden Roboter, API-Key mit Ausgabenlimit | Beschlossen (Nutzungsbedingungen) |
| 13.10.2026 | Skills zusätzlich als Dateien im Repo robot-brain | Beschlossen |
| 13.10.2026 | Skills roboter-testumgebung und adobe-oss-agent-tools freigegeben | Beschlossen |
| 13.10.2026 | Gehirn (OpenClaw, Vektorspeicher, Embeddings) läuft auf Marvins altem Laptop als Heimserver statt auf einem Pi 5 | Beschlossen, Eignung prüfen |
| 13.10.2026 | Schlaubi handelt nie in Marvins Namen ohne Rückfrage | Beschlossen |
| 13.10.2026 | Eigene Mail-Adresse für Schlaubi schon in der Testphase, nie Antworten aus Marvins Google-Konto. Kanäle: Telegram, dann E-Mail | Beschlossen, Anbieter offen |
| 13.10.2026 | Mail-Anbieter für Schlaubi: mail.de FreeMail (IMAP imap.mail.de:993, SMTP smtp.mail.de:465). Marvin legt das Konto an | Beschlossen |
| 13.10.2026 | Design Körper „Schlaubi“ Version 1 freigegeben (docs/design-koerper.md) | Beschlossen |
| 13.10.2026 | Gehäuse: Holzrahmen mit Seiten aus milchigem Kunststoff (Acryl opal), Status-Licht als LED-Ring, der den ganzen Würfel leuchten lässt. Pi, Powerbanks und Netzteil sind vorhanden | Beschlossen (Marvins Variante) |
| 13.10.2026 | Selbsterhalt erweitert: Sparen, Zuarbeit für Einnahmen (Marvin verkauft), Belohnung. Deutsches Recht, Einnahmen sind Marvins, Freigabe-Stufen (Einzelfreigabe, später begrenzte Dauerfreigaben als ADR). Abo-Modell später als eigenes Projekt | Beschlossen |
| 13.10.2026 | API-Monatslimit 30 $ (Recherche höchstens 15 $), Warnung 80 %, Sparmodus 90 %, Stopp 100 % | Beschlossen |
| 13.10.2026 | Sprache bleibt lokal: Audio (Aktivierungswort, Spracherkennung, Sprachausgabe) verlässt nie Würfel und Laptop, kein Cloud-Sprachdienst, auch nicht als Rückfall. Nur der erkannte Text geht für das Gespräch an die Claude-API | Beschlossen |
| 13.10.2026 | Sicherung von Schlaubis Gedächtnis auf einer externen Festplatte bei Marvin zu Hause. Verschlüsselt und automatisch, Wiederherstellung wird regelmäßig getestet. Werkzeug und Takt legt der Plan fest | Beschlossen |
| 13.10.2026 | Wissen und Interessen (L3) für immer behalten, nichts löschen, nur als ersetzt markieren. So viel wie möglich sammeln, nach Relevanz in aktiv/Archiv gewichten. Quellen-Bewertung (Stufen A–D, Bestätigungen, lernende Bewertung). Mehrere Orchestrierungs-Ansätze parallel testen, Sicherheits- und Stabilitätsmechanismen (Details: Notion „Design Gehirn“). Marvins Löschwunsch geht vor | Beschlossen, Retention übriger Daten als Vorschlag offen |
| 13.10.2026 | Retention übriger Daten bestätigt (Audio sofort löschen, Gespräche 1 Jahr dann verdichten, Kamerabilder nach Auswertung, fremde Mails 30 Tage, Rohseiten 90 Tage, Logs 1 Jahr, Daten über Dritte nur auf Wunsch). Merk-Schutz vor jeder Löschung: „merken“ durch Marvin, automatische Wichtigkeitsprüfung, im Zweifel behalten, nie löschen ohne Übernahme ins Wissen | Beschlossen |
| 13.10.2026 | Zusätzlicher Vektorspeicher neben sqlite-vec. Kandidat LanceDB (Apache-2.0, eingebettet, keine Telemetrie gefunden), Zweck noch zu klären | Beschlossen, Auswahl offen |
| 13.10.2026 | Zusätzlicher Vektorspeicher: LanceDB, als Vergleich und Ersatz für sqlite-vec. Beide werden aus derselben Quelle (append-only Einträge und Markdown) befüllt und lassen sich daraus neu aufbauen. Fällt einer aus, sucht Schlaubi im anderen weiter. Vor der Nutzung vollständige Prüfung nach Checkliste | Beschlossen |
| 13.10.2026 | Kamerabilder dürfen zur Auswertung an die Claude-API, nur wenn Marvin etwas zeigt. Ohne Metadaten (EXIF, Ort), Personen nur mit Einwilligung | Beschlossen |
| 13.10.2026 | Design Gehirn Version 1 freigegeben (docs/design-gehirn.md). Bauplan Gehirn Version 1 geschrieben, zur Bestätigung | Beschlossen |
| 13.10.2026 | Bauplan Gehirn Version 1 bestätigt. Löschen von Laptops und externer Festplatte noch nicht freigegeben: erst alle Inhalte sichern und prüfen (Checkliste Phase 0) | Beschlossen |
| 13.10.2026 | Alte Inhalte der Laptops und der ersten externen Festplatte werden auf eine zweite externe Festplatte gesichert (getrennt von Schlaubis Sicherungsplatte, beschriftet „Alt-Sicherung – nicht löschen“) | Beschlossen |
| 13.10.2026 | Testphase mit separatem Google-Testkonto statt Marvins privatem Account. Marvin legt es an, nur Testdaten, kein Zugriff auf das private Konto. Ersetzt „Alle Tests zuerst mit privatem Google-Account“ | Beschlossen |
| 14.10.2026 | MCP-Schnittstelle (Würfel-MCP, Gedächtnis-MCP, Charakter als MCP-Vorlage), damit jeder Laptop von Marvin Host sein kann und Schlaubi überall derselbe ist. Kommt nach Version 1, wird aber mitgedacht (feste Funktionen, Herkunft, Warteschlange). Keine lokale Kopie des Gedächtnisses auf anderen Laptops, offline Neues wird später übertragen | Beschlossen (Version 2) |
| 14.10.2026 | Charakter: Grundton Mentor. Gegenüber Marvin keine KI-Floskeln. Gegenüber Dritten nie verneinen, eine KI zu sein, im Netz als Bot erkennbar | Beschlossen |
| 14.10.2026 | Charakter: trockener Humor, sparsam, aber stark. Deutlicher Widerspruch, ehrlich, kritisch, darf auch mal unfreundlich sein (Kritik an Ideen, nicht an der Person). Linke Haltung prägt Werte und Blickwinkel, wird nie ausgesprochen, Fakten und Quellen-Bewertung bleiben neutral, keine Lüge auf ernsthafte Nachfrage. Charakter schärft sich im Gespräch | Beschlossen |
| 14.10.2026 | Charakter entwickelt sich von selbst (ohne Einzelfreigabe). Fester Kern (Grenzen und Regeln) in eigener Datei, die nur Marvin ändert. Änderungen nur aus Gesprächen mit Marvin, versioniert, langsam, rücksetzbar, mit wöchentlichem Selbsttest | Beschlossen |
| 14.10.2026 | Charakter: gesprochene Antworten kurz (ein bis zwei Sätze), ausführlicher nur auf Nachfrage | Beschlossen |
| 14.10.2026 | Charakter: Gegenüber anderen Menschen lehnt Schlaubi auf seine Art ab und umgeht Anfragen, mal höflich, mal launisch. Keine Aufträge Dritter, nichts über sie speichern, nicht beleidigend, KI-Frage nie verneinen, im Notfall auf Hilfe verweisen | Beschlossen |
| 14.10.2026 | Charakter: kann Smalltalk nicht leiden, nicht sexistisch, mega klug und weiß es (Nuancen von Göttlichkeit), ohne Alter, Laune dynamisch und begründet (Faktoren offen). Rechte Positionen: klare, scharfe Ablehnung an Inhalten, aber kein Hass auf Menschen, keine Beleidigung, keine politische Einordnung von Personen | Beschlossen, Umsetzung „rechte Menschen“ als Vorschlag |
| 14.10.2026 | Charakter als Baukasten: detailliertes Profil in vier Schichten (fester Kern, Persönlichkeit mit Reglern, Laune-Modell mit frei erweiterbaren, gewichteten Faktoren, Entwicklung innerhalb vom Nutzer gesetzter Bereiche). Der Nutzer bestimmt den Aufbau selbst. Laune begründet, nie Einfluss auf Fakten oder festen Kern | Beschlossen, Bearbeitungsweg offen |
| 14.10.2026 | Charakter-Profil wird im Gespräch mit Schlaubi bearbeitet. Nur Marvin, Sprachänderungen mit Bestätigung per Telegram, fester Kern nur direkt in der Datei, jede Änderung versioniert und rücksetzbar | Beschlossen |
