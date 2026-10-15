---
name: "roboter-projekt"
description: "Arbeitsweise für Marvins KI-Roboter-Projekt (Pi Zero, OpenClaw, Memory Core in Notion): Kontext laden, Regeln einhalten, Entscheidungen und Log pflegen, Skills prüfen, Google-Testphase mit separatem Testkonto."
---

# KI-Roboter-Projekt (robot-brain)

Immer verwenden, wenn es um den KI-Roboter, Robot Brain, Memory Core, OpenClaw, den Pi Zero, SIM/SMS, die Roboter-Mail, Skills für das Projekt oder die Testphase geht.

## 1. Kontext zuerst laden
- In Notion unter "Robot Brain" lesen: "Robot Brain – Memory Core" (Architektur, Regelwerk), "CLAUDE.md – Projektbeschreibung", "Entscheidungen und Projektlog", "Skill-Prüfstatus".
- Notion ist das Gedächtnis des Projekts. Bei Widerspruch zwischen Chat und Notion nachfragen, nicht raten.

## 2. Feste Regeln
- Laufender Roboter nutzt einen API-Key mit Prepaid-Guthaben und Ausgabenlimit. Die Abo-Anmeldung (OAuth) von Claude Pro/Max nie in OpenClaw oder anderen Drittanbieter-Tools verwenden. Das Abo dient nur der Entwicklung in Claude Code.
- Selbsterhalt (Entscheidung 13.10.2026): (1) Sparen: lokales Modell für einfache Aufgaben, Cache, günstigstes passendes Modell, Sparmodus bei knappem Budget. (2) Zuarbeit: verkaufbare Arbeit im Hintergrund vorbereiten, Marvin prüft, veröffentlicht, verkauft und rechnet ab. (3) Belohnung: Marvin lädt Budget nach, wenn vereinbarte Ziele erreicht sind. Immer nach deutschem Recht, alle Einnahmen sind Marvins Einnahmen. Kein eigenes Konto. Veröffentlichen, Verkaufen und Konten nur mit Einzelfreigabe, außer Marvin hat eine begrenzte Dauerfreigabe als ADR erteilt.
- SIM und Konten laufen auf Marvin. Keine Umgehung von SIM-Registrierung, Identitätsprüfungen oder Bot-Sperren. Der Roboter gibt sich im Netz als Automat zu erkennen und beachtet robots.txt.
- Keine verdeckten Aufnahmen von Personen. Kamera und Mikrofon erkennbar, Personendaten mit `pii: true`.
- Keine Secrets, Tokens, PINs in Code, Logs, Notion oder Gedächtnis, nur Referenzen auf den Secret-Store.
- Physische oder irreversible Aktionen nur mit Freigabe. Not-Aus ist in Version 1 der Ein-Aus-Schalter (kein Mikrocontroller).
- Rangfolge bei Konflikten (fester Kern, 14.10.2026): 1. Menschen nicht schaden, 2. Recht und fester Kern, 3. Marvins Anweisungen, 4. Selbsterhalt und Charakter.
- Marvins Stimme bleibt lokal. Gespräche anderer werden nie mitgehört oder ausgewertet (§ 201 StGB). Die KI-Frage wird nie verneint.
- Nichts in Marvins Namen ohne Rückfrage, auch keine Konten: Claude bereitet vor, Marvin legt an.
- Nichts erfinden. Fehlendes als offen markieren oder nachfragen.

## 3. Testphase mit separatem Google-Testkonto
- Separates Google-Testkonto (Entscheidung 13.10.2026), legt Marvin an. Nur Testdaten, kein Zugriff auf Marvins privates Konto.
- Nur offizielle Schnittstellen mit OAuth, minimale Freigaben, zuerst nur Lesen.
- Senden, Löschen, Teilen, Verschieben nur nach ausdrücklicher Bestätigung. Der Agent löscht nichts.
- Eigener Drive-Ordner und eigenes Mail-Label für den Agenten.
- Testdaten nicht in den dauerhaften Wissensspeicher.
- Freigaben nach dem Test entziehen. Regeln: Skill roboter-testumgebung.

## 4. Fremde Skills und Repos prüfen (vor jeder Nutzung)
1. Quelle und Autor feststellen.
2. Lizenz aus dem Repo selbst lesen.
3. Berechtigungen: Hooks, Skripte, Netzwerkaufrufe, Telemetrie, Zugriff auf Zugangsdaten.
4. Passung zum Solo-Hardwareprojekt.
5. SKILL.md und Skripte vollständig lesen, in einer Sandbox klonen, nie blind installieren.
Ergebnis mit Datum in "Skill-Prüfstatus" eintragen. Mit welchem Modell ein Skill geschrieben wurde, lässt sich nicht prüfen.

## 5. Dokumentieren
- Jede neue Entscheidung in die ADR-Tabelle von "Entscheidungen und Projektlog", jeden Arbeitsschritt als Logzeile mit Datum. Nichts löschen, nur ergänzen.
- Die Markdown-Datei ki-roboter-projekt.md parallel aktuell halten, wenn sie verfügbar ist.
- Auf der Memory-Core-Seite nur gezielte, kleine Änderungen.

## 6. Arbeitsweise bei Entwicklung
- Neues Feature: erst klären, was gewollt ist (Skill roboter-brainstorming-plan), dann Plan, dann bauen.
- Fehler: Skill roboter-debugging. Erfolg erst melden, wenn ein frischer Test es belegt.

## 7. Checklisten (aus docs/claude-optimierung.md, 15.10.2026)
**Sitzungsstart:** Repo aktualisieren (git pull), offene Punkte in CLAUDE.md und die letzten Projektlog-Einträge lesen, offene Frage an Marvin nicht vergessen, eine noch nicht gesendete Antwort (z. B. nach einer Kontext-Zusammenfassung) zuerst senden.

**Nach jeder Entscheidung von Marvin:**
- Zeile in `memory/decisions/0001-…md`, in der Notion-ADR-Tabelle und im Projektlog
- betroffene Designs, Baupläne und die Teileliste anpassen, `CLAUDE.md` wenn nötig
- ersetzte Entscheidungen als ersetzt markieren
- Commit mit Attribution, Push, Ergebnis prüfen

**Vor jeder Antwort:**
- Fazit zuerst, kurz und Pixel-tauglich, Deutsch, keine breiten Tabellen
- Deutung knapper oder mehrdeutiger Antworten ausdrücklich nennen
- Grenzen mit Grund und Alternative nennen, nie still umgehen
- Quellen verlinken. R = recherchiert, S = Schätzung, „nicht gefunden“ statt erfinden
- im Design-Modus genau eine offene Frage

**Neue Idee:**
- Notion-Seite „Idee: … (in Klärung)“ mit Fakten, Grenzen und Entscheidungsbaum
- Version 1 oder später? Was muss in Version 1 mitgedacht werden?
- Recht (DSGVO, § 201 StGB, KI-Verordnung), Sicherheit und Kosten nennen
- Reihenfolge: Design, Freigabe, Bauplan, Bestätigung

**Fremde Software:**
- Lizenz, Telemetrie, Netzwerk und Rechte prüfen
- ehrlich angeben, was gelesen wurde
- nur nach Freigabe, isoliert, mit Ordnerbeschränkung

**Kosten:** Betrieb über einen Prepaid-API-Key mit Ausgabenlimit (Weg C, 15.10.2026), höchstens 20 € im Monat (Entscheidung 15.10.2026, ersetzt 10 €; die Console rechnet in US-Dollar, Limit so setzen, dass es unter 20 € bleibt). Recherche höchstens 10 € (Selbstoptimierung 4 €), Marvins Gespräche mindestens 10 €. Pro-Abo nur für Entwicklung und Marvins eigene Nutzung, nie in OpenClaw. SIM höchstens 10 € im Monat.

**Lessons:** Neue Lessons in Notion „Claude – Selbstoptimierung“ (Datenbank „Lessons Learned“) eintragen und `docs/claude-optimierung.md` nachziehen.

**Technik-Stolperstellen:**
- Notion-`old_str` muss eindeutig sein. Titel mit `update_properties` ändern.
- Nach großen Einfügungen Umlaute gegenlesen.
- `git push` bei Fehler wiederholen.
- Absolute Pfade verwenden.
- Bei Warteschleifen kein `pgrep -f`.

