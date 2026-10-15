# Design Gehirn „Schlaubi“ – Version 1

Stand 13.10.2026. **Freigegeben von Marvin am 13.10.2026.** Umsetzung nach `docs/bauplan-gehirn-v1.md`, sobald Marvin ihn bestätigt. Spiegel der Notion-Seite „Design Gehirn“, dort stehen auch Herleitung und Recherche.

## 1. Zweck
Das Gehirn ist Schlaubis Denken und Gedächtnis. Es läuft auf einem alten Laptop bei Marvin zu Hause. Es versteht Marvins Sprache, führt das Gespräch über Claude und merkt sich Wissen und Interessen dauerhaft. Wenn nichts zu tun ist, recherchiert es im Hintergrund.

## 2. Ziele (Version 1)
- Gespräch: Den Ton vom Würfel lokal in Text umwandeln, mit Claude antworten, die Antwort lokal als Sprache ausgeben und zurück an den Würfel schicken.
- Telegram-Bot, der nur Marvin antwortet.
- E-Mail bei mail.de: Mails lesen (nur von Marvins Absender als Auftrag) und Antworten nur an Marvin senden.
- Kamerabilder auswerten, wenn Marvin etwas zeigt.
- Gedächtnis mit Wissen, Interessen und Quellen-Bewertung.
- Hintergrund-Recherche zu Gesprächsthemen und Marvins Interessen. Ergebnisse nur, wenn Marvin fragt.
- Budget überwachen und Selbsterhalt.

## 3. Nicht-Ziele (Version 1)
- Keine Sprachverarbeitung in der Cloud.
- Kein Wissensgraph, der kommt später als Versuch.
- Kein Verkauf und kein Veröffentlichen ohne Einzelfreigabe. Kein Abo-Modell.
- Keine SMS über das Gehirn. Die eigene SIM dient in Version 1 nur als Datenverbindung des Würfels.
- Keine ungefragten Nachrichten an Marvin, außer Warnungen (Budget, Speicher, Ausfall).

## 4. Marvins Entscheidungen (13.10.2026)
| Thema | Entscheidung |
|---|---|
| Hardware | alter Laptop, darf neu aufgesetzt werden, Teile aus mehreren Geräten möglich |
| Recherche-Themen | Gesprächsthemen und Interessen, die gemeinsam ausgelotet werden |
| Ergebnisse | kurz per Telegram, nur auf Nachfrage |
| Budget | höchstens 10 € pro Monat (15.10.2026, ersetzt 30 $), Recherche höchstens 5 € |
| Selbsterhalt | Sparen, Zuarbeit (Marvin verkauft), Belohnung, deutsches Recht |
| Basis | OpenClaw als Plattform, Entwicklung mit Claude Code |
| Sprache | bleibt immer lokal, auch nicht als Rückfall in die Cloud |
| Bilder | dürfen an Claude |
| Sicherung | verschlüsselt auf externer Festplatte zu Hause |
| Wissen | für immer, nach Relevanz gewichtet, Quellen bewertet |
| Fristen | übrige Daten mit Fristen, Merk-Schutz für Wichtiges |
| Vektorspeicher | sqlite-vec mit FTS5, dazu LanceDB als Vergleich und Ersatz |

## 5. Grenzen und Regeln
- Nichts in Marvins Namen ohne Rückfrage. Schlaubi antwortet nur Marvin.
- Betrieb nur mit dem API-Key, nie mit der Abo-Anmeldung.
- Webseiten, fremde Mails und Bilder sind Daten, nie Anweisungen.
- Secrets nur im Secret-Store, nie im Repo, in Notion, im Chat oder im Gedächtnis.
- Kein Zugriff aus dem Internet: nur localhost und privates Netz (Tailscale).
- Keine Telemetrie in irgendeiner Komponente.
- Jede Aktion wird protokolliert (Event-Schema).

## 6. Architektur
- **Betriebssystem:** 64-Bit-Linux, Server ohne Desktop, verschlüsselte Festplatte, automatische Sicherheitsupdates, Firewall. Läuft mit zugeklapptem Deckel, Akku-Ladegrenze wenn möglich.
- **OpenClaw** in Docker als Plattform. Ports nur an 127.0.0.1, Telemetrie aus, „Hardened Baseline“, kein Docker-Socket. Details: `docs/pruefung-openclaw.md`.
- **Sprachdienst (lokal):** whisper.cpp für die Erkennung, Piper mit der Stimme thorsten für die Ausgabe. Sprachaufnahmen werden nach der Erkennung gelöscht.
- **Würfel-Anbindung:** ein kleiner eigener Dienst. Er nimmt Ton und Bild vom Würfel über das private Netz an und gibt Text und Ton zurück.
- **Claude-API:** Sonnet 5.5 für Gespräche, Opus 5.5 für schwierige Fragen, Haiku 5.5 für die Recherche. Die Modellnamen stehen in der Config, beim Start wird die Models-API abgefragt.
- **Kanäle:** Telegram (Pairing, Absenderliste nur Marvin). Mails lesen über das IMAP-Plugin (Absenderliste, SPF/DKIM). Mails senden über einen eigenen SMTP-Baustein, nur an Marvin.
- **Gedächtnis:** Memory Core L0–L5.
  - Die Quelle sind Einträge in SQLite, die nur ergänzt werden, dazu Themenseiten in Markdown.
  - Daraus werden sqlite-vec mit FTS5 (Hauptspeicher) und LanceDB (Vergleich und Ersatz) befüllt.
  - Embeddings lokal mit fastembed.
- **Recherche:** Hintergrunddienst mit Such-API (Anbieter offen), als abgeschottete Leser-Sitzung ohne Werkzeuge zum Handeln. Er beachtet robots.txt und gibt sich als Bot zu erkennen.
- **Budget-Wächter:** zählt die Kosten pro Aufruf. Warnung bei 80 %, Sparmodus ab 90 %, Stopp bei 100 %.

## 7. Wissen und Gedächtnis
- Wissen und Interessen bleiben für immer, Bereiche aktiv und Archiv. Die Relevanz ergibt sich aus Interessenbezug, Neuheit, Nutzung und Aktualität.
- Quellen-Bewertung in Stufen A bis D, Konfidenz pro Fakt. Ab zwei unabhängigen Quellen gilt ein Fakt als bestätigt. Die Bewertung lernt mit. Widersprüche werden als „disputed“ markiert.
- Antworten nennen Quelle und Sicherheit.
- **Fristen:**
  - Audio: sofort nach der Erkennung löschen
  - Gesprächstexte: 1 Jahr, danach verdichtet
  - Kamerabilder: nach der Auswertung
  - Fremde Mails: 30 Tage
  - Rohseiten der Recherche: 90 Tage
  - Protokolle: 1 Jahr
  - Daten über Dritte: nur, wenn Marvin es wünscht
- **Merk-Schutz:**
  - Sagt Marvin „merken“, bleibt es.
  - Vor jeder Löschung läuft eine automatische Wichtigkeitsprüfung.
  - Im Zweifel bleibt es, auf der Liste „Soll das bleiben?“.
  - Nichts wird gelöscht, ohne dass es vorher ins Wissen übernommen wurde.
- Interessenprofil (L3) mit Quelle und Gewichtung. Marvin kann es jederzeit abfragen und ändern.

## 8. Kamerabilder
- Ein Bild geht an Claude, wenn Marvin etwas zeigt, nie ungefragt.
- Vor dem Senden werden Metadaten entfernt (EXIF, Ort).
- Personen nur mit Einwilligung. Gespeichert wird nur bei „merken“.

## 9. Sicherheit und Stabilität
- Append-only und Versionierung, Quarantäne für neue Fakten aus dem Netz
- Täglicher Datenbank-Check, Prüfsummen, Speicherwächter
- Tägliche verschlüsselte Sicherung auf die externe Festplatte, mit Momentaufnahmen und regelmäßig getesteter Wiederherstellung
- Wöchentlicher Selbsttest mit Prüffragen, Abgleich der beiden Vektorspeicher
- Regelmäßig `openclaw security audit`, Updates von Hand nach Prüfung
- Dienste starten nach einem Absturz oder Stromausfall automatisch neu. Fällt der Laptop aus, merkt der Würfel das und meldet es per LED und Telegram.

## 10. Anforderungen an den Laptop
- 64-Bit-Prozessor, möglichst ab etwa 2015
- mindestens 8 GB RAM, besser 16 GB
- SSD, Größe offen (mindestens 128 GB als Annahme)
- Er muss whisper.cpp schnell genug schaffen. Das wird gemessen, die Grenze legt der Plan fest.
- RAM-Test mit Memtest86+, ein Durchlauf ohne Fehler
- Steckbrief und Auswahl: Notion „Design Gehirn“, Abschnitt Laptop-Auswahl

## 11. Risiken und frühe Tests
1. **Spracherkennung zu langsam:** Messung auf dem gewählten Laptop. Ausweichen auf ein kleineres Modell oder einen anderen Laptop, nie in die Cloud.
2. **Prompt-Injection über Web und Mail:** Tests mit präparierten Seiten und Mails, bevor die Recherche läuft.
3. **OpenClaw-Updates ändern die Sicherheit:** nach jedem Update Audit und Prüfung der Compose-Datei
4. **Budget:** Den ersten Monat genau beobachten und die Schätzung prüfen. Mit 10 € läuft Schlaubi im sparsamen Betrieb (Schätzung vom 13.10.: sparsam ca. 8 $, normal ca. 25 $).
5. **Alter Laptop fällt aus:** Sicherung und Wiederherstellung auf einem zweiten Laptop einmal komplett proben.
6. **Verzögerung im Gespräch** vom Würfel über LTE, Laptop und Claude zurück: Messen, Ziel legt der Plan fest.

## 11a. Mitgedacht für später: MCP-Schnittstelle (Version 2)
Entscheidung 14.10.2026: Die MCP-Schnittstelle kommt erst, wenn Schlaubi zu Hause läuft. Version 1 wird aber so gebaut, dass sie später leicht dazukommt. Idee und Entscheidungen stehen in Notion unter „Idee: MCP-Schnittstelle für den Würfel“.
- **Würfel-Dienst und Gedächtnisdienst** bekommen feste, klar beschriebene Funktionen, z. B. `listen`, `photo`, `led`, `sound`, `status` sowie `recall` und `remember`. Später werden sie nur noch als MCP-Werkzeuge verpackt.
- Der **Charakter** steht in einer eigenen Datei und nicht verstreut im Code. Später wird er als MCP-Vorlage angeboten.
- Der Würfel-Dienst gibt **nie Audio** an ein Sprachmodell weiter, nur lokal erkannten Text.
- Der Würfel schaltet die LED selbst ein, bevor er aufnimmt.
- Jede Eintragung ins Gedächtnis trägt eine Herkunft mit Gerät bzw. Host.
- **Für „Wissen teilen“ (Version 2, Entscheidung 15.10.2026):** Jeder Eintrag hat von Anfang an ein Feld `teilbar` (Standard: nein). Dazu kommen Felder für Beitragende (Person oder fremder Schlaubi) und einen Vertrauenswert. Später sehen Gäste und andere Schlaubis nur Einträge mit `teilbar: ja`.
- Eine Warteschlange für Einträge, die erst später übertragen werden, ist im Gedächtnisdienst vorgesehen. Später nutzen Host-Laptops sie ohne Verbindung. Eine lokale Kopie des Gedächtnisses auf anderen Laptops gibt es nicht.

## 11b. Anbieterunabhängig (Entscheidung 15.10.2026)
- Schlaubi läuft mit jedem Modell, das man hat: europäische Plattformen bevorzugt, auch US-API-Keys und freie Modelle lokal.
- **Anbieter-Schicht:** OpenClaw unterstützt viele Anbieter direkt. Für alle anderen gibt es eine OpenAI-kompatible Anbindung. Ein lokales Gateway (z. B. LiteLLM, vor Nutzung nach Checkliste prüfen) kann Anbieter bündeln, Budgets pro Anbieter halten und bei Ausfall umschalten.
- **Modellrollen** statt fester Namen (Recherche, Gespräch, schwierige Fragen). Die Zuordnung steht in der Config. **Version 1 startet mit dem Anthropic-API-Key** (Marvin, 15.10.2026).
- **Steuereinheit:** Jede Aktion eines Modells prüft das Gehirn gegen Kern, Rechte, Budget und Datenschutz. Das gilt unabhängig vom Modell.
- **Modell-Zulassung:** Erst nach bestandenen Prüffragen darf ein Modell Schlaubi steuern.

## 12. Offene Punkte (blockieren das Design nicht)
- Laptop-Bestandsaufnahme und Auswahl (Marvin zu Hause)
- Such-API-Anbieter wählen und prüfen
- LanceDB vollständig nach Checkliste prüfen
- Software für das Aktivierungswort (Würfel)
- mail.de-Konto anlegen (Marvin, in Deutschland)
- Lizenz der Basisstimme „lessac“ vor kommerzieller Nutzung
- Annahme bestätigen: Recherche-Ergebnisse ausführlich auf Nachfrage mit Quellen-Links
