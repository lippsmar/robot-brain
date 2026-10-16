# Design Data Lakehouse – Entwurf

Stand 16.10.2026. **Entwurf zur Klärung, nicht freigegeben.** Anlass: Marvin findet die Lakehouse-Idee aus dem Gemini-Brainstorming gut, weil mit der Zeit viele unstrukturierte Daten anfallen, die schnell abrufbar sein sollen. Spiegel der Notion-Seite „Design Data Lakehouse (Entwurf)“.

## 1. Zweck
Alle Daten von Schlaubi an einem Ort auf dem Gehirn-Laptop: strukturierte Messwerte und unstrukturierte Inhalte (Texte, Webseiten, Transkripte, später Bilder). Sie sollen über Jahre wachsen können und trotzdem schnell durchsuchbar und auswertbar bleiben.

## 2. Ziele
- **Ein Katalog:** Schlaubi weiß, welche Daten es gibt, wo sie liegen, aus welcher Quelle, wie alt, ob personenbezogen (`pii`) und wie lange sie bleiben.
- **Unstrukturiertes ablegen:** Dokumente, Recherche-Ergebnisse, Webseiten und Transkripte als Original plus durchsuchbaren Text.
- **Schnell finden:** Volltextsuche (Deutsch) und Ähnlichkeitssuche (Vektoren) kombiniert. Annahme als Messlatte: unter 1 Sekunde bei 100.000 Textabschnitten.
- **Schnell auswerten:** Auswertungen über Jahre von Messwerten. Annahme als Messlatte: eine Monatsauswertung unter 2 Sekunden.
- **Wachsen ohne Umbau:** frische Daten bleiben in SQLite (schnell beim Schreiben), ältere wandern in ein Archiv im Spaltenformat (schnell beim Auswerten).

## 3. Nicht-Ziele
- Keine Cloud, kein Cloud-Archiv, kein Hugging Face für Rohdaten (Entscheidung 13.10.2026).
- Notion bleibt Projektgedächtnis und Übersicht, kein Datenspeicher (die API schafft im Schnitt etwa 3 Anfragen pro Sekunde).
- Kein Delta Lake und kein Iceberg: Ihre Stärken (mehrere Rechner, Objektspeicher, viele Schreiber) brauchen wir auf einem Laptop mit einem Schreiber nicht.
- Kein freies SQL durch das Sprachmodell (Last, Prompt-Injection). Schlaubi nutzt feste Abfragen als Werkzeuge.

## 4. Aufbau in drei Zonen
1. **Eingang (roh, nur anhängen):**
   - bleibt wie gebaut: Data Lake für Messwerte (SQLite), Event-Log (JSONL), Gedächtnis-Kern (SQLite)
   - neu: Dokument-Ablage `rohdaten/dokumente/JJJJ/MM/` mit Originaldatei und Metadaten (Prüfsumme, Quelle, Abrufzeit, `pii`, Lizenz bzw. robots.txt-Status)
2. **Archiv (Spaltenformat Parquet):**
   - nachts wandern abgeschlossene Monate aus SQLite in Parquet-Dateien, aufgeteilt nach Kanal und Monat
   - SQLite behält nur die heißen Daten (Annahme: die letzten 3 Monate) und bleibt dadurch klein
   - nichts wird gelöscht, nur verschoben, mit Prüfsumme vor und nach dem Umzug
3. **Suchschicht für Unstrukturiertes (LanceDB):**
   - Textabschnitte mit Quelle, Zeit, `pii`, Volltext-Index (BM25 mit deutschem Wortstamm) und Vektoren aus fastembed
   - später auch Bilder als Blobs
   - passt zur Entscheidung vom 13.10.2026: LanceDB als Vergleich und Ersatz neben sqlite-vec, beide aus derselben Quelle befüllt

Dazu ein **Katalog** (kleine SQLite-Tabelle): Datensatz, Ort, Format, Schema-Version, Zeitraum, Anzahl, Prüfsumme, `pii`, Aufbewahrungsfrist. Das Manifest des Data Lake ist der erste Eintrag.

## 5. Abfragen
- **DuckDB** als lokale Abfrage-Maschine für Parquet (liest und schreibt Parquet ohne weitere Pakete).
- SQLite-Daten gibt der Code über Pythons eingebautes `sqlite3` an DuckDB weiter. Die SQLite-Erweiterung von DuckDB würde sonst zur Laufzeit aus dem Netz geladen.
- **Feste Einstellungen:**
  - `autoinstall_known_extensions=false`, `autoload_known_extensions=false`, `allow_community_extensions=false`
  - `lock_configuration=true`
  - `threads=2`, `memory_limit` etwa 2 GB
  - Auslagerungsordner auf der verschlüsselten Platte
- **Für Schlaubi:** wenige feste Werkzeuge, z. B. „suche in meinen Dokumenten“ (LanceDB, Volltext plus Vektor) und „werte Kanal X über Zeitraum Y aus“ (DuckDB). Die Code-Sandbox (Design Code-Skills) darf das Archiv nur lesen.

## 6. Datenschutz und Sicherheit
- Alles bleibt auf dem Laptop, verschlüsselte Festplatte (LUKS). Parquet- und Lance-Dateien sind selbst nicht verschlüsselt.
- `pii` geht durch alle Zonen mit, auch im Archiv und in der Suche.
- **Löschwunsch:** Parquet ist unveränderlich. Löschen heißt neue Datei ohne den Datensatz schreiben und die alte entfernen. In LanceDB löschen und alte Versionen sofort aufräumen (Standard wäre 7 Tage). Beides nur mit Marvins Freigabe, wie im Gedächtnis-Kern.
- Fristen und Merk-Schutz aus Design Gehirn gelten unverändert.
- Webseiten nur mit Bot-Kennung und robots.txt (fester Kern).
- Kein Paket darf zur Laufzeit ins Netz. Das wird mit einem Testlauf ohne Netzwerk (`unshare -n`) belegt.

## 7. Bausteine (recherchiert 16.10.2026, vor Nutzung nach Checkliste prüfen)
- **DuckDB 1.5.6** (28.09.2026, MIT): Wheel 21,6 MB, keine Pflicht-Abhängigkeiten. Parquet, JSON und ICU sind fest eingebaut. Keine Telemetrie dokumentiert und keine gefunden, Beleg per Testlauf ohne Netz. Optional eingebaute Verschlüsselung (AES-256-GCM).
- **LanceDB 0.39.0** (17.09.2026, Apache-2.0): Wheel 71 MB, entpackt etwa 176 MB. Zieht pyarrow, numpy, pydantic, tqdm und lance-namespace mit.
  - Telemetrie: In alten Versionen (bis 0.6.7) gab es Analyse-Daten an PostHog. In 0.39.0 gibt es sie nicht mehr, im Paket keine Spuren gefunden.
  - Nur eine OpenTelemetry-Brücke, die ohne eigenes Zutun nichts sendet.
  - Eingebaute Einbettungs-Modelle und Reranker nicht nutzen, sie laden aus dem Netz. Wir liefern die Vektoren selbst (fastembed).
- **pyarrow 25.0.1** (10.08.2026, Apache-2.0): 50 MB, kommt mit LanceDB. Die neueste Version 26.0.0 ist jünger als 14 Tage.
- **Wichtig für den Laptop:** Die normalen LanceDB-Pakete brauchen einen Prozessor mit AVX2 (Haswell, ab etwa 2013). Sonst gibt es die Variante `lancedb-compat`, derzeit nutzbar in 0.38.0. Prüfen mit `grep -o avx2 /proc/cpuinfo` beim Steckbrief (Gehirn Phase 0).
- **Speicher:** DuckDB will mindestens 125 MB pro Thread, gut sind 1–4 GB. Bei 8 GB RAM reichen 2 Threads mit 2 GB Grenze. Platz für Programme etwa 400 MB.

## 8. Stufen
1. **Ohne neue Pakete:** Katalog und Dokument-Ablage (nur Python-Bordmittel). Sofort nutzbar.
2. **DuckDB und Parquet-Archiv:** nach Paketprüfung, Umzug alter Monate, feste Auswertungen.
3. **LanceDB-Suche:** nach Paketprüfung und AVX2-Check auf dem Laptop, Vergleich mit sqlite-vec/FTS5 an denselben Daten.

## 9. Risiken und frühe Tests
- **Alter Prozessor ohne AVX2:** LanceDB stürzt ab. Test: Steckbrief, sonst compat-Variante oder bei sqlite-vec bleiben.
- **Zu wenig RAM:** Test mit einem Jahr erfundener Messwerte, Speicher und Zeit messen.
- **Heimliches Netz:** Testlauf ohne Netzwerk für DuckDB und LanceDB.
- **Archiv-Umzug verliert Daten:** Prüfsumme und Zeilenzahl vor und nach dem Umzug, erst dann in SQLite als archiviert markieren.
- **Suche zu langsam oder schlecht:** Messung mit 100.000 Abschnitten. Vergleich der Treffer mit sqlite-vec/FTS5.

## 10. Offene Punkte (in Klärung)
- Welche unstrukturierten Daten zuerst (Recherchen und Webseiten, eigene Dokumente und PDFs, Transkripte von Marvins Sprache, später Fotos)?
- Grenze heiß/kalt: 3 Monate in SQLite (Annahme)?
- Soll LanceDB langfristig sqlite-vec ersetzen, oder bleiben beide?
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
