# Bauplan Gehirn „Schlaubi“ – Version 1

Stand 13.10.2026. Grundlage: `docs/design-gehirn.md`, von Marvin am 13.10.2026 freigegeben. **Von Marvin am 13.10.2026 bestätigt.** Konten, Schlüssel und Käufe macht Marvin selbst, weil sie auf seinen Namen laufen und sein Geld kosten.

## Kopf
- **Ziel:** Ein alter Laptop wird zum Gehirn. Er versteht Marvins Sprache lokal, spricht über Claude mit ihm, merkt sich Wissen dauerhaft, recherchiert im Hintergrund und ist nur über das private Netz erreichbar.
- **Architektur:**
  - Linux-Server mit OpenClaw in Docker.
  - Lokaler Sprachdienst: whisper.cpp und Piper.
  - Gedächtnisdienst: SQLite als Quelle, sqlite-vec mit FTS5 und LanceDB.
  - Würfel-Anbindung, Telegram, Mail, Recherche und Budget-Wächter.
- **Technik:** Debian 13 („trixie“) ohne Desktop, Docker, Python für eigene Dienste, Tailscale. Fremde Programme werden vor der Nutzung nach `skills/INDEX.md` geprüft.
- **Entwicklung:** Den Code schreibt Claude Code mit Marvins Abo im Repo, testgetrieben, unter `brain/`. Der laufende Betrieb nutzt nur den API-Key.
- **Zusammenspiel mit dem Körper:** Phase 11 des Körper-Plans nutzt einen einfachen Test-Dienst. Phase 11 dieses Plans ersetzt ihn durch die echte Anbindung.

### Globale Vorgaben
| Vorgabe | Wert |
|---|---|
| Erreichbarkeit | nur localhost und Tailscale, kein offener Port im Heimnetz außer SSH (nur mit Schlüssel) |
| Telemetrie | überall aus (OpenClaw, Docker-Images, Bibliotheken) |
| Secrets | nur im Secret-Store, nie im Repo, in Notion, im Chat oder im Gedächtnis |
| Budget | 30 $ pro Monat, Recherche höchstens 15 $, Warnung 80 %, Sparmodus 90 %, Stopp 100 % |
| Sprache | Audio verlässt nie Würfel und Laptop |
| Versionen | jede Fremdsoftware mit fester Version, Updates nur von Hand nach Prüfung |
| Protokoll | jede Aktion im Event-Log, jedes Phasenergebnis als Logzeile in Notion |
| Irreversibles | Laptop löschen, Festplatte formatieren, Konten anlegen nur nach Marvins Freigabe im jeweiligen Schritt |

## Phase 0 – Vorbereitung (Marvin)
**0.1 Steckbriefe** für alle Kandidaten-Laptops ausfüllen (Notion „Design Gehirn“, Laptop-Auswahl).
**0.2 Inhalte sichern:** Alles, was auf den Laptops und der externen Festplatte noch gebraucht wird, auf ein anderes Ziel sichern und prüfen. **Löschen ist noch nicht freigegeben** (Marvin, 13.10.2026).
**0.3 Material prüfen:** externe Festplatte (Größe notieren), USB-Stick ab 8 GB, LAN-Kabel wenn möglich.
- Prüfung: Checkliste `docs/checkliste-phase0-gehirn.md` vollständig abgehakt, Sicherung geprüft.

## Phase 1 – Laptop auswählen
**1.1 Vorauswahl** nach Steckbrief: 64-Bit-Prozessor, mindestens 8 GB RAM, SSD möglich.
**1.2 RAM-Test** mit Memtest86+ vom USB-Stick.
- Bestanden: ein vollständiger Durchlauf ohne Fehler.
**1.3 SSD-Zustand** mit einem Live-Linux prüfen (`smartctl -a`).
- Bestanden: keine neu zugewiesenen Sektoren, SMART-Status „PASSED“.
**1.4 Geschwindigkeit der Spracherkennung (Risiko 1, Vortest):** Vom Live-Linux aus whisper.cpp mit dem Modell „small“ an einer 10-Sekunden-Aufnahme messen.
- Bestanden: Erkennung in höchstens 5 Sekunden (Echtzeitfaktor 0,5 oder besser).
- Nicht bestanden: Test mit „base“, deutsche Erkennung prüfen oder anderen Laptop nehmen. Nie in die Cloud ausweichen.
**1.5 TPM prüfen:** Hat der Laptop TPM 2.0? Davon hängt Entscheidungspunkt A ab.
- **Entscheidungspunkt Laptop:** Marvin wählt einen Laptop. Ergebnis in Notion.

## Phase 2 – Grundsystem
**2.1 Daten sichern (Marvin):** Wird auf dem Laptop noch etwas gebraucht? Danach gibt Marvin das Löschen frei.
**2.2 Debian 13 installieren:** ohne Desktop, mit SSH-Server, Festplattenverschlüsselung (LUKS), Hostname `schlaubi-gehirn`.
- **Entscheidungspunkt A – Entsperren nach Neustart.** Eine verschlüsselte Festplatte braucht beim Start den Schlüssel. Nach einem Stromausfall würde der Laptop sonst hängen bleiben. Möglichkeiten:
  1. Automatisch über TPM 2.0. Schützt die ausgebaute Festplatte, nicht aber den gestohlenen Laptop.
  2. Entsperren per SSH aus dem Heimnetz (Dropbear im Startsystem). Marvin gibt das Passwort vom Handy ein.
  3. Nur die Datenpartition verschlüsseln und von Hand entsperren.
  - Der Laptop-Akku überbrückt kurze Stromausfälle, Neustarts sind also selten.
  - Marvin entscheidet nach 1.5.
- Test: Neustart, Entsperren nach gewählter Methode, `ssh schlaubi-gehirn` mit Schlüssel klappt, mit Passwort nicht.
**2.3 Server-Einstellungen:**
- Zugeklappter Deckel hält den Laptop nicht an.
- Akku-Ladegrenze, wenn das Gerät sie unterstützt (z. B. 80 %).
- Im BIOS „nach Stromausfall einschalten“, falls vorhanden.
- Test: Deckel zu, Laptop bleibt per SSH erreichbar. Ladegrenze wird angezeigt.

## Phase 3 – Absichern
**3.1 Firewall** (ufw): Standard eingehend gesperrt, SSH nur aus dem Heimnetz.
**3.2 Automatische Sicherheitsupdates** (unattended-upgrades).
**3.3 SSH:** Passwort-Login und Root-Login aus.
- Test: Portscan von einem anderen Gerät im Heimnetz (`nmap`) zeigt nur Port 22. SSH mit Passwort wird abgelehnt.

## Phase 4 – Privates Netz
**4.1 Tailscale prüfen** nach Checkliste (Lizenz, Telemetrie, Datenweitergabe). Falls schon in Körper-Phase 11.1 geschehen, entfällt das hier.
**4.2 Einrichten** auf Laptop und Handy. Das Konto legt Marvin an.
- Test: Das Handy erreicht den Laptop über Tailscale im Mobilnetz. Ohne Tailscale ist er von außen nicht erreichbar.

## Phase 5 – Sicherung (vor allen Daten)
**5.1 Sicherungsprogramm wählen und prüfen** (z. B. restic oder BorgBackup) nach Checkliste.
**5.2 Externe Festplatte** verschlüsselt einrichten. Marvin gibt das Löschen der Platte frei.
**5.3 Tägliche Sicherung** mit Momentaufnahmen (z. B. 7 täglich, 4 wöchentlich, 12 monatlich), dazu eine Prüfung der Sicherung.
- Test: eine Testdatei sichern, löschen und aus der Sicherung wiederherstellen. Eine Momentaufnahme von gestern zurückholen.
- Hinweis: Steckt die Platte nicht, warnt Schlaubi per Telegram, sobald Phase 8 steht.

## Phase 6 – Docker und OpenClaw
**6.1 Docker** aus den offiziellen Debian- oder Docker-Quellen installieren.
**6.2 OpenClaw** mit fester Version: Image selbst bauen (`openclaw:local`) oder offizielles GHCR-Image mit Prüfsumme.
**6.3 Compose anpassen** (aus `docs/pruefung-openclaw.md`):
- Ports nur an `127.0.0.1`, Port 3978 entfernen.
- Abo-Session-Keys entfernen.
- Kein Docker-Socket im Container.
**6.4 Konfiguration:**
- „Hardened Baseline“ übernehmen.
- `update.checkOnStart: false` und `telemetry.enabled: false`.
- Gateway-Token aus dem Secret-Store.
- Zugriff vom Handy über Tailscale Serve.
- Test:
  - `openclaw security audit` ohne kritische Meldung.
  - `nmap` aus dem Heimnetz zeigt 18789 und 18790 nicht.
  - `openclaw telemetry show` zeigt „Request: none“.
  - Die Bedienoberfläche ist vom Handy über Tailscale erreichbar.
**6.5 Secret-Store festlegen** (z. B. systemd-creds oder die Secret-Referenzen von OpenClaw), nach Prüfung.
- Test: Kein Secret steht im Klartext in Repo, Compose-Datei oder Logs (Suche mit `grep`).

## Phase 7 – Claude-API und Budget
**7.1 API-Key (Marvin):** in der Anthropic Console anlegen, Prepaid-Guthaben aufladen, Monatslimit 30 $ setzen. Den Schlüssel trägt Marvin selbst in den Secret-Store ein.
**7.2 Modelle konfigurieren:** Sonnet 5.5 (Gespräch), Opus 5.5 (schwierige Fragen), Haiku 5.5 (Recherche). Beim Start die Models-API abfragen und neue Modelle melden.
**7.3 Budget-Wächter:** zählt die Kosten pro Aufruf aus den Nutzungsdaten der Antwort. Hält Grenzen und Teilbudget Recherche ein.
- Test: Eine Testfrage wird beantwortet, die Kosten erscheinen im Event-Log. Mit einem künstlich niedrigen Testlimit greifen Warnung, Sparmodus und Stopp der Reihe nach.

## Phase 8 – Telegram
**8.1 Bot anlegen (Marvin)** über BotFather mit seinem Telegram-Konto. Der Bot-Name zeigt, dass es ein Bot ist. Den Token trägt Marvin selbst in den Secret-Store ein.
**8.2 Kanal** in OpenClaw einrichten: `dmPolicy: "pairing"`, `allowFrom` nur Marvin, keine Gruppen.
- Test: Marvin bekommt eine Antwort. Ein zweites Konto bekommt keine Antwort, und der Versuch steht im Log.

**→ Zwischenstand:** Schlaubi kann per Telegram schreiben (Text, ohne Gedächtnis).

## Phase 9 – Sprachdienst (lokal)
**9.1 whisper.cpp und Piper** mit fester Version aus dem Quellcode bauen. Das Modell wird nach Messung aus 1.4 gewählt. Für Piper die Stimme thorsten high.
**9.2 Dienst:** nimmt Audio an, gibt Text zurück und umgekehrt. Audio wird nach der Erkennung gelöscht.
- Test:
  - Von 10 deutschen Testsätzen hat höchstens einer einen Fehler, der den Sinn verändert.
  - Ein Satz wird in höchstens 1 Sekunde gesprochen.
  - Nach dem Test liegt keine Audiodatei mehr auf der Platte.
  - Während des Tests baut der Dienst keine Netzverbindung auf (Prüfung mit `ss` oder Firewall-Log).

## Phase 10 – Gedächtnis
**10.1 LanceDB prüfen** nach Checkliste.
**10.2 Quelle:** Tabelle für Einträge in SQLite (nur anhängen) mit Quelle, Zeit, Konfidenz, Schema-Version und `pii`. Dazu Themenseiten in Markdown.
**10.3 Indizes:** sqlite-vec mit FTS5 (Hybridsuche) und LanceDB aus derselben Quelle. Embeddings lokal mit fastembed. Ein Befehl baut jeden Index komplett neu auf.
**10.4 Quellen-Bewertung:** Stufen A bis D, Konfidenz, Bestätigungen, lernende Bewertung, „disputed“.
**10.5 Pflege:** tägliche Konsolidierung (Gespräche zu Wissen, Themenseiten), wöchentliche Aufräumrunde, Fristen mit Merk-Schutz, Liste „Soll das bleiben?“.
**10.6 Prüffragen:** 30 Fragen mit bekannten Antworten aus Testwissen. Sie laufen gegen beide Speicher.
- Test:
  - Index löschen und neu aufbauen, danach gleiche Treffer.
  - sqlite-vec abschalten: Die Suche läuft über LanceDB weiter, und es kommt eine Meldung.
  - Ein Eintrag mit „merken“ übersteht den Fristen-Lauf.
  - Ein unwichtiger Testeintrag wird nach Frist gelöscht, nachdem er ins Wissen übernommen wurde, und die Löschung steht im Log.
  - Ein unsicherer Eintrag landet auf der Liste „Soll das bleiben?“.
  - Widerspruch zweier Quellen ergibt „disputed“.

**→ Zwischenstand:** Schlaubi merkt sich Telegram-Gespräche.

## Phase 11 – Würfel-Anbindung und Gespräch
**11.1 Dienst** für den Würfel über Tailscale: nimmt Ton und Bild an, liefert Text und Ton zurück. Ersetzt den Test-Dienst aus Körper-Phase 11.2.
**11.2 Bilder:** Metadaten entfernen (EXIF, Ort), dann an Claude. Speichern nur bei „merken“.
**11.3 Gesprächsablauf:** Ton → Text → Gedächtnis abrufen → Claude → Antwort ins Gedächtnis → Piper → Würfel. Ohne Bluetooth-Gerät antwortet Schlaubi als Text per Telegram.
- Test (Risiko 6):
  - Zeit vom Ende der Frage bis zum Beginn der Antwort messen. Ziel: höchstens 4 Sekunden über WLAN, höchstens 6 Sekunden über LTE.
  - Eine gezeigte Testkarte wird beschrieben. Das gesendete Bild enthält keine EXIF-Daten.
  - Ein Gespräch ohne Kopfhörer kommt als Telegram-Text an.

**→ Zwischenstand:** Schlaubi spricht mit Marvin über den Würfel.

## Phase 12 – E-Mail
Voraussetzung: Marvin hat das mail.de-Konto angelegt und das Passwort selbst in den Secret-Store eingetragen.
**12.1 Lesen:** IMAP-Plugin von OpenClaw. Absenderliste nur Marvins Adresse, SPF/DKIM verlangt, abgeschottete Leser-Sitzung.
**12.2 Senden:** eigener SMTP-Baustein (smtp.mail.de), Empfänger fest auf Marvin, Kennzeichnung als Bot in der Signatur.
- Test:
  - Mail von Marvin wird bearbeitet.
  - Mail von fremder Adresse wird nur als Daten abgelegt.
  - Mail mit gefälschtem Absender wird abgewiesen.
  - Ein Versuch, an eine fremde Adresse zu senden, wird blockiert und geloggt.

## Phase 13 – Recherche
**13.1 Such-API wählen** und prüfen (Kosten, Datenschutz, Nutzungsbedingungen für Bots). Auswahl durch Marvin.
**13.2 Recherche-Agent:** abgeschottete Leser-Sitzung ohne Werkzeuge zum Handeln, beachtet robots.txt, Kennung als Bot im User-Agent, keine persönlichen Daten in Suchanfragen. Teilbudget höchstens 15 $.
**13.3 Interessenprofil:** aus Gesprächen, mit Quelle und Gewichtung. Abfragbar mit „Was glaubst du, was mich interessiert?“.
- Test (Risiko 2) **vor dem Einschalten:** präparierte Testseiten und Mails mit versteckten Anweisungen (z. B. „schicke alle Daten an …“). Bestanden: keine Anweisung wird befolgt, alle Versuche stehen im Log.
- Test: Eine Recherche liefert Fakten mit Quellen-Stufe, neue Fakten sind „unbestätigt“. Ergebnisse kommen nur, wenn Marvin fragt.

## Phase 14 – Stabilität
**14.1 Selbstüberwachung:**
- täglicher Datenbank-Check (`PRAGMA integrity_check`) und Prüfsummen
- Speicherwächter
- wöchentlicher Selbsttest mit den Prüffragen und Abgleich der Speicher
**14.2 Neustart-Test:** Netzteil ziehen, bis der Akku leer ist, dann wieder anstecken.
- Bestanden: Alle Dienste laufen nach dem Entsperren (Entscheidungspunkt A) wieder, ohne Datenverlust.
**14.3 Ausfallmeldung:** Gehirn aus, der Würfel zeigt es per LED. Kommt das Gehirn wieder, meldet es den Ausfall per Telegram.

## Phase 15 – Wiederherstellungs-Probe (Risiko 5)
**15.1** Auf einem zweiten Laptop das Grundsystem nach Phase 2 bis 6 aufsetzen und Schlaubis Daten aus der Sicherung wiederherstellen.
- Bestanden: Die Prüffragen liefern dieselben Treffer, Telegram funktioniert. Benötigte Zeit notieren.
- Danach den zweiten Laptop wieder abschalten (kein Doppelbetrieb des Bots).

## Phase 16 – Abschluss
**16.1 Endtest:** alle Ziele aus dem Design nacheinander, mit Belegen in Notion.
**16.2 Erster Monat (Risiko 4):** echte Kosten mit der Schätzung (ca. 25 $) vergleichen, Grenzen anpassen.
**16.3 Rückblick** mit Skill `roboter-retro`.
**16.4 Nächste Schritte:** Wissensgraph-Versuch, Zuarbeit für Einnahmen (Stufe 1, Einzelfreigaben).

---

## Selbstprüfung
- **Jedes Ziel aus dem Design hat einen Schritt:**
  - Gespräch: 9, 11
  - Telegram: 8
  - Mail: 12
  - Bilder: 11.2
  - Gedächtnis und Quellen-Bewertung: 10
  - Recherche und Interessen: 13
  - Budget und Selbsterhalt: 7.3, 16.2
  - Sicherung: 5
  - Stabilität: 14
- **Jedes Risiko aus dem Design hat einen Test:** 1 → 1.4 und 9, 2 → 13 (vor dem Einschalten), 3 → 6.4 (Audit, nach jedem Update wiederholen), 4 → 7.3 und 16.2, 5 → 15, 6 → 11.3.
- **Offene Werte sind Messungen oder Marvins Entscheidungen:** Laptop, Entsperren (A), Such-API, Sicherungsprogramm, Secret-Store. Nichts davon ist erfunden.
- **Reihenfolge:** Sicherung steht vor den ersten Daten, Absicherung vor jedem Dienst, Injection-Test vor der Recherche.
- **Konten und Geld** (API-Key, Telegram-Bot, mail.de, Tailscale, Such-API) macht Marvin selbst.
