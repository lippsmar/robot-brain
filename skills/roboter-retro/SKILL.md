---
name: "roboter-retro"
description: "Rückblick auf eine Arbeitssitzung am KI-Roboter (Hardware oder Software): herausfinden, was Zeit gekostet hat oder schiefging, und Verbesserungen an Regeln, Skills, Prüfungen und Notion vorschlagen. Verwenden, wenn Marvin um einen Rückblick, eine Retro oder Lehren aus einer Sitzung bittet."
---

# Rückblick (Retro) für den KI-Roboter

Angepasst aus dem Skill retro von mattpocock/skills (MIT-Lizenz, Copyright (c) 2026 Matt Pocock).

## Ziel
Nicht die Arbeit bewerten, sondern die **Umgebung** verbessern, damit die nächste Sitzung schneller und sicherer läuft: Regeln, Skills, Prüfskripte, Notion-Seiten, Werkzeuge.

## Ablauf
1. **Sitzung festlegen.** Ohne Angabe die aktuelle Sitzung. Sonst die genannte Sitzung, ihr Projektlog-Eintrag in Notion und die zugehörigen Commits.
2. **Quellen lesen.** Verlauf der Sitzung, Projektlog und Entscheidungen in Notion, `git log`, Event-Log und Messprotokolle, falls vorhanden. Nur belegbare Befunde, jeweils mit Quelle (Datei und Zeile, Commit oder Notion-Seite). Nichts erfinden.
3. **Kandidaten suchen**, in diesen Bereichen:
   - **Kontext finden:** Wie lange hat es gedauert, die richtige Notion-Seite, Datei oder Information zu finden? Würde ein Verweis in CLAUDE.md, INDEX.md oder auf der Notion-Startseite helfen?
   - **Automatische Prüfungen:** Gab es einen Fehler, den ein Test, ein Prüfskript, ein Linter oder eine Messung früher gefunden hätte? Erst prüfen, ob es so eine Prüfung schon gibt und sie nur nicht lief.
   - **Hardware und Sicherheit:** Gab es Probleme mit Strom, Pegeln, Verkabelung, Not-Aus oder Freigaben? Fehlt ein Messpunkt oder ein Sicherheitsschritt im Plan? Diese Befunde zuerst nennen.
   - **Regeln und Skills:** Wurde eine Regel ignoriert, war sie unklar oder fehlt sie? Gibt es Regeln, die nichts bewirken und gestrichen werden können? Gleiche Regel an mehreren Stellen: auf eine Stelle zusammenführen.
   - **Werkzeuge:** Gab es teure oder umständliche Schritte, die ein kleines Skript oder ein besserer Befehl abkürzen würde?
   - **Informationszugang:** Fehlte eine wichtige Information (Logs, Datenblatt, Messwerte, Zugriff)? Wie käme der Agent künftig daran, ohne neue Rechte oder Secrets?
4. **Vorschläge zeigen**, nach Wichtigkeit sortiert (Sicherheit zuerst). Je Vorschlag: Befund mit Quelle, konkrete Änderung, wo sie hingehört, Aufwand.
5. **Freigabe abwarten.** Nichts ändern, bevor Marvin einzelne Vorschläge freigegeben hat. Danach umsetzen und als Logzeile mit Datum in "Entscheidungen und Projektlog" festhalten.

## Wo gehört eine Verbesserung hin?
- **Mechanisch prüfbar** (feste Regel, Format, Wertebereich): als Test, Prüfskript oder Schema, nicht als Text.
- **Ermessensfrage**: als Regel in den passenden Skill oder in CLAUDE.md.
- **CLAUDE.md** knapp halten, dort vor allem Verweise auf Skills und Notion-Seiten.
- **Entscheidungen** gehören in die ADR-Tabelle, nicht in Skills.
