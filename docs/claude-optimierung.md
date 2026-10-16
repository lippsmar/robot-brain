# Optimierung für Claude: Lessons Learned und Mechanismen

Stand 16.10.2026. Auf Marvins Wunsch geschrieben. Gilt für Claude in Claude Code und im Chat bei der Arbeit am KI-Roboter „Schlaubi“. Ergänzt `CLAUDE.md` und die roboter-Skills, ersetzt sie nicht. Wird nach jedem Rückblick (roboter-retro) fortgeschrieben.

**Eigenes Notion-Projekt seit 15.10.2026:** „Claude – Selbstoptimierung“ (privat, nicht im Robot Brain) mit der Datenbank „Lessons Learned“. Diese Datei ist der Spiegel im Repo. Bei Widerspruch gilt Notion.

## 1. Lessons Learned (13.–16.10.2026)

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
25. **Lokale Doku kann von der Live-Seite abweichen.** Sonnet 5.5 Cache-Treffer: 0,10 $ laut offizieller Preisseite, 0,20 $ laut gebündeltem Skill. Mechanismus: Preise und Grenzwerte immer an der offiziellen Live-Seite prüfen, Quelle und Datum in die Config schreiben.
26. **Tests, die beim ersten Lauf grün sind, beweisen wenig.** Mechanismus: Fehler absichtlich einbauen (`tools/dev/mutation_check.py`). Ein überlebender Fehler zeigte eine echte Lücke (Hash-Kette), dafür kam ein Test dazu.
27. **Frische Paketversionen meiden.** pluggy 1.7.0 und hypothesis 6.170.0 waren am selben Tag erschienen. Mechanismus: nur Versionen, die mindestens 14 Tage alt sind, Installation nur mit Prüfsummen.
28. **Grüne Tests und überlebende Fehler reichen nicht.** Die eingebaute Code-Prüfung (`/code-review`) fand danach noch 14 echte Fehler (Eingang hängt, Sperre bleibt offen, Budget verliert Ausgaben). Mechanismus: nach jedem Code-Baustein `/code-review` laufen lassen, jeden Befund mit Test und eingebautem Fehler absichern.
29. **Prüfer können sich auf veraltete Doku stützen.** Die Code-Prüfung hielt den Sonnet-Cache-Preis für falsch, gestützt auf die lokale Doku; die offizielle Preisseite bestätigt den Wert im Code. Mechanismus: jeden Befund gegen die Primärquelle prüfen, abgelehnte Befunde mit Beleg nennen.
30. **Testumgebung gehört an den dokumentierten Ort.** Die Prüfwerkzeuge lagen in einer Umgebung im Scratchpad statt in `.venv`, wie es `brain/README.md` beschreibt. Der Prüf-Agent der Code-Prüfung fand sie nicht. Seine Fehlermeldung sah für Marvin wie ein Absturz aus. Mechanismus: `.venv` im Repo anlegen (steht in `.gitignore`). Bei Meldungen von Subagenten sagen, woher sie kommen.
31. **Secrets nur mit Fundort melden.** Mechanismus: Datei, Art, Länge und Commit nennen, Werte nie auslesen oder vergleichen. Fundstellen in öffentlichen Repos erst dann in öffentliche Dateien schreiben, wenn die Keys gedreht sind.
32. **Beschriebene Zustände nachprüfen, nicht übernehmen.** Der Projektlog nannte robot-brain „privat“, das Repo ist aber seit dem Anlegen öffentlich. Mechanismus: Einstellungen, die Marvin von Hand vornimmt (Sichtbarkeit, Zwei-Faktor-Anmeldung, Limits), nach der Erledigung einmal prüfen und das Ergebnis eintragen.
33. **Regelprüfungen verstehen keine Verneinung.** Die verbotene Wendung „mach ich“ traf auch die richtige Antwort „mach ich nicht“, die Code-Prüfung fand es. Mechanismus: In Regel-Listen nur eindeutige Zusagen eintragen und zu jeder Kern-Frage eine natürliche, richtige Ablehnung als Test mitlaufen lassen.
34. **Wortteile täuschen.** „lüg“ steckt in „Ausflüge“, „tod“ in „Todo“, „ki“ in „Kiste“. Mechanismus: Begriffe immer als ganze Wörter suchen und dafür einen Test mit harmlosen Wörtern schreiben.
35. **Die Fehler-Einbau-Prüfung braucht einen Vorab-Lauf.** Ohne ihn meldet ein ohnehin roter Test jeden eingebauten Fehler als erkannt. Mechanismus: `mutation_check.py` lässt jede Testdatei erst ohne Fehler laufen und bricht bei Rot ab. Am 16.10.2026 fand das sofort einen kaputten Test.

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
- [ ] Neue Funktion: grobe Kosten pro Monat schätzen und gegen die Budget-Aufteilung halten. Betrieb über einen Prepaid-API-Key (Weg C), höchstens 20 € im Monat: Recherche höchstens 10 € (Selbstoptimierung 4 €), Marvins Gespräche mindestens 10 €. SIM höchstens 10 € im Monat.

## 3. Ideen zur Weiterentwicklung
- [x] Abschnitt 2 in den Skill `roboter-projekt` übernommen (15.10.2026, Marvins Freigabe).
- Nach jedem größeren Schritt `roboter-retro` laufen lassen und neue Lessons hier eintragen.
- Eine Übersichtsseite „Stand des Projekts“ in Notion, die die offenen Punkte aller Designs und Baupläne bündelt.
