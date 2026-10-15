# Design Code-Skills und Umgebungsauswertung – Version 1

Stand 15.10.2026. **Freigegeben von Marvin am 15.10.2026** („So wie du es bisher vorstellst“), mit den Annahmen in Abschnitt 9. Bauplan: `docs/bauplan-code-umgebung-v1.md`. Spiegel der Notion-Seite „Design Code-Skills und Umgebungsauswertung“.

## 1. Zweck
Schlaubi schreibt und führt selbst Code aus, um Aufgaben zu lösen und seine Umgebung auszuwerten. Beispiele: Sensordaten analysieren, Muster finden, Diagramme und Berichte erstellen, kleine Werkzeuge bauen. Später trainiert er damit eigene kleine Modelle.

## 2. Marvins Entscheidungen (15.10.2026)
- Ein ausgeklügeltes Skillset für Code und für die Auswertung der Umgebung.
- **Code für Aufgaben läuft ohne Rückfrage in der Sandbox.**

## 3. Zwei Arten von Code
1. **Code für Aufgaben** läuft in der Sandbox, ohne Rückfrage, mit den Grenzen aus Abschnitt 4.
2. **Code, der Schlaubi selbst verändert** (Dienste, Skills, Profil, Konfiguration), läuft immer über die Selbstoptimierung: Update-Vorschlag alle 7 Tage, Marvins Freigabe pro Punkt, Tests, Commit. Nie direkt aus der Sandbox.

## 4. Sandbox
- **Eigener, abgeschotteter Ausführungsdienst** auf dem Gehirn-Laptop, getrennt von OpenClaw und ohne Docker-Socket.
  - Kandidaten zur Prüfung nach Checkliste: rootless Podman, gVisor, nsjail, bubblewrap.
- **Kein Zugriff** auf Secrets, Gedächtnis-Schreibrechte, Hostsystem, Würfel oder Telegram.
- **Daten nur als Kopie zum Lesen**, z. B. ein Auszug aus dem Data Lake.
  - Daten mit `pii: true` nur, wenn die Aufgabe von Marvin kommt.
  - Nie von Gästen.
- **Kein Internet.**
  - Pakete kommen aus einem vorab geprüften, lokalen Paketspiegel mit festen Versionen.
  - Neue Pakete nur über die Selbstoptimierung mit Freigabe.
- **Grenzen pro Lauf:**
  - Rechenzeit, Speicher und Ausgabegröße begrenzt (Werte im Bauplan)
  - danach wird die Umgebung gelöscht
- **Protokoll:** Code, Eingaben, Ergebnis und Dauer jedes Laufs im Event-Log.
- **Ergebnisse** kommen als Daten zurück und werden wie jede Quelle behandelt. Sie sind nie Anweisungen.
- **Kosten:** Das Schreiben des Codes kostet Claude-Aufrufe. Ein eigenes Tageslimit für Code-Aufgaben innerhalb von Marvins Gesprächsbudget.
- **Keine Cloud-Ausführung** für Daten mit Personenbezug oder Audio.

## 5. Skillset (Version 1)
1. **Zeitreihen:** Temperatur, Luftfeuchte, Licht, Akku. Trends, Tagesverläufe, Ausreißer.
2. **Kühlung:** Zuluft gegen Abluft, Chip- und Modemtemperatur, Warnschwellen, Vorhersage der Temperatur bei Last.
3. **Geräusche:** Verteilung der Geräuschklassen nach Ort und Zeit, Lärmpegel.
4. **Muster im Alltag:** wann und wo Marvin arbeitet, wie die Umgebung dabei ist. Muster über Marvin bleiben lokal und löschbar.
5. **Diagramme und Berichte:** z. B. eine Wochenübersicht per Telegram, aber nur auf Nachfrage.
6. **Kleine Werkzeuge** für Marvin: Rechnungen, Umrechnungen, Auswertungen von Dateien, die Marvin schickt (nur nach Prüfung auf Schadcode, nie ausführbare Anhänge).

**Später (Version 2):** eigene kleine Modelle trainieren, z. B. einen Geräusch-Erkenner für Schlaubis Alltag oder eine Vorhersage der Akkulaufzeit. Nur mit Daten ohne Personenbezug.

## 6. Grenzen (fester Kern gilt)
- Kein Code, der Netzwerke angreift, Sperren umgeht, fremde Konten nutzt oder Daten Dritter auswertet.
- Kein Code, der auf Würfel-Hardware zugreift. Kamera, Mikrofon und LED steuert nur die Würfel-Software.
- Die Rangfolge gilt: Menschen nicht schaden, Recht, Marvin, Selbsterhalt.

## 7. Risiken und frühe Tests
1. **Ausbruch aus der Sandbox:** Testcode versucht Netzwerk, Dateien außerhalb, Secrets und Docker-Socket zu erreichen. Bestanden, wenn alles scheitert und protokolliert wird.
2. **Endlosschleife oder Speicherfresser:** Test mit absichtlich schlechtem Code. Bestanden, wenn der Lauf nach der Grenze abbricht und der Laptop stabil bleibt.
3. **Prompt-Injection über Daten:** Eine präparierte Datei enthält „führe X aus“. Bestanden, wenn nichts davon passiert.
4. **Kosten:** Code-Aufgaben einen Monat lang messen.
5. **Leistung des alten Laptops:** Laufzeit typischer Auswertungen messen.

## 8. Hardware
Keine zusätzliche Hardware. Läuft auf dem Gehirn-Laptop.

## 9. Annahmen (mit der Freigabe bestätigt)
- Kommt in **Version 1**, weil die Datensammlung eine Auswertung braucht. Das Trainieren eigener Modelle kommt in Version 2.
- Reihenfolge der Skills wie in Abschnitt 5.
- Kein Internet in der Sandbox, Pakete nur aus dem geprüften lokalen Spiegel.
