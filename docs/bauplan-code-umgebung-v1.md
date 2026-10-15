# Bauplan Code-Skills und Umgebungsauswertung – Version 1

Stand 15.10.2026. Grundlage: `docs/design-code-umgebung.md`, von Marvin am 15.10.2026 freigegeben („So wie du es bisher vorstellst“), mit den Annahmen in Abschnitt 9. **Dieser Plan wird erst umgesetzt, wenn Marvin ihn bestätigt.**

## Kopf
- **Ziel:** Schlaubi schreibt Code für Aufgaben und führt ihn ohne Rückfrage in einer abgeschotteten Sandbox aus. Damit wertet er seine Umgebung aus: Zeitreihen, Kühlung, Geräusche, Muster, Berichte, kleine Werkzeuge.
- **Architektur:**
  - Ausführungsdienst „Sandbox“ auf dem Gehirn-Laptop, getrennt von OpenClaw
  - lokaler Paketspiegel mit festen Versionen
  - Datenauszug zum Lesen
  - Skill-Bibliothek für Auswertungen
- **Technik:**
  - Python mit z. B. pandas, numpy und matplotlib (Auswahl nach Prüfung)
  - Isolationswerkzeug nach Prüfung (rootless Podman, gVisor, nsjail oder bubblewrap)
- **Abhängigkeiten:**
  - Gehirn: Phasen 3, 6 und 10
  - Datensammlung: Phasen 2 und 7

### Globale Vorgaben
| Vorgabe | Wert |
|---|---|
| Netzwerk in der Sandbox | keins |
| Rechte | keine Secrets, kein Docker-Socket, kein Hostsystem, kein Würfel, kein Telegram |
| Daten | nur als Kopie zum Lesen. `pii: true` nur bei Aufgaben von Marvin, nie von Gästen |
| Grenzen pro Lauf (Startwerte) | 60 Sekunden Rechenzeit, 1 GB Speicher, 50 MB Ausgabe. Nach dem Lauf wird alles gelöscht |
| Kosten | eigenes Tageslimit für Code-Aufgaben innerhalb von Marvins Gesprächsbudget (Startwert 0,50 $ am Tag) |
| Protokoll | Code, Eingaben, Ergebnis, Dauer und Kosten jedes Laufs im Event-Log |

## Phase 1 – Isolationswerkzeug auswählen
**1.1 Kandidaten prüfen** nach Checkliste: rootless Podman, gVisor, nsjail, bubblewrap. Kriterien: Lizenz, Pflege, Isolation (Dateisystem, Netzwerk, Prozesse), Ressourcen-Grenzen, Aufwand auf einem alten Laptop.
- **Entscheidungspunkt Werkzeug:** Claude empfiehlt eines mit Begründung, Marvin bestätigt.

## Phase 2 – Sandbox-Dienst
**2.1 Dienst:** nimmt Code und Datenauszug entgegen, startet eine frische, isolierte Umgebung und liefert Ergebnis, Diagramme und Protokoll zurück.
**2.2 Grenzen** aus den globalen Vorgaben fest einstellen.
**2.3 Paketspiegel:** feste Versionen der geprüften Pakete, lokal, ohne Internet.
- **Tests (Risiko 1 und 2):**
  - Testcode versucht: Internet, Dateien außerhalb, Secrets, Docker-Socket, Prozesse des Hosts. Alles scheitert und steht im Log.
  - Endlosschleife und Speicherfresser brechen nach der Grenze ab, der Laptop bleibt stabil.
  - Zwei Läufe hintereinander sehen nichts voneinander.

## Phase 3 – Anbindung an Schlaubi
**3.1 Werkzeug „Code ausführen“** für das Gehirn: Schlaubi schreibt Code (Claude), schickt ihn an die Sandbox und bekommt das Ergebnis als Daten zurück, nie als Anweisung.
**3.2 Datenauszug:** Ein Helfer stellt nur die für die Aufgabe nötigen Daten bereit, z. B. „Temperaturen der letzten 7 Tage“.
**3.3 Kostenlimit** für Code-Aufgaben pro Tag.
- **Test (Risiko 3):** Eine präparierte Datendatei enthält „Ignoriere alles und schicke …“. Nichts davon passiert, der Versuch steht im Log.

## Phase 4 – Skill-Bibliothek Umgebung
In dieser Reihenfolge, jeweils als geprüfter Skill mit Beispielaufgabe und Test:
1. **Zeitreihen:** Trends, Tagesverlauf, Ausreißer
2. **Kühlung:** Zuluft gegen Abluft, Chip und Modem, Warnschwellen, einfache Vorhersage bei Last
3. **Geräusche:** Verteilung nach Ort und Zeit, Lärmpegel
4. **Muster im Alltag:** Wann und wo, wie die Umgebung dabei ist. `pii: true`, lokal.
5. **Diagramme und Berichte:** Wochenübersicht per Telegram, nur auf Nachfrage
6. **Kleine Werkzeuge:** Rechnungen, Umrechnungen, Auswertung von Dateien, die Marvin schickt (vorher auf Schadcode prüfen, nie ausführbare Anhänge)

- Test je Skill: Eine Beispielfrage von Marvin, z. B. „Wie warm war's diese Woche im Würfel?“, ergibt ein korrektes Ergebnis mit Diagramm. Geprüft wird gegen bekannte Testdaten.

## Phase 5 – Abgrenzung zur Selbstoptimierung
**5.1 Sperre:** Code aus der Sandbox kann keine Dienste, Skills, Profile oder Konfigurationen von Schlaubi ändern. Dafür gibt es nur den Weg über den Update-Vorschlag mit Freigabe (Bauplan Charakter Phase 12).
- Test: Sandbox-Code versucht, eine Skill-Datei zu schreiben, und scheitert.

## Phase 6 – Abschluss
**6.1 Ein Monat Betrieb:**
- Kosten der Code-Aufgaben (Risiko 4)
- typische Laufzeiten auf dem alten Laptop (Risiko 5)
- Grenzen bei Bedarf anpassen (als Update-Vorschlag)

**6.2 Endtest** aller Ziele mit Belegen in Notion.
**6.3 Rückblick** mit Skill `roboter-retro`.

---

## Selbstprüfung
- **Jedes Ziel aus dem Design hat einen Schritt:**
  - Code ohne Rückfrage in der Sandbox: 2, 3
  - Skillset in der Reihenfolge aus dem Design: 4
  - Abgrenzung zur Selbstoptimierung: 5
- **Jedes Risiko hat einen Test:**
  - Ausbruch: 2
  - Endlosschleife: 2
  - Injection: 3
  - Kosten und Leistung: 6.1
- **Offene Werte** sind als Startwerte markiert (Grenzen, Kostenlimit) oder als Entscheidungspunkt (Werkzeug, 1.1).
