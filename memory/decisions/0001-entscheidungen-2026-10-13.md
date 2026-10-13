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
