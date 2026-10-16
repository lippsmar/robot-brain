# Bauplan Data Lakehouse – Version 1

Stand 16.10.2026. **Bestätigt von Marvin am 16.10.2026** („Alles bestätigt“). Design: `docs/design-lakehouse.md` (freigegeben 16.10.2026). Spiegel der Notion-Seite „Bauplan Data Lakehouse“.

## Kopf
- **Ziel:** Was Schlaubi gerade braucht, liegt sofort bereit (Tagesparameter, laufende Projekte, aktive Themen), alles andere bleibt im Langzeitgedächtnis und im Archiv auffindbar.
- **Architektur:** drei Stufen nach Bedarf. „Sofort“ im Arbeitsspeicher, „Langzeit“ in SQLite mit Volltext und Vektoren, „Archiv“ in Parquet. Wissenspakete wandern je nach Nutzung zwischen „Sofort“ und „Langzeit“. Laufende Projekte erkennt Schlaubi selbst.
- **Technik:** Python 3.13 unter `brain/`, SQLite (STRICT, nur anhängen wie Data Lake und Gedächtnis-Kern), später sqlite-vec, fastembed, DuckDB, LanceDB nach Paketprüfung.
- **Baut auf:** `brain/memory.py` (Gedächtnis-Kern), `brain/datalake.py`, `brain/context.py` (Zustand), `brain/patterns.py` (Muster), `brain/cooling.py`, `brain/budget.py`. Bauplan Gehirn Phase 10 (10.1 LanceDB prüfen, 10.3 Indizes) wird hier konkret.
- **Globale Vorgaben:**
  - Erst Test, dann Code. Pro Phase ein Commit und ein Notion-Eintrag, Abschluss mit Skill `paket-abschluss`.
  - Pakete: feste Version, mindestens 14 Tage alt, Prüfsummen, vor Nutzung nach `skills/INDEX.md` prüfen.
  - Kein Netz zur Laufzeit, belegt mit Testlauf ohne Netzwerk.
  - Alle Zahlen aus Design Abschnitt 15 kommen in die Config.
  - `pii` und `teilbar` an jedem Datensatz.

## Phase 1 – Katalog, Wissenspakete, Stufe „Sofort“ (ohne neue Pakete, sofort machbar) ✅ 16.10.2026
Umgesetzt in `brain/katalog.py`, `brain/wissen.py`, `brain/sofort.py`, `brain/ablage.py`. Noch offen aus 1.4: die letzten Gespräche (kommen mit der Gesprächs-Ablage, Bauplan Gehirn 10.5).
**1.1 Katalog:** SQLite-Tabelle mit Datensatz, Ort, Format, Schema-Version, Zeitraum, Anzahl, Prüfsumme, `pii`, Frist.
- Test: Das Manifest des Data Lake erscheint als Eintrag. Eine geänderte Prüfsumme fällt auf.

**1.2 Wissenspakete:** Pakete (Name, Kurzfassung, Kernfakten, offene Fragen, Status aktiv/ruhend, Merker laufendes Projekt, letzte Nutzung, `pii`, `teilbar`, Herkunft) und Abschnitte mit Quelle. Volltextsuche über Abschnitte wie im Gedächtnis-Kern (Wörter und Wortteile, deutsche Schreibweisen).
- Test: Paket anlegen, Abschnitt finden, `pii` bleibt am Treffer.

**1.3 Lebenslauf:** Hochholen bei Nutzung, höchstens 5 aktiv (das am längsten nicht genutzte rutscht zurück), nach 30 Tagen ohne Nutzung zurück ins Langzeitgedächtnis. Die neue Kurzfassung beim Zurückwandern kommt über eine Schnittstelle. Bis der API-Key da ist, steht dort ein Platzhalter, der die alte Kurzfassung behält.
- Test mit fester Uhr: 6. Paket verdrängt das älteste. Tag 31 ohne Nutzung → ruhend. Laufendes Projekt bleibt aktiv. Nichts wird gelöscht.

**1.4 Stufe „Sofort“:** ein Bündel aus Zustand, heutigen Messwerten, „heute anders als sonst“, Kühlungs-Lage, Budget-Stand, Merk-Liste, letzten Gesprächen (3 Tage) und aktiven Paketen. Aufbau beim Start und morgens, danach bei jeder Änderung nachgeführt.
- Test: Bündel enthält alles, `pii`-Teile sind markiert. Messung: Abruf unter 10 ms.

**1.5 Dokument-Ablage:** `rohdaten/dokumente/JJJJ/MM/` mit Original und Metadaten (Prüfsumme, Quelle, Abrufzeit, `pii`, Lizenz bzw. robots.txt-Status), Eintrag im Katalog, Text als Abschnitte in ein Paket.
- Test: doppelte Datei wird erkannt, Prüfsumme stimmt, Laufzeitdaten liegen nie im Repo.

**→ Zwischenstand:** Schlaubi führt Themen als Pakete, hält die wichtigsten bereit und findet alles per Volltext.

## Phase 2 – Vektoren und Themen-Erkennung
**2.1 Pakete prüfen:** sqlite-vec und fastembed nach Checkliste, Einbettungs-Modell als ONNX-Datei lokal, mit Prüfsumme (Bauplan Gehirn 10.1/10.3).
- Test: Lauf ohne Netzwerk erzeugt Vektoren.

**2.2 Hybridsuche:** Volltext plus Vektor über alle Pakete, auch ruhende. Ein Befehl baut den Index komplett neu auf.
- Test: Neuaufbau ergibt gleiche Treffer. Messung mit 100.000 erfundenen Abschnitten: unter 100 ms.

**2.3 Themen-Erkennung:** Frage → passendes Paket (Ähnlichkeit zur Kurzfassung plus Wörter), mit Schwelle. Unter der Schwelle wird kein Paket hochgeholt.
- Test: Prüffragen, die zwei ähnliche Themen trennen müssen (z. B. „Kühlung Würfel“ gegen „Kühlschrank“), und Fragen ohne Thema.

**→ Zwischenstand:** Ein Thema kommt nach oben, sobald es angesprochen wird.

## Phase 3 – Laufende Projekte selbst erkennen
**3.1 Erkennen:** Zähler pro Paket (mindestens 3 Gespräche in 7 Tagen) und Einordnung „Arbeit daran“ gegen „Plaudern“ durch das günstige Modell nach festen Fragen, Begründung im Event-Log. Bis der API-Key da ist, wird der Bewerter in Tests ersetzt.
- Test: Arbeitsgespräche ergeben ein Projekt, reines Plaudern nicht, 2 Gespräche reichen nicht.

**3.2 Offen sagen:** Schlaubi sagt einmal kurz, dass er etwas als Projekt führt oder ein Projekt endet. Marvin kann widersprechen, umbenennen und Pakete zusammenlegen.
- Test: Widerspruch nimmt den Merker zurück und wird sich gemerkt. Zusammenlegen verliert keine Abschnitte.

**3.3 Ende:** nach 30 Tagen ohne Arbeit daran.
- Test mit fester Uhr.

## Phase 4 – Prompt-Aufbau und Cache (braucht den API-Key)
**4.1 Reihenfolge:** Kern, Profil, aktive Pakete vorne (Prompt-Cache), danach Tagesparameter und Frage. Cache-Regeln vorher in der aktuellen API-Doku nachlesen.
- Test: Nur aktive Pakete und nötige Tagesparameter gehen raus, nie das ganze Gedächtnis.

**4.2 Messen:** Zeit vom Ende der Frage bis zum ersten hörbaren Wort beim Testweg mit dem Handy (Bauplan Gehirn 11.5–11.8), Ziel unter 2 Sekunden. Kosten pro Gespräch im Budget-Wächter mit und ohne Cache.

## Phase 5 – Archiv mit DuckDB und Parquet
**5.1 DuckDB 1.5.6 prüfen** nach Checkliste, feste Einstellungen aus Design Abschnitt 11.
- Test: Lauf ohne Netzwerk. Erweiterungen lassen sich nicht nachladen.

**5.2 Nächtlicher Umzug:** abgeschlossene Monate älter als 3 Monate aus SQLite nach Parquet, je Kanal und Monat.
- Test: Prüfsumme und Zeilenzahl vor und nach, erst dann als archiviert markiert. Abbruch in der Mitte verliert nichts.

**5.3 Feste Auswertungen:** „Kanal X über Zeitraum Y“ über SQLite und Parquet zusammen.
- Messung mit einem Jahr erfundener Messwerte: Monatsauswertung unter 2 Sekunden, Speicher unter 2 GB.

**5.4 Löschwunsch im Archiv:** neue Datei ohne den Datensatz, nur mit Marvins Freigabe, im Event-Log.

## Phase 6 – LanceDB im Vergleich (nach dem Laptop-Steckbrief mit AVX2)
**6.1** LanceDB 0.39.0 (oder `lancedb-compat` ohne AVX2) nach Checkliste prüfen, Lauf ohne Netzwerk.
**6.2** Befüllen aus derselben Quelle wie sqlite-vec.
**6.3** Vergleich an denselben Prüffragen: Treffer und Zeit. Ergebnis an Marvin. Ob LanceDB sqlite-vec ersetzt, entscheidet er.

## Phase 7 – Abstandssensor anbinden
**7.1** Der Würfel reagiert selbst in Millisekunden (Bauplan Körper Phase 9) und schickt nur Ereignisse („jemand kam näher“, „Würfel verlassen“).
**7.2** Ereignisse landen im Data Lake, Anwesenheit fließt in die Tagesparameter.
- Test beim Testweg mit dem Handy, danach mit dem echten Sensor.

## Reihenfolge
Phase 1 und 2 sowie 3 (ohne echtes Modell) und 5 gehen sofort in der Cloud-Sitzung. Phase 4 braucht den API-Key, Phase 6 den Laptop, Phase 7 den Würfel bzw. den Testweg.

## Selbstprüfung
- Jede Entscheidung aus Design Abschnitt 2 hat eine Aufgabe: Vektoren (2), schnell nach Bedarf (1.3, 1.4, 2.3), Abstandssensor (7), laufende Projekte selbst erkennen (3), Langzeitgedächtnis (1.3), Sprache schnell (4).
- Namen einheitlich: Wissenspaket, Stufe „Sofort“, Langzeit, Archiv, laufendes Projekt.
- Keine Platzhalter ohne Plan: Kurzfassung und Projekt-Bewerter bekommen ihr Modell mit dem API-Key (Phase 4), bis dahin Testersatz.
