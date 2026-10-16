# Design Data Lakehouse – Version 1

Stand 16.10.2026. **Freigegeben von Marvin am 16.10.2026** („Selbst erkennen. Alles freigegeben“), einschließlich aller Annahmen. Anlass: Marvin findet die Lakehouse-Idee aus dem Gemini-Brainstorming gut, weil mit der Zeit viele unstrukturierte Daten anfallen, die schnell abrufbar sein sollen. Spiegel der Notion-Seite „Design Data Lakehouse“. Bauplan: `docs/bauplan-lakehouse-v1.md`.

## 1. Zweck
Alle Daten von Schlaubi an einem Ort auf dem Gehirn-Laptop: Messwerte, Gespräche, Wissen und Dokumente. Was gerade gebraucht wird, ist sofort da, egal wie alt es ist. Was lange ruht, wandert ins Langzeitgedächtnis, geht aber nie verloren.

## 2. Marvins Entscheidungen (16.10.2026)
- **Mit Vektor-Datenbank.**
- **Schnell nach Bedarf, nicht nach Alter:** Jedes Thema soll schnell abrufbar sein, sobald es behandelt wird. Themenbereiche und Wissenspakete liegen je nach Bedarf im schnellen Speicher oder im Archiv.
- **Schnell sein müssen:** Abstandssensor, Fragen zu einem laufenden Projekt, Reaktion auf Sprache, Tagesparameter und was Claude sonst für wichtig hält (Abschnitt 5).
- **Laufende Projekte** sind die, an denen Marvin gerade mit Schlaubi arbeitet. **Schlaubi erkennt sie selbst.**
- **Länger nicht genutzte Pakete kommen ins Langzeitgedächtnis.**
- Alle Annahmen in diesem Dokument sind mit freigegeben.

## 3. Nicht-Ziele
- Keine Cloud, kein Cloud-Archiv, kein Hugging Face für Rohdaten (Entscheidung 13.10.2026).
- Notion bleibt Projektgedächtnis und Übersicht, kein Datenspeicher (die API schafft im Schnitt etwa 3 Anfragen pro Sekunde).
- Kein Delta Lake und kein Iceberg: Ihre Stärken (mehrere Rechner, Objektspeicher, viele Schreiber) brauchen wir auf einem Laptop mit einem Schreiber nicht.
- Kein freies SQL durch das Sprachmodell (Last, Prompt-Injection). Schlaubi nutzt feste Abfragen als Werkzeuge.
- Der Abstandssensor hängt nicht an der Datenbank (Abschnitt 6).

## 4. Drei Speicherstufen nach Bedarf
Passend zu den Stufen im Memory Core (`memory/SYSTEM_PROMPT.md`):

| Stufe | Inhalt | Ort | Ziel (Annahme) |
|---|---|---|---|
| **Sofort** (L1 Arbeitsgedächtnis) | Tagesparameter, letzte Gespräche, aktive Wissenspakete, Merk-Liste, Budget-Stand | Arbeitsspeicher des Gehirn-Dienstes | unter 10 ms |
| **Langzeit** (L3 semantisch) | alle Wissenspakete, auch ruhende; Vektor-Index und Volltext über alles Wissen | SQLite mit sqlite-vec und FTS5 auf der SSD, später LanceDB zum Vergleich | unter 100 ms |
| **Archiv** (L2/L5) | alte Messreihen und Rohtexte, Dokument-Originale | Parquet-Dateien und Ablage `rohdaten/` | Sekunden sind in Ordnung |

- Der ganze Vektor-Index bleibt immer durchsuchbar. Bei 100.000 Textabschnitten sind das etwa 150 MB (Schätzung, 384 Dimensionen). „Ins Langzeitgedächtnis“ heißt also: nicht mehr vorgeladen und nicht mehr im Prompt, aber jederzeit wieder auffindbar.
- Messwerte: Die letzten 3 Monate bleiben in SQLite, ältere abgeschlossene Monate wandern nachts ins Parquet-Archiv (Annahme). Nichts wird gelöscht, nur verschoben, mit Prüfsumme vor und nach dem Umzug.

## 5. Was sofort da sein muss (Stufe „Sofort“)
- **Tagesparameter:** Zustand (Tageszeit, Ort, Akku, Verbindung, Gespräch; gebaut in `brain/context.py`), die heutigen Messwerte (Temperatur, Luftfeuchte, Druck, Licht, Lautstärke, Anwesenheit aus dem Abstandssensor), „heute anders als sonst“ (gebaut in `brain/patterns.py`), Kühlungs-Lage.
- **Letzte Gespräche:** die Gespräche der letzten Tage als Kurzfassung (Annahme: 3 Tage).
- **Aktive Wissenspakete:** höchstens 5 gleichzeitig (Annahme), sonst wird der Kontext für das Modell zu groß und teuer.
- **Merk-Liste** („merken“) und **Budget-Stand** (für Sparmodus-Entscheidungen).
- Vorwärmen: Morgens und beim Start baut Schlaubi die Tagesparameter neu auf und lädt die laufenden Projekte.

## 6. Abstandssensor
Er reagiert direkt auf dem Würfel in Millisekunden (Anwesenheit, Gesten, Not-Abstand) und braucht das Gehirn dafür nicht. Ins Lakehouse wandern nur Ereignisse („jemand kam näher“, „Würfel verlassen“) und daraus berechnete Werte für die Tagesparameter.

## 7. Wissenspakete
Ein Wissenspaket ist ein Thema, z. B. „Kühlung“, „Projekt Würfel-Gehäuse“ oder ein Interessengebiet von Marvin. Es enthält:
- Name, Kurzfassung (wenige Sätze), Kernfakten, offene Fragen
- Textabschnitte mit Vektoren und Quellen (Gespräche, Recherchen, Dokumente)
- Status: **aktiv** (Stufe „Sofort“), **ruhend** (Langzeit), dazu Merker **laufendes Projekt**
- Zeitpunkt der letzten Nutzung, `pii`, `teilbar`, Herkunft

**Lebenslauf:**
1. **Hochholen:** Erkennt Schlaubi das Thema in einer Frage (Vektor-Ähnlichkeit der Frage zur Kurzfassung des Pakets, dazu Wörter aus dem Volltext), holt er das Paket nach oben. Sind schon 5 aktiv, rutscht das am längsten nicht genutzte zurück.
2. **Zurück ins Langzeitgedächtnis:** nach 30 Tagen ohne Nutzung (Annahme). Dabei schreibt Schlaubi die Kurzfassung neu, mit dem günstigen Modell.
3. **Neues Paket:** Kehrt ein Thema wieder, das noch kein Paket hat, legt Schlaubi eines an.

## 8. Laufende Projekte selbst erkennen
- Ein Thema gilt als **laufendes Projekt**, wenn Marvin mit Schlaubi daran arbeitet: Es kommt in mindestens 3 Gesprächen innerhalb von 7 Tagen vor und es geht um Arbeit daran (Aufgaben, Entscheidungen, Bauteile, Code, Pläne), nicht nur um Plaudern (Annahme). Die Einordnung macht das günstige Modell nach festen Fragen, mit Begründung im Event-Log.
- Ein laufendes Projekt bleibt in der Stufe „Sofort“, solange daran gearbeitet wird. Nach 30 Tagen ohne Arbeit daran endet der Merker und das Paket folgt den normalen Regeln.
- **Offen gesagt:** Wird etwas zum laufenden Projekt oder endet es, sagt Schlaubi das einmal kurz („Ich führe die Gehäuse-Sache jetzt als Projekt.“). Marvin kann widersprechen, umbenennen oder Pakete zusammenlegen.
- Fragen zum laufenden Projekt beantwortet Schlaubi aus dem aktiven Paket, ohne erst suchen zu müssen.

## 9. Schnelle Reaktion auf Sprache
- Die Datenbank bremst nicht: Die Suche braucht Millisekunden. Die Zeit geht in Spracherkennung (whisper.cpp) und Modell-Antwort (je etwa 1 s, Schätzung).
- **Prompt-Cache:** Kern, Profil und die aktiven Wissenspakete stehen vorne im Prompt und werden über den Prompt-Cache der API wiederverwendet. Das macht die Antwort schneller und billiger. Die Tagesparameter und die Frage kommen danach. Cache-Regeln (Mindestlänge, Haltezeit, Preise) vor dem Bau in der aktuellen API-Doku nachlesen.
- Eine kurze erste Reaktion darf starten, bevor die ganze Antwort fertig ist (Streaming zur Sprachausgabe).
- Messlatte (Annahme): zwischen Ende der Frage und erstem hörbaren Wort unter 2 Sekunden.

## 10. Katalog und Ablage
- **Katalog** (kleine SQLite-Tabelle): Datensatz, Ort, Format, Schema-Version, Zeitraum, Anzahl, Prüfsumme, `pii`, Aufbewahrungsfrist. Das Manifest des Data Lake ist der erste Eintrag, jedes Wissenspaket ein weiterer.
- **Dokument-Ablage** `rohdaten/dokumente/JJJJ/MM/`: Originaldatei mit Metadaten (Prüfsumme, Quelle, Abrufzeit, `pii`, Lizenz bzw. robots.txt-Status). Der Text daraus geht in Abschnitte eines Wissenspakets.
- Was zuerst hineinkommt: Gespräche mit Marvin (als Wissen verdichtet), Recherche-Ergebnisse, Dokumente, die Marvin gibt, und die Ereignisse des Würfels. Fotos später.

## 11. Abfragen
- **DuckDB** als lokale Abfrage-Maschine für Parquet (liest und schreibt Parquet ohne weitere Pakete).
- SQLite-Daten gibt der Code über Pythons eingebautes `sqlite3` an DuckDB weiter. Die SQLite-Erweiterung von DuckDB würde sonst zur Laufzeit aus dem Netz geladen.
- **Feste Einstellungen:** `autoinstall_known_extensions=false`, `autoload_known_extensions=false`, `allow_community_extensions=false`, `lock_configuration=true`, `threads=2`, `memory_limit` etwa 2 GB, Auslagerungsordner auf der verschlüsselten Platte.
- **Für Schlaubi:** feste Werkzeuge, z. B. „suche in meinem Wissen“ (Volltext plus Vektor), „was weiß ich zu Projekt X“ (aktives Paket), „werte Kanal X über Zeitraum Y aus“ (DuckDB). Die Code-Sandbox (Design Code-Skills) darf das Archiv nur lesen.

## 12. Datenschutz und Sicherheit
- Alles bleibt auf dem Laptop, verschlüsselte Festplatte (LUKS). Parquet- und Lance-Dateien sind selbst nicht verschlüsselt.
- `pii` geht durch alle Stufen mit, auch im Archiv, in der Suche und in den Wissenspaketen. Ein Paket mit `pii` geht nie an Gäste (Version 2).
- **An die API** gehen nur die aktiven Pakete und Tagesparameter, die für die Frage nötig sind, nie das ganze Gedächtnis.
- **Löschwunsch:** Parquet ist unveränderlich. Löschen heißt neue Datei ohne den Datensatz schreiben und die alte entfernen. In LanceDB löschen und alte Versionen sofort aufräumen. Beides nur mit Marvins Freigabe, wie im Gedächtnis-Kern.
- Fristen und Merk-Schutz aus Design Gehirn gelten unverändert. „Ins Langzeitgedächtnis“ ist keine Löschung.
- Webseiten nur mit Bot-Kennung und robots.txt (fester Kern).
- Kein Paket darf zur Laufzeit ins Netz. Das wird mit einem Testlauf ohne Netzwerk (`unshare -n`) belegt.

## 13. Bausteine (recherchiert 16.10.2026, vor Nutzung nach Checkliste prüfen)
- **sqlite-vec mit FTS5** und **fastembed** (Bauplan Gehirn 10.3): erste Vektor-Datenbank, schon entschieden am 13.10.2026.
- **DuckDB 1.5.6** (28.09.2026, MIT): Wheel 21,6 MB, keine Pflicht-Abhängigkeiten. Parquet, JSON und ICU sind fest eingebaut. Keine Telemetrie dokumentiert und keine gefunden, Beleg per Testlauf ohne Netz.
- **LanceDB 0.39.0** (17.09.2026, Apache-2.0): Wheel 71 MB, zieht pyarrow, numpy, pydantic, tqdm und lance-namespace mit. Keine Telemetrie mehr (bis 0.6.7 gab es PostHog). Eingebaute Einbettungs-Modelle und Reranker nicht nutzen, sie laden aus dem Netz. **Braucht AVX2**, sonst `lancedb-compat` 0.38.0. Prüfen beim Laptop-Steckbrief.
- **pyarrow 25.0.1** (10.08.2026, Apache-2.0): kommt mit LanceDB. 26.0.0 ist jünger als 14 Tage.
- **Speicher:** DuckDB will mindestens 125 MB pro Thread. Bei 8 GB RAM reichen 2 Threads mit 2 GB Grenze. Die Stufe „Sofort“ braucht wenige MB.

## 14. Risiken und frühe Tests
- **Falsches Thema erkannt:** Das falsche Paket wird hochgeholt. Test mit Prüffragen, die zwei ähnliche Themen trennen müssen. Kostet nur Kontext, nichts geht verloren.
- **Plaudern wird zum Projekt:** Test mit Gesprächen, die nur plaudern.
- **Alter Prozessor ohne AVX2:** LanceDB stürzt ab. Steckbrief, sonst compat-Variante oder bei sqlite-vec bleiben.
- **Zu wenig RAM:** Test mit einem Jahr erfundener Messwerte, Speicher und Zeit messen.
- **Heimliches Netz:** Testlauf ohne Netzwerk für DuckDB und LanceDB.
- **Archiv-Umzug verliert Daten:** Prüfsumme und Zeilenzahl vor und nach dem Umzug, erst dann in SQLite als archiviert markieren.
- **Suche zu langsam oder schlecht:** Messung mit 100.000 Abschnitten. Vergleich der Treffer mit sqlite-vec/FTS5 und LanceDB.

## 15. Annahmen (mit freigegeben 16.10.2026)
Sofort unter 10 ms, Langzeit unter 100 ms; höchstens 5 aktive Pakete; 30 Tage bis ins Langzeitgedächtnis (auch für das Ende eines laufenden Projekts); laufendes Projekt ab 3 Gesprächen in 7 Tagen mit Arbeit daran; letzte Gespräche 3 Tage; Messwerte 3 Monate in SQLite; erste hörbare Reaktion unter 2 Sekunden. Alle Werte stehen später in der Config und lassen sich ändern.

## 16. Noch offen (klärt der Bau, keine Entscheidung nötig)
- Ob LanceDB langfristig sqlite-vec ersetzt, entscheidet der Vergleich an denselben Daten (Bauplan Phase 6).
- Laptop-Eignung (RAM, AVX2) steht noch aus (Gehirn Phase 0).

## Quellen
- DuckDB Erweiterungen und Sicherheit: https://duckdb.org/docs/current/operations_manual/securing_duckdb/securing_extensions.html
- DuckDB SQLite-Erweiterung: https://duckdb.org/docs/current/core_extensions/sqlite.html
- DuckDB Python-Build (eingebaute Erweiterungen): https://github.com/duckdb/duckdb-python/blob/v1.5.6/pyproject.toml
- DuckDB Leistung und Speicher: https://duckdb.org/docs/current/guides/performance/environment.html
- LanceDB alte Telemetrie (bis 0.6.7): https://github.com/lancedb/lancedb/blob/python-v0.5.0/python/lancedb/utils/events.py
- LanceDB Volltextsuche: https://docs.lancedb.com/search/full-text-search
- LanceDB CPU-Ziel: https://github.com/lancedb/lancedb/blob/v0.39.0/.cargo/config.toml
- Lance Blobs: https://lance.org/guide/blob/
- Iceberg-Kataloge: https://py.iceberg.apache.org/configuration/
- Versionen: PyPI JSON-API (https://pypi.org/pypi/<paket>/json), abgerufen 16.10.2026
