---
name: "roboter-projekt"
description: "Arbeitsweise für Marvins KI-Roboter-Projekt (Pi Zero, OpenClaw, Memory Core in Notion): Kontext laden, Regeln einhalten, Entscheidungen und Log pflegen, Skills prüfen, Google-Testphase."
---

# KI-Roboter-Projekt (robot-brain)

Immer verwenden, wenn es um den KI-Roboter, Robot Brain, Memory Core, OpenClaw, den Pi Zero, SIM/SMS, die Roboter-Mail, Skills für das Projekt oder die Testphase geht.

## 1. Kontext zuerst laden
- In Notion unter "Robot Brain" lesen: "Robot Brain – Memory Core" (Architektur, Regelwerk), "CLAUDE.md – Projektbeschreibung", "Entscheidungen und Projektlog", "Skill-Prüfstatus".
- Notion ist das Gedächtnis des Projekts. Bei Widerspruch zwischen Chat und Notion nachfragen, nicht raten.

## 2. Feste Regeln
- Laufender Roboter nutzt einen API-Key mit Prepaid-Guthaben und Ausgabenlimit. Die Abo-Anmeldung (OAuth) von Claude Pro/Max nie in OpenClaw oder anderen Drittanbieter-Tools verwenden. Das Abo dient nur der Entwicklung in Claude Code.
- Selbsterhalt = Budget überwachen, drosseln, Marvin zum Nachladen auffordern. Kein eigenes Konto, kein selbständiges Geldbeschaffen.
- SIM und Konten laufen auf Marvin. Keine Umgehung von SIM-Registrierung, Identitätsprüfungen oder Bot-Sperren. Der Roboter gibt sich im Netz als Automat zu erkennen und beachtet robots.txt.
- Keine verdeckten Aufnahmen von Personen. Kamera und Mikrofon erkennbar, Personendaten mit `pii: true`.
- Keine Secrets, Tokens, PINs in Code, Logs, Notion oder Gedächtnis, nur Referenzen auf den Secret-Store.
- Physische oder irreversible Aktionen nur mit Freigabe. Not-Aus läuft lokal auf dem Microcontroller.
- Nichts erfinden. Fehlendes als offen markieren oder nachfragen.

## 3. Testphase mit Marvins privatem Google-Account
- Nur offizielle Schnittstellen mit OAuth, minimale Freigaben, zuerst nur Lesen.
- Senden, Löschen, Teilen, Verschieben nur nach ausdrücklicher Bestätigung. Der Agent löscht nichts.
- Eigener Drive-Ordner und eigenes Mail-Label für den Agenten.
- Inhalte aus dem privaten Account nur auf ausdrücklichen Wunsch in den dauerhaften Wissensspeicher.
- Freigaben nach dem Test entziehen. Offene Option: separates Testkonto.

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