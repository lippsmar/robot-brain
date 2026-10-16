# brain – Code für Schlaubis Gehirn

Stand 16.10.2026. Der Code entsteht nach `docs/bauplan-gehirn-v1.md`, `docs/bauplan-charakter-v1.md`, `docs/bauplan-daten-v1.md` und `docs/bauplan-lakehouse-v1.md`, testgetrieben, mit Python 3.13 (wie Debian 13 auf dem Gehirn-Laptop).

## Bausteine

| Datei | Zweck | Bauplan |
|---|---|---|
| `eventlog.py` | Event-Log: eine JSONL-Datei pro Tag (UTC), fortlaufende Nummer, Hash-Kette gegen unbemerkte Änderungen, Anker (`head()`) gegen Kürzen und Neuschreiben, Prüfung gegen `schemas/event.schema.json` (seit 16.10.2026 Version 1.2, alte Einträge mit 1.1 bleiben gültig), Secrets werden abgewiesen, Dateien nur für Schlaubis Konto lesbar | Grenzen und Regeln: „Jede Aktion wird protokolliert“ |
| `budget.py` | Budget-Wächter: Kosten aus den Nutzungsdaten der API, Grenzen in Euro, Töpfe Gesamt, Recherche und Selbstoptimierung, Stufen Warnung, Sparmodus, Stopp. Stoppt vor dem Console-Limit, lässt Gesprächen immer das Minimum, weist Modelle ohne Preise ab | Gehirn 7.3 |
| `memory.py` | Gedächtnis-Kern: SQLite (STRICT-Tabellen, nur anhängen, auch gegen `INSERT OR REPLACE` gesichert), Herkunft, `pii`, `teilbar`, Merk-Schutz, Archiv statt Löschen, Löschen nur mit Marvins Freigabe (Inhalt wird überschrieben), Volltextsuche nach Wörtern (ß/ss, ä/ae gleichwertig) und Wortteilen, Eingang für Einträge anderer Hosts | Gehirn 10.2, 10.2a |
| `images.py` | Bilder vor dem Versand an Claude bereinigen: JPEG und PNG ohne EXIF, Ort, XMP, ICC, Kommentare, Vorschaubilder und Daten hinter dem Bildende. Erlaubnisliste, Pixel bleiben Byte für Byte gleich, andere Formate und kaputte Dateien werden abgewiesen. Die Drehung (EXIF-Orientierung) wird vorher ausgelesen und mitgegeben | Gehirn 11.2 |
| `datalake.py` | Data Lake für Messwerte und Geräuschklassen vom Würfel: SQLite (STRICT, nur anhängen), doppelt gesendete Pakete werden erkannt, Lücken über fortlaufende Nummern, Qualität ok/fehler/unplausibel, Orte über benannte WLANs (sonst „unterwegs“), Beschriftungen von Marvin mit Vermerk, Stundenwerte, Manifest mit `pii`, Index auf Zeit | Daten 6.1, 7, 8.2 |
| `cooling.py` | Kühlung: Zuluft, Abluft, Chip und Modem der letzten Stunde, Abgleich der Sensoren, Trend, Warnung ab 70 °C oder bei Drosselung, einmal pro heißer Phase, mit Laune-Faktor. Druck-Abgleich der beiden Klimasensoren (Mittel über 10 Minuten, Toleranz 1 hPa, Entwarnung erst unter 0,75 hPa) | Daten 3, 3.3, Körper 8a.4 |
| `context.py` | Zustand für das Gespräch: Tageszeit, Ort, Akku, Verbindung, ob ein Gespräch läuft. Nur frische Daten (5 Minuten), sonst „unbekannt“. Ein bekannter Ort ist persönlich (`pii`) | Daten 6.2 |
| `patterns.py` | Muster aus vier Wochen: wann Marvin wo ist, wo er öfter kurz ist (z. B. Café, ab 3 Besuchstagen), wie laut und warm es dort ist, wann der Akku knapp wird. Vergleich „heute lauter als sonst“ mit denselben Stunden am gleichen Tagestyp. Alles `pii`, lokal, auf Nachfrage gezeigt, löschbar (Sperrliste) und zurückholbar | Daten 9 |
| `katalog.py` | Katalog aller Datensätze im Lakehouse: Ort, Format, Zeitraum, Anzahl, Prüfsumme, `pii`, Frist. Jede Änderung ist eine neue Version, die neueste gilt. Übernimmt das Manifest des Data Lake (nur geänderte Kanäle). Prüfung ohne Prüfsumme ist ein Fehler, nie ein stilles „ok“ | Lakehouse 1.1 |
| `wissen.py` | Wissenspakete: Thema mit Kurzfassung und Abschnitten (die Abschnitte liegen im Gedächtnis-Kern, mit Tag des Pakets). Hochholen bei Nutzung, höchstens 5 aktiv, das am längsten ungenutzte rutscht zurück, laufende Projekte nie. Nach 30 Tagen ohne Nutzung ins Langzeitgedächtnis mit neuer Kurzfassung (Modell kommt mit dem API-Key), Projekt endet nach 30 Tagen ohne Arbeit. Gäste sehen nur teilbare Pakete ohne `pii`. Themenbaum mit Oberthemen ohne Kreise und Überblick. Alles als angehängte Ereignisse | Lakehouse 1.2, 1.3, Wissen 1.3 |
| `sofort.py` | Stufe „Sofort“: Zustand, heutige Messwerte, „heute anders als sonst“, Kühlung, aktive Pakete, Merk-Liste, Budget als Bündel im Arbeitsspeicher. Aufbau beim Start, dann Teil für Teil nachgeführt, eine kaputte Quelle stört die anderen nicht. Lesen dauert Mikrosekunden | Lakehouse 1.4 |
| `ablage.py` | Dokument-Ablage `dokumente/JJJJ/MM/` außerhalb des Repos: Original unter Prüfsumme, Metadaten daneben, Eintrag im Katalog, gleiches Dokument nur einmal. Text als Abschnitte in ein Wissenspaket, auch bei einem zweiten Paket oder nach einem Fehler genau das Fehlende | Lakehouse 1.5 |
| `aussagen.py` | Aussagen (Subjekt, Beziehung, Objekt) mit Belegen, Quellen-Stufe A–D, Vertrauen aus unabhängigen Belegen, gültig seit/bis. Status bestätigt, ersetzt (nichts wird gelöscht) und umstritten (wird beim Lesen berechnet: endet von selbst, Marvins Bestätigung gewinnt). Suche tolerant für Groß/klein, Umlaute, ß. Quelle entfernen nimmt ihre Belege weg, Aussagen ohne Beleg werden nicht mehr genannt | Wissen 1.1, 1.2 |
| `module.py` | Wissensmodule: Ordner mit `modul.yaml` und Markdown. Steckbrief und Prüfsummen geprüft, nur `.md` direkt im Ordner, keine Links. Wird ein Wissenspaket, neue Version archiviert die alte, geänderte Einstellung braucht eine neue Version. Abgebrochenes Einlesen lässt sich einfach wiederholen. Versteckte Anweisungen werden gemeldet, nie befolgt | Wissen 1.4 |
| `freie_quellen.py` | Kostenlose Recherche mit ehrlicher Bot-Kennung: Wikipedia-Artikel (normale Seiten, CC BY-SA 4.0) und Marginalia-Suche (CC-BY-NC-SA 4.0). robots.txt nach RFC 9309 bei jedem Schritt, auch nach Weiterleitungen. Nur https, Zeit- und Größenlimit, jeder Abruf im Event-Log | Wissen 1.5 |
| `_sqlite.py` | gemeinsames Öffnen der Lakehouse-Datenbanken (private Datei, WAL, Sicherheits-Pragmas) und Sperren gegen Ändern und Löschen | Lakehouse |
| `zahlen.py` | Zahlen in deutscher Schreibweise für Texte an Marvin | – |
| `schema.py` | kleine Prüfung gegen JSON-Schema (nur die Schlüsselwörter, die unsere Schemas nutzen) | – |
| `secrets_guard.py` | erkennt Secrets in Daten, bevor sie gespeichert werden (Schlüsselnamen auch in camelCase, bekannte Key-Formate, HTTP-Auth). Zahlen wie GPIO-Pins bleiben erlaubt | Arbeitsregeln |
| `character/kern.md`, `character/core.py` | fester Kern (Rangfolge und Regeln aus Design Charakter, Abschnitt 2) und Startschutz: Schlaubi startet nur, wenn der Kern genau dem letzten git-Stand entspricht, dem Dienst nicht gehört, nicht für Gruppe oder andere beschreibbar ist und kein Link ist | Charakter 1 |
| `character/profil.yaml`, `profil.schema.json`, `profile.py` | Startprofil (Persönlichkeit, Regler, Haltung, Laune-Faktoren, Entwicklung) mit Schema. Einträge, die den Kern berühren, werden abgewiesen | Charakter 2 |
| `character/prompt.py` | System-Prompt: Kern zuerst und vollständig, dann Rolle, Charakter, Zeit, Kanal, Laune mit Grund und Antwortlänge. Fester Teil getrennt vom wechselnden (Caching), Grenze 6000 Zeichen | Charakter 3 |
| `character/mood.py` | Laune-Rechner: Stimmung, Energie, Gereiztheit, abklingende Faktoren, Begründung, Dämpfung bei ernsten Themen, jede Änderung im Event-Log | Charakter 4 |
| `character/pruefragen.yaml`, `exam.py` | 44 Prüffragen (21 Kern-Fragen, davon Grenzfälle: Vermutung kennzeichnen statt erfinden) mit Regelprüfung und Bewertungs-Prompt für Haiku. Antwortseite sieht nur Frage, Sprecher und Kanal, Bewerter ist eine getrennte, frische Anfrage. Grenzfälle zählen nur mit Bewerter als bestanden. Bestanden: Kern 100 %, Rest mindestens 90 % | Charakter 5 |
| `character/live_profile.py` | Laufzeit-Profil im eigenen git-Repo im Datenordner: Marvin ändert Regler im Gespräch (Vorschlag in einem Satz, Übernahme nur nach seinem Ja in seinem Telegram-Chat, auch bei Sprache), Kern-Änderungen abgewiesen mit Hinweis auf `kern.md`, Webseiten, Mails und Dritte ändern nichts, Rückgängig Schritt für Schritt, Auskunft „Was hat sich an dir verändert?“. Entwicklung von selbst: nur bewegliche Regler, im Spielraum; im Gespräch höchstens ein Schritt pro Tag und zwei pro Regler und Woche, dazu ein eigener Schritt des Wochenlaufs; nach durchgefallenem Selbsttest werden alle Schritte der letzten 7 Tage zurückgenommen, mit Alarm; nur ein Schreiber zur Zeit (Sperre) | Charakter 10, 11 |
| `character/_git.py` | ein abgesicherter git-Aufruf für Kern-Prüfung und Laufzeit-Profil: feste Argumente, saubere Umgebung ohne fremde Konfiguration, keine Hooks | Charakter 1, 10 |
| `character/safe_yaml.py` | strenges YAML-Laden: nur SafeLoader, keine doppelten Schlüssel, keine Aliase, Größen- und Tiefengrenze | Charakter 2, 5 |
| `config/prices.toml` | Preise der Claude-API mit Quelle und Prüfdatum | Gehirn 7.2 |
| `config/budget.toml` | Grenzen in Euro, Wechselkurs mit Datum, Schwellen | Gehirn 7.1, 7.3 |

Vektorsuche (sqlite-vec, fastembed, LanceDB), Fristen-Lauf, Themenseiten und Quellen-Bewertung folgen in eigenen Schritten (Bauplan Gehirn 10.1, 10.3 bis 10.6).

### Laufzeit-Profil liegt nicht im Repo
`character/profil.yaml` ist das Startprofil. Ändert Marvin den Charakter im Gespräch (Bauplan Charakter Phase 10), ist das Laufzeit-Datum und liegt nach der Code-Regel nie im Repo: Das laufende Profil bekommt ein eigenes git-Repo in Schlaubis Datenordner, dem Dienst gehörend. Das Code-Repo mit `kern.md` bleibt für den Dienst nur lesbar. Deshalb darf der Startschutz verlangen, dass der `.git`-Ordner des Code-Repos dem Dienst nicht gehört (Befund 13 der Code-Prüfung vom 16.10.2026).

## Tests

```sh
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r brain/requirements.txt -r brain/requirements-dev.txt
.venv/bin/python -m pytest                      # alle Tests
.venv/bin/ruff check brain                      # Code-Prüfung
.venv/bin/mypy                                  # Typprüfung
.venv/bin/python -m coverage run -m pytest && .venv/bin/python -m coverage report
.venv/bin/python tools/dev/mutation_check.py    # erkennen die Tests eingebaute Fehler? (parallel, ein Lauf pro CPU-Kern)
.venv/bin/python tools/dev/mutation_check.py --geaendert   # schnell: nur Dateien, die seit dem letzten Commit geändert sind
# danach in Claude Code: /code-review <Bereich> high
```

`brain/requirements.txt` enthält die Pakete für den Betrieb (seit 16.10.2026 PyYAML), `brain/requirements-dev.txt` die Werkzeuge für die Entwicklung. Die Testumgebung liegt in `.venv` im Repo (nicht eingecheckt), damit auch Prüf-Agenten sie finden.

Stand 16.10.2026: 846 Tests grün, mypy ohne Befund, alle 354 eingebauten Fehler werden erkannt (Wissen Stufe 1: Code-Prüfung 10 Befunde, 9 behoben, einer zurückgestellt: Überblick fragt pro Paket einzeln, reicht für Version 1. Lakehouse Phase 1: 10 Befunde, 9 behoben, einer begründet zurückgestellt). `mutation_check.py` prüft vorher, ob die Tests ohne eingebauten Fehler grün sind. Die Code-Prüfung (`/code-review`) vom 16.10.2026 fand 15 Befunde: 14 sind behoben und mit Tests abgesichert, einer (13) ist durch das getrennte Laufzeit-Profil gelöst. Die zweite Prüfung (Zustand und Muster) fand 10 Befunde, alle behoben, u. a. Vergleich nur mit denselben Stunden und Tagestyp, Akku-Phasen über Mitternacht, lokale statt UTC-Tage, Index auf Zeit. Die dritte (Laufzeit-Profil) fand 10 Befunde, alle behoben, u. a. einzeiliger Grund (sonst ließ sich der Verlauf fälschen), git ohne fremde Konfiguration, Bestätigung an Marvins Telegram-Chat gebunden, Rückgängig nur mit seinem Ja, Rücknahme bei Fehlern.

## Regeln für den Code
- Erst der Test, dann der Code. Fertig ist etwas erst, wenn ein frischer Testlauf es belegt.
- Für jede wichtige Regel einen eingebauten Fehler in `brain/tests/mutations.json` ergänzen. Überlebt er, fehlt ein Test.
- Laufzeitdaten (Event-Log, Datenbank, laufendes Profil) liegen nie im Repo. Pfade kommen aus der Config.
- Keine Secrets in Code, Tests, Logs oder Gedächtnis. Nur Referenzen auf den Secret-Store.
- Fremde Pakete nur nach Prüfung (`skills/INDEX.md`), mit fester Version, mindestens 14 Tage alt, Installation nur mit Prüfsummen (`--require-hashes`).
- Bezeichner und Kommentare im Code auf Englisch, Doku für Marvin auf Deutsch.
