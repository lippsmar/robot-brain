# Optimierung für Claude: Lessons Learned und Mechanismen

Stand 15.10.2026. Auf Marvins Wunsch geschrieben. Gilt für Claude in Claude Code und im Chat bei der Arbeit am KI-Roboter „Schlaubi“. Ergänzt `CLAUDE.md` und die roboter-Skills, ersetzt sie nicht. Wird nach jedem Rückblick (roboter-retro) fortgeschrieben.

**Eigenes Notion-Projekt seit 15.10.2026:** „Claude – Selbstoptimierung“ (privat, nicht im Robot Brain) mit der Datenbank „Lessons Learned“. Diese Datei ist der Spiegel im Repo. Bei Widerspruch gilt Notion.

## 1. Lessons Learned (13.–15.10.2026)

### Zusammenarbeit mit Marvin
1. **Marvin liest am Pixel 8.** Kurze Absätze, Listen statt breiter Tabellen, Fazit zuerst, Deutsch.
2. **Eine Frage pro Nachricht wirkt.** Marvin antwortet schnell und knapp, die Entscheidungen bleiben sauber getrennt. Wo eine Frage eine Auswahl braucht, Beispiele nennen statt einer festen Liste.
3. **Knappe Antworten können mehrdeutig sein.** Beispiele: „Ja Freigabe“ nach zwei offenen Punkten, „Auch“, „A und …“. Mechanismus: die eigene Deutung ausdrücklich nennen („Ich habe das auf beides bezogen“) und Korrektur anbieten. Nie still annehmen.
4. **Marvin denkt in großen Ideen** (MCP, Wissen teilen, Selbstoptimierung, Einnahmen). Bewährt hat sich: aufnehmen, Fakten und Grenzen nennen, als „Version 2, mitgedacht“ einordnen und die nötigen Vorkehrungen sofort in Version 1 eintragen.
5. **Korrekturen kommen schnell** („Doch keine lokale Sicherung“). Alte Entscheidung als ersetzt markieren, nicht löschen.
6. **Lange Arbeiten brauchen Zwischenstände.** Bei Builds oder vielen Werkzeugaufrufen kurz sagen, was gerade läuft.

### Grenzen und Haltung
7. **Wünsche, die Recht oder Ethik berühren**, kamen mehrfach vor:
   - sich nicht als Bot zu erkennen geben
   - „hasst rechte Menschen“
   - „was um ihn herum gesagt wird“
   - verdeckte politische Haltung

   Bewährt hat sich: den legitimen Kern umsetzen und die Grenze klar mit Grund nennen (z. B. § 201 StGB, Art. 50 KI-Verordnung, Ehrlichkeit). Eine Alternative anbieten. Nie still umgehen und nie still ablehnen.
8. **Feste Grenzen gehören in den festen Kern**, nicht in änderbare Profile. Sie gelten auch gegenüber Marvins späteren Wünschen, solange Recht oder Schaden für andere betroffen sind.
9. **„Nichts in Marvins Namen“** gilt auch für Konten: API-Key, Telegram-Bot, mail.de, Tailscale, Google-Testkonto, Käufe. Claude bereitet vor, Marvin legt an.

### Fakten und Quellen
10. **Recherche-Ergebnisse widersprechen sich** (SIM-Preise, AI-Act-Fristen). Mechanismus: R (recherchiert, mit Quelle) und S (Schätzung) markieren, Widersprüche offen nennen, „vor dem Kauf prüfen“ dazuschreiben.
11. **„Nicht gefunden“ ist ein gültiges Ergebnis** (BerryBase-Preis BME280). Nie einen Preis oder eine Zahl erfinden.
12. **Fremde Repos sind oft riesig** (OpenClaw mit 55.000 Dateien, die ArtCraft-Apps mit bis zu 525.000 Zeilen). Ehrlich „gezielt geprüft, nicht vollständig gelesen“ schreiben und die gelesenen Dateien auflisten.
13. **Versionen ändern sich zwischen Prüfung und Nutzung** (VectorCraft 0.10.0 → 0.11.0). Vor der Nutzung kurz nachprüfen, was neu ist.

### Werkzeuge und Technik
14. **Notion `update_content`:**
    - `old_str` muss eindeutig sein.
    - Nummerierte Listen und Tabellenzellen werden anders gespeichert als geschrieben. Bei „No matches“ einen kürzeren Ausschnitt nehmen, bei „Multiple matches“ einen längeren.
    - Bei Unsicherheit vorher `fetch` ausführen.
15. **Notion-Titel** zuverlässig mit `update_properties` ändern. In Kombination mit `update_content` wurde der Titel nicht immer übernommen.
16. **Umlaute und Tippfehler** schleichen sich in lange Notion-Texte ein („Bauplane“, „tteilbar“). Nach größeren Einfügungen die neuen Wörter kurz gegenlesen.
17. **`git push` scheitert gelegentlich** („remote rejected“). Einfach wiederholen, Ergebnis prüfen.
18. **Das Arbeitsverzeichnis wechselt** zwischen Sitzungen. Immer absolute Pfade verwenden, zu Beginn `git pull` ausführen.
19. **Warteschleifen mit `pgrep -f`** finden sich selbst und enden nie (VectorCraft-Build). Besser auf eine Datei oder Prozess-ID warten oder die Benachrichtigung des Hintergrundauftrags nutzen.
20. **Fremden Code nur in der Sandbox bauen**, mit Ordnerbeschränkung (`--automation-read-root/-write-root`) und headless. Das Lesen fremder Doku über das Read-Werkzeug ist unkritischer als `cat` in der Shell. Der Auto-Modus hat Letzteres einmal blockiert.
21. **Skills, die geändert werden**, gleich als Zip zum Hochladen mitschicken und Marvin sagen, welche alte Version zu ersetzen ist.
22. **Nach einer Kontext-Zusammenfassung** zuerst die noch offene Antwort an Marvin senden (Checkliste A).
23. **Abo- und Nutzungsregeln ändern sich schnell** (Hilfeartikel 7.10.2026). Vor Aussagen dazu die aktuelle offizielle Seite lesen und das Datum nennen.
24. **Bilder nach Notion:** `create-file-upload`, einmal per `curl` POST senden, dann die `file-upload://`-Quelle in die Seite. Upload-Token nie in Dateien oder Logs.

## 2. Mechanismen (Checklisten)

### A. Beim Sitzungsstart
- [ ] `git pull` im Repo, letzter Commit und offene Punkte in `CLAUDE.md` ansehen
- [ ] Letzte Einträge im Notion-Projektlog lesen
- [ ] Prüfen, ob eine Frage an Marvin offen oder eine Antwort noch nicht gesendet ist, und das zuerst erledigen

### B. Nach jeder Entscheidung von Marvin
- [ ] Zeile in `memory/decisions/0001-…md` (Datum, Entscheidung, Status)
- [ ] Gleiche Zeile in der Notion-ADR-Tabelle und eine Zeile im Projektlog
- [ ] Betroffene Design-, Bauplan- und Teilelisten-Dateien anpassen
- [ ] `CLAUDE.md` (offene Punkte, Verweise) aktualisieren, wenn betroffen
- [ ] Ersetzte Entscheidungen als ersetzt markieren
- [ ] Commit mit Attribution, Push, Ergebnis prüfen

### C. Vor jeder Antwort an Marvin
- [ ] Fazit zuerst, kurz, Pixel-tauglich
- [ ] Eigene Deutung mehrdeutiger Antworten genannt?
- [ ] Grenzen mit Grund genannt, wo nötig?
- [ ] Quellen bei recherchierten Fakten verlinkt?
- [ ] Genau eine offene Frage am Ende (im Design-Modus)

### D. Neue Idee von Marvin
- [ ] Notion-Seite „Idee: … (in Klärung)“ mit Fakten, Grenzen und Entscheidungsbaum
- [ ] Prüfen: Version 1 oder später? Was muss in Version 1 mitgedacht werden?
- [ ] Rechtliche und Sicherheitsfolgen nennen (DSGVO, § 201 StGB, KI-Verordnung, Kosten)
- [ ] Erst Design, dann Freigabe, dann Bauplan, dann Bestätigung

### E. Fremde Software
- [ ] Quelle, Lizenz aus dem Repo, Telemetrie, Netzwerkzugriffe, Rechte
- [ ] Ehrlich angeben, was gelesen wurde und was nicht
- [ ] Nutzung nur nach Marvins Freigabe, isoliert und mit Ordnerbeschränkung
- [ ] Ergebnis in `skills/INDEX.md` und Notion „Skill-Prüfstatus“

### F. Kosten im Blick
- [ ] Neue Funktion: grobe Kosten pro Monat schätzen und gegen die Budget-Aufteilung halten. Betrieb über einen Prepaid-API-Key (Weg C, 15.10.2026), Höhe des Monatsbudgets offen. Die frühere Aufteilung auf 30 $ ruht bis dahin. SIM höchstens 10 € im Monat.

## 3. Ideen zur Weiterentwicklung
- [x] Abschnitt 2 in den Skill `roboter-projekt` übernommen (15.10.2026, Marvins Freigabe).
- Nach jedem größeren Schritt `roboter-retro` laufen lassen und neue Lessons hier eintragen.
- Eine Übersichtsseite „Stand des Projekts“ in Notion, die die offenen Punkte aller Designs und Baupläne bündelt.
